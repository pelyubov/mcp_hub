import os
import sys

from mcp.server.fastmcp import FastMCP
from numpy import ndarray

current_dir = os.path.dirname(__file__)  
project_root = os.path.abspath(os.path.join(current_dir, '..'))
sys.path.append(project_root)

from utils.chunker import recursive_chunking
from utils.vector_store import (add_text_to_qdrant, delete_collection,
                                embed_model, search_similar_texts)

mcp = FastMCP(name="SearchService")

def drop_content_if_title_not_matching(
    query_embed: ndarray, title: str | None, similarity_threshold: float = 0.5
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
    from utils import (get_html_from_url, get_title_n_paragraphs_from_html,
                       process_text, search_google)
    results, last_index_search = search_google(query)
    query_embedding = embed_model.encode(query)
    for result in results:
        try:
            html = get_html_from_url(result)
            title, paragraphs = get_title_n_paragraphs_from_html(html)
            if drop_content_if_title_not_matching(query, title):
                continue
            for paragraph in paragraphs:
                chunks = recursive_chunking(
                    process_text(paragraph), 
                    embed_model.max_seq_length * 0.8,
                    10
                )
                [add_text_to_qdrant(chunk, title) for chunk in chunks]
            context = search_similar_texts(
                query,
                limit
            )
            return context
        except Exception as e:
            pass
            # print(f"Error processing {result}: {e}")
        finally:
            delete_collection()

if __name__ == "__main__":
    mcp.run()