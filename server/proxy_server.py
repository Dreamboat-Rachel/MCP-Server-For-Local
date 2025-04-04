import json
import os
import asyncio
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack

mcp = FastMCP("ProxyServer")
exit_stack = AsyncExitStack()

CONFIG_FILE = "D:\\downloads\\github_project\\mcp-server\\mcp-client\\mcp-client\\config\\servers.json"

def load_server_config(config_file: str) -> list:
    try:
        with open(config_file, 'r') as f:
            servers = json.load(f)
        print(f"DEBUG: Loaded servers: {servers}")
        if not isinstance(servers, list):
            raise ValueError("Config file must contain a list of server configurations")
        return servers
    except Exception as e:
        print(f"DEBUG: Config load error: {str(e)}")
        return []

SERVERS = load_server_config(CONFIG_FILE)
sessions: Dict[str, ClientSession] = {}
tool_mapping: Dict[str, str] = {}

async def initialize_servers():
    for server in SERVERS:
        command = "python"
        script_path = os.path.join(os.path.dirname(__file__), server["script"])
        server_params = StdioServerParameters(command=command, args=[script_path], env=None)
        stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
        stdio, write = stdio_transport
        session = await exit_stack.enter_async_context(ClientSession(stdio, write))
        await session.initialize()
        sessions[server["name"]] = session
        response = await session.list_tools()
        for tool in response.tools:
            tool_mapping[tool.name] = server["name"]
            print(f"DEBUG: Registered tool '{tool.name}' from {server['name']}")

@mcp.tool(description="代理工具，根据工具名动态调用其他服务端的工具，输入格式为字典：{'tool': 'tool_name', 'args': {...}}")
async def proxy_tool_call(params: Dict[str, Any]) -> str:
    try:
        tool_name = params.get("tool")
        tool_args = params.get("args", {})
        if not tool_name or tool_name not in tool_mapping:
            return f"⚠️ 未知工具: {tool_name}"
        server_name = tool_mapping[tool_name]
        session = sessions[server_name]
        result = await session.call_tool(tool_name, tool_args)
        return result.content[0].text
    except Exception as e:
        return f"⚠️ 工具调用失败: {str(e)}"

async def run_proxy():
    print("DEBUG: Starting MCP ProxyServer")
    await mcp.run_stdio_async()

async def main():
    await initialize_servers()
    await run_proxy()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        asyncio.run(exit_stack.aclose())