import asyncio
import json
import os
from contextlib import AsyncExitStack
from typing import Any, Iterable

from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, stdio_client
from mcp.types import CallToolResult
from openai import OpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)
from openai.types.chat.chat_completion import Choice
from openai.types.shared_params import FunctionDefinition

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
        tools: Iterable[ChatCompletionToolParam] = [],
        # model: str = "gemini-2.0-flash",
        model: str = "gemini-2.5-flash-preview-05-20",
        temperature: int = 0,
    ):
        return self.chat.completions.create(
            model=model,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            temperature=temperature,
        )


class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.sessions: list[ClientSession] = []
        self.exit_stack = AsyncExitStack()
        self.gem = GeminiClient(GEMINI_API_KEY)  # type: ignore

    # methods will go here
    async def connect_to_servers(self, servers_script_paths: list[str]):
        for servers_script_path in servers_script_paths:
            await self.connect_to_server(servers_script_path)

    async def connect_to_server(self, servers_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        is_python = servers_script_path.endswith(".py")
        is_js = servers_script_path.endswith(".js")
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")

        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command=command, args=[servers_script_path], env=None
        )

        stdio_transport = await self.exit_stack.enter_async_context(
            stdio_client(server_params)
        )
        self.stdio, self.write = stdio_transport

        session = await self.exit_stack.enter_async_context(
            ClientSession(self.stdio, self.write)
        )

        await session.initialize()

        self.sessions.append(session)

        # List available tools
        # response = await self.session.list_tools()
        # tools = response.tools
        # print("\nConnected to server with tools:", [tool.name for tool in tools])

    async def process_query(self, query: str) -> str:
        assert self.sessions is not None, (
            "Session must be initialized before processing a query"
        )
        """Process a query using Claude and available tools"""
        messages: list[ChatCompletionMessageParam] = [
            {"role": "user", "content": query}
        ]

        available_tools: list[ChatCompletionToolParam] = []
        for session in self.sessions:
            response = await session.list_tools()
            available_tools.extend(
                [
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
            )

        tool_choice_res = self.gem.response(messages, tools=available_tools)

        if not tool_choice_res:
            return "No tool choice response from Gemini"

        # Process response and handle tool calls
        final_text: list[str] = []

        assistant_message_content: list[str | Choice] = []
        print(f"\nTool choices: {tool_choice_res.choices}. Only choosing first one.")
        for index, choice in enumerate(tool_choice_res.choices[:1]):
            print(f"Choice {index}: {choice}")
            if cnt_msg := choice.message.content:
                final_text.append(cnt_msg)
                assistant_message_content.append(cnt_msg)
            elif tool_calls := choice.message.tool_calls:
                results_tool_call: list[CallToolResult] = []
                for tool_call in tool_calls:
                    tool_name = tool_call.function.name
                    tool_args: dict[str, Any] = (
                        json.loads(tool_call.function.arguments)
                        if tool_call.function.arguments
                        else {}
                    )

                    assert isinstance(tool_args, dict), (
                        f"Tool arguments must be a dictionary, got {type(tool_args)}"
                    )
                    # Execute tool call
                    # TODO need to transform self.sessions to better data structure
                    # result = await self.sessions.call_tool(tool_name, tool_args)
                    result = None
                    is_tool_called = False
                    for session in self.sessions:
                        if tool_name in [
                            tool.name for tool in (await session.list_tools()).tools
                        ]:
                            result = await session.call_tool(tool_name, tool_args)
                            is_tool_called = True
                            break

                    assert isinstance(result, CallToolResult)
                    if not is_tool_called:
                        raise Exception(f"Tool {tool_name} not found in sessions.")

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
                    final_text.append("Result tool call: " + str(results_tool_call))
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
        # rephase_res = self.gem.response(messages=messages, tools=available_tools)
        print("RUN HEER 1")
        rephase_res = self.gem.response(messages=messages)
        print("RUN HEER 2")
        if content := rephase_res.choices[0].message.content:
            final_text.append(content)
        else:
            print("⚠️ No response from Gemini")

        return "\n".join(final_text)

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Type your queries or 'quit' to exit.")

        while True:
            try:
                query = input("\nQuery: ").strip()

                if query.lower() == "quit" or query.lower() == "exit" or query == "q":
                    break
                if not query:
                    continue

                response = await self.process_query(query)
                print("\n" + response)  # DEBUG str(response)
                print("-" * 50)

            except Exception as e:
                print(f"\n❌ Error: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        await self.exit_stack.aclose()


async def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python client.py <path_to_mcp_server_1_script> <path_to_mcp_server_2_script> ..."
        )
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_servers(sys.argv[1:])
        await client.chat_loop()
    finally:
        await client.cleanup()


if __name__ == "__main__":
    import sys

    asyncio.run(main())
