import os
import sys

from mcp.server.fastmcp import FastMCP
from numpy import ndarray

from utils.chunker import recursive_chunking
from utils.vector_store import (add_text_to_qdrant, delete_data_in_collection,
                                embed_model, search_similar_texts)

# current_dir = os.path.dirname(__file__)  
# project_root = os.path.abspath(os.path.join(current_dir, '..'))
# sys.path.append(project_root)


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


@mcp.tool(name="search-information", description="A tool to search information for a query.")
def search(query: str, limit: int = 10):
    """Search the web for the given query and return the results."""
    from utils import (get_html_from_url, get_title_n_content_from_html,
                       process_text, search_google)
    print("a")
    results, last_index_search = search_google(query, num_results=limit)
    query_embedding = embed_model.encode(query)
    for result in results:
        try:
            print(f"Found URL: {result if isinstance(result, str) else result.url}")
            html = get_html_from_url(result)
            title, content = get_title_n_content_from_html(html)
            # if drop_content_if_title_not_matching(query_embedding, title, similarity_threshold=0.5):
            #     continue
            content = process_text(content)
            print(f"Processing content for title: {title}")
            # if not content:
            #     print("No content found, skipping...")
            #     continue
            print(f"Content: ", content)
            chunks = recursive_chunking(
                content, 
                int(embed_model.max_seq_length * 0.8),
                10
            )
            for chunk in chunks:
                print(f"Adding chunk: {chunk[:50]}...")
                print("-" * 50)
                if not chunk.strip():
                    continue
                try:
                    add_text_to_qdrant(chunk, title, result if isinstance(result, str) else result.url)
                except Exception as e:
                    print(f"Error adding text to Qdrant: {e}")
                    continue
            print("=" * 50 + "\n")
        except Exception:
            continue
            
    context = search_similar_texts(
        query,
        limit=10,
        threshold=0.5,
    )
    delete_data_in_collection()
    return context

if __name__ == "__main__":
    mcp.run()
#     context_found = search("cá chép nấu măng chua", limit=3)
#     print(context_found)

