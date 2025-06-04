from mcp.server.fastmcp import FastMCP

mcp = FastMCP(name="DummyService")


@mcp.tool()
async def dummy_tool(a: int, b: int) -> int:
    """
    Dummy tool. The tool that get sum of two number.
    """
    return a + b


if __name__ == "__main__":
    mcp.run("stdio")
