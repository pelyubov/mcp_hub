import os

import dotenv

dotenv.load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
assert GEMINI_API_KEY, "GEMINI_API_KEY must be set in .env file"


from google import genai
from google.genai.types import GenerateContentConfigDict, Tool
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

SYSTEM_PROMPT = """Use search tool to find information on the web then summarize the information found related to the question in form of a short paragraph."""

class GeminiClient(genai.Client):
    """Custom Gemini client to handle API requests."""

    def __init__(self, api_key: str, tools: list = None):
        super().__init__(api_key)
        self.tools = tools or []

    def response(self, prompt: str, model: str = "gemini-2.0-flash") -> str:
        return self.models.generate_content(
            model=model,
            config=GenerateContentConfigDict(
                system_instruction=SYSTEM_PROMPT,
                temperature=0.3,
                tools=self.tools,
            ),
            contents=prompt
        ).text 

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["main.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


# Optional: create a sampling callback
# async def handle_sampling_message(
#     message: types.CreateMessageRequestParams,
# ) -> types.CreateMessageResult:
#     return types.CreateMessageResult(
#         role="assistant",
#         content=types.TextContent(
#             type="text",
#             text="Hello, world! from model",
#         ),
#         model="gpt-3.5-turbo",
#         stopReason="endTurn",
#     )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
            read, write
            # , sampling_callback=handle_sampling_message
        ) as session:
        
            prompt = "Tìm hiểu về định luật Newton"
            await session.initialize()

            mcp_tools = await session.list_tools()

            print("Available tools:", tools)
            tools = [
                types.Tool(
                    function_declarations=[
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "parameters": {
                                k: v
                                for k, v in tool.inputSchema.items()
                                if k not in ["additionalProperties", "$schema"]
                            },
                        }
                    ]
                )
                for tool in mcp_tools.tools
            ]

            gemini_client = GeminiClient(api_key=GEMINI_API_KEY, tools=tools)

            print(gemini_client.response(prompt))
            

if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
