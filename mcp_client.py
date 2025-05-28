import asyncio
import json
from typing import Iterable, Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.client.stdio import stdio_client

from openai import OpenAI

from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai.types.shared_params import FunctionDefinition
from dotenv import load_dotenv

import os

load_dotenv()  # load environment variables from .env

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
assert GEMINI_API_KEY is not None, "GEMINI_API_KEY must be set in .env file"

SYSTEM_PROMPT = """Use search tool to find information on the web then summarize the information found related to the question in form of a short paragraph."""


class GeminiClient(OpenAI):

    def __init__(self, api_key: str):
        super().__init__(
            api_key=api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )

    def response(
        self,
        messages: Iterable[ChatCompletionMessageParam],
        tools: Iterable[ChatCompletionToolParam],
        model: str = "gemini-2.0-flash",
    ):
        return self.chat.completions.create(
            model=model, messages=messages, tools=tools, tool_choice="auto"
        )


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.gem = GeminiClient(GEMINI_API_KEY)

    # methods will go here

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = server_script_path.endswith(".py")
        is_js = server_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[server_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await self.session.initialize()

        # List available tools
        response = await self.session.list_tools()
        tools = response.tools
        print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        assert (
            self.session is not None
        ), "Session must be initialized before processing a query"
        """Process a query using Claude and available tools"""
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": query}
        ]

        response = await self.session.list_tools()
        available_tools: list[ChatCompletionToolParam] = [
            ChatCompletionToolParam(
                function=FunctionDefinition(
                    name=tool.name,
                    description=tool.description or "",
                    parameters=tool.inputSchema,
                ),
                type="function",
            )
            for tool in response.tools
        ]

        response = self.gem.response(messages, tools=available_tools)

        if not response:
            return "No response from Gemini"

        # Process response and handle tool calls
        final_text = []

        assistant_message_content = []
        for index, choice in enumerate(response.choices):
            print(f"Choice {index}: {choice}")
            if cnt_msg := choice.message.content:
                final_text.append(cnt_msg)
                assistant_message_content.append(cnt_msg)

            if tool_calls := choice.message.tool_calls:
                results_tool_call = []
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = (
                        json.loads(tool_call.function.arguments)
                        if tool_call.function.arguments
                        else {}
                    )

                    assert isinstance(
                        tool_args, dict
                    ), f"Tool arguments must be a dictionary, got {type(tool_args)}"
                    # Execute tool call
                    result = await self.session.call_tool(tool_name, tool_args)

                    if result.isError:
                        final_text.append(
                            f"Error calling tool {tool_name}"  # FIX can not get error message
                        )
                        continue
                    results_tool_call.append(result)
                    final_text.append(
                        f"[Calling tool {tool_name} with args {tool_args}]"
                    )

                    assistant_message_content.append(choice)
                    # messages.append(
                    #     {"role": "assistant", "content": assistant_message_content}
                    # )

                    # Add results of tool calls to messages
                    # messages.append(
                    #     {
                    #         "role": "function",
                    #         "name": tool_name,
                    #         "content": str(
                    #             result
                    #         ),  # CONSIDER change to better structure
                    #     }
                    # )
                    # BUG does GEMINI not have "function" role?

                    messages.append(
                        {
                            "role": "assistant",
                            "content": json.dumps(
                                {
                                    "tool_name": tool_name,
                                    "tool_result": str(result),
                                }
                            ),
                        }
                    )

        # Get next response from GEMINI
        response_second = self.gem.response(messages=messages, tools=available_tools)
        final_text.append(response_second.choices[0].message.content)

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit":
                    break

                response = await self.process_query(query)
                print("\n" + response)  # DEBUG str(response)

            except Exception as e:
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print("Usage: python client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
