from utils.chunker import recursive_chunking
from utils.get_html import get_html_from_url, get_title_n_content_from_html
from utils.search_google import search_google
from utils.text_preprocessing import process_text

try:
    query = "cá chép"
    results, last_index_search = search_google(query, num_results=5)
    for result in results:
        print(f"Found URL: {result if isinstance(result, str) else result.url}")
        html = get_html_from_url(result)
        title, content = get_title_n_content_from_html(html)

        content = process_text(content)
        print(f"Processing content for title: {title}")

        chunks = recursive_chunking(content, int(512 * 0.8), 10)
        for chunk in chunks:
            print(f"Adding chunk: {chunk[:50]}...")
            print("-" * 50)
            if not chunk.strip():
                continue
        print("=" * 50 + "\n")
except Exception as e:
    print(f"An error occurred during the search: {e}")

# import os
# import sys
#
# current_dir = os.path.dirname(__file__)
# project_root = os.path.abspath(os.path.join(current_dir, ".."))
# sys.path.append(project_root)
# uv run mcp_client.py tools/weather.py tools/summarize_web_content.py tools/search.py
