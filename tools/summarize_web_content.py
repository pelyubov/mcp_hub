from mcp.server.fastmcp import FastMCP
import os
import sys

current_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)
from utils import get_html_from_url, get_title_n_content_from_html


mcp = FastMCP(name="SummarizeWebContentService")


@mcp.tool(description="read content from an url")
async def read_html(url: str) -> str:
    """Read content from an URL."""
    html = get_html_from_url(url)
    if not html:
        return "Failed to fetch content."
    _, content = get_title_n_content_from_html(html)
    return content


if __name__ == "__main__":
    mcp.run(transport="stdio")
