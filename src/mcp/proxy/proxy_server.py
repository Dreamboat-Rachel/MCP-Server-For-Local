import json
import os
import asyncio
import platform
import logging
from pathlib import Path
from typing import Any, Dict
from mcp.server.fastmcp import FastMCP
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from contextlib import AsyncExitStack
from dotenv import load_dotenv

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("ProxyServer")

mcp = FastMCP("ProxyServer")
exit_stack = AsyncExitStack()

# 加载 .env 文件并设置默认路径
load_dotenv()

# 获取项目根目录
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONFIG_FILE = os.getenv("CONFIG_FILE", str(PROJECT_ROOT / "servers.json"))
SERVERS_DIR = os.getenv("SERVERS_DIR", str(PROJECT_ROOT / "servers"))

def normalize_path(path: str) -> str:
    """标准化路径，确保跨平台兼容性"""
    return str(Path(path).resolve())

def get_python_command() -> str:
    """获取 Python 命令，考虑不同平台"""
    if platform.system() == "Windows":
        return "python"
    return "python3"

def get_node_command() -> str:
    """获取 Node.js 命令，考虑不同平台"""
    if platform.system() == "Windows":
        return "node"
    return "node"

def load_server_config(config_file: str) -> list:
    """加载服务器配置"""
    try:
        config_file = normalize_path(config_file)
        if not os.path.exists(config_file):
            logger.warning(f"Config file not found at {config_file}, using empty server list")
            return []
        
        with open(config_file, 'r', encoding='utf-8') as f:
            servers = json.load(f)
            
        if not isinstance(servers, list):
            raise ValueError("Config file must contain a list of server configurations")
            
        # 验证每个服务器配置
        for server in servers:
            if not isinstance(server, dict):
                raise ValueError("Each server configuration must be a dictionary")
            if "name" not in server or "script" not in server:
                raise ValueError("Each server configuration must have 'name' and 'script' fields")
                
        logger.info(f"Successfully loaded {len(servers)} server configurations")
        return servers
    except Exception as e:
        logger.error(f"Error loading server config: {str(e)}")
        return []

SERVERS = load_server_config(CONFIG_FILE)
sessions: Dict[str, ClientSession] = {}
tool_mapping: Dict[str, str] = {}

async def initialize_servers():
    """初始化所有服务器连接"""
    if not SERVERS:
        logger.warning("No servers configured, skipping initialization")
        return
        
    for server in SERVERS:
        try:
            server_name = server["name"]
            script_name = server["script"]
            
            # 构建服务器脚本的完整路径
            script_path = normalize_path(os.path.join(SERVERS_DIR, script_name))
            if not os.path.exists(script_path):
                logger.error(f"Server script not found: {script_path}")
                continue
                
            # 确保脚本有执行权限
            if platform.system() != "Windows":
                os.chmod(script_path, 0o755)
                
            # 根据脚本扩展名确定命令
            is_python = script_name.endswith('.py')
            is_js = script_name.endswith('.js')
            
            if not (is_python or is_js):
                logger.error(f"Unsupported script type: {script_name}")
                continue
                
            command = get_python_command() if is_python else get_node_command()
            server_params = StdioServerParameters(
                command=command,
                args=[script_path],
                env=None
            )
            
            # 建立连接
            stdio_transport = await exit_stack.enter_async_context(stdio_client(server_params))
            stdio, write = stdio_transport
            session = await exit_stack.enter_async_context(ClientSession(stdio, write))
            await session.initialize()
            
            # 注册会话和工具
            sessions[server_name] = session
            response = await session.list_tools()
            for tool in response.tools:
                tool_mapping[tool.name] = server_name
                logger.info(f"Registered tool '{tool.name}' from {server_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize {server['name']}: {str(e)}")

@mcp.tool(description="代理工具，根据工具名动态调用其他服务端的工具，输入格式为字典：{'tool': 'tool_name', 'args': {...}}")
async def proxy_tool_call(params: Dict[str, Any]) -> str:
    """代理工具调用"""
    try:
        tool_name = params.get("tool")
        tool_args = params.get("args", {})
        
        if not tool_name:
            return "⚠️ 工具名称缺失"
            
        if tool_name not in tool_mapping:
            return f"⚠️ 未知工具: {tool_name}"
            
        server_name = tool_mapping[tool_name]
        if server_name not in sessions:
            return f"⚠️ 服务器 {server_name} 未连接"
            
        session = sessions[server_name]
        result = await session.call_tool(tool_name, tool_args)
        return result.content[0].text
        
    except Exception as e:
        logger.error(f"Tool call error: {str(e)}")
        return f"⚠️ 工具调用失败: {str(e)}"

async def run_proxy():
    """运行代理服务器"""
    logger.info("Starting MCP ProxyServer")
    await mcp.run_stdio_async()

async def main():
    """主函数"""
    try:
        await initialize_servers()
        await run_proxy()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
    finally:
        logger.info("Cleaning up resources")
        await exit_stack.aclose()

if __name__ == "__main__":
    asyncio.run(main())