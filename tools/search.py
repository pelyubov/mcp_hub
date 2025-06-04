import os
import sys

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

from mcp.server.fastmcp import FastMCP
from torch import Tensor

from utils import (
    get_html_from_url,
    get_title_n_content_from_html,
    process_text,
    search_google,
)
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
def search(query: str, limit: int = 5) -> list[str]:
    """Search the web for the given query and return the results."""

    results, last_index_search = search_google(query)
    # query_embedding = embed_model.encode(query)
    for result in results:
        if not result:
            continue
        if not isinstance(result, str):
            result = result.url
        try:
            html = get_html_from_url(result if isinstance(result, str) else result)
            title, contents = get_title_n_content_from_html(html)
            # if drop_content_if_title_not_matching(query_embedding, title):
            #     continue
            chunks = recursive_chunking(
                process_text(contents),
                int(embed_model.max_seq_length * 0.8),
                10,
            )

            for chunk in chunks:
                add_text_to_qdrant(
                    chunk, title, result if isinstance(result, str) else result
                )
                print(f"Adding chunk: {chunk[:50]}...")
        except Exception as e:
            # pass
            print(f"Error processing {result}: {e}")
    context = search_similar_texts(query, limit)
    delete_data_in_collection()
    return context


if __name__ == "__main__":
    mcp.run("stdio")
