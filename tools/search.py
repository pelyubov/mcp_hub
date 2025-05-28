from mcp.server.fastmcp import FastMCP
from torch import Tensor


from utils.chunking import recursive_chunking
from utils.vector_store import (
    add_text_to_qdrant,
    delete_data_in_collection,
    embed_model,
    search_similar_texts,
)

mcp = FastMCP(name="SearchService")


def drop_content_if_title_not_matching(
    query_embed: Tensor, title: str | None, similarity_threshold: float = 0.5
):
    if title is None:
        return False
    assert query_embed.shape == (768,)

    title_embed = embed_model.encode(title)
    similarity = embed_model.similarity(query_embed, title_embed)
    if similarity <= similarity_threshold:
        return False
    return True


@mcp.tool(name="search", description="A tool to search for a query.")
def search(query: str, limit: int = 10) -> list[str]:
    """Search the web for the given query and return the results."""
    from utils import (
        get_html_from_url,
        get_title_n_content_from_html,
        process_text,
        search_google,
    )

    results, last_index_search = search_google(query)
    query_embedding = embed_model.encode(query)
    for result in results:
        try:
            html = get_html_from_url(result)
            title, paragraphs = get_title_n_content_from_html(html)
            if drop_content_if_title_not_matching(query_embedding, title):
                continue
            for paragraph in paragraphs:
                chunks = recursive_chunking(
                    process_text(paragraph), int(embed_model.max_seq_length * 0.8), 10
                )
                [
                    add_text_to_qdrant(
                        chunk, title, result if isinstance(result, str) else result
                    )
                    for chunk in chunks
                ]
        except Exception as e:
            pass
            # print(f"Error processing {result}: {e}")
    context = search_similar_texts(query, limit)
    delete_data_in_collection()
    return context


if __name__ == "__main__":
    mcp.run()
