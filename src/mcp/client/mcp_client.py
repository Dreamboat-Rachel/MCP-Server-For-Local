import asyncio
import os
import json
import sys
import platform
import logging
from pathlib import Path
from typing import Optional, List
from contextlib import AsyncExitStack
from dashscope import Generation
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("MCPClient")

# 加载环境变量
load_dotenv()

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

class MCPClient:
    def __init__(self):
        """初始化 MCP 客户端"""
        self.exit_stack = AsyncExitStack()
        self.api_key = os.getenv("DASHSCOPE_API_KEY")
        self.model = os.getenv("MODEL") or "qwen-max"

        if not self.api_key:
            raise ValueError("❌ 未找到 API Key，请在 .env 文件中设置 DASHSCOPE_API_KEY")

        import dashscope
        dashscope.api_key = self.api_key
        self.session: Optional[ClientSession] = None

    async def connect_to_server(self, server_script_path: str):
        """连接到 MCP 服务器并列出可用工具"""
        try:
            # 验证服务器脚本路径
            server_script_path = normalize_path(server_script_path)
            if not os.path.exists(server_script_path):
                raise FileNotFoundError(f"服务器脚本不存在: {server_script_path}")

            # 确保脚本有执行权限
            if platform.system() != "Windows":
                os.chmod(server_script_path, 0o755)

            # 确定脚本类型和命令
            is_python = server_script_path.endswith('.py')
            is_js = server_script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("服务器脚本必须是 .py 或 .js 文件")

            command = get_python_command() if is_python else get_node_command()
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )

            # 建立连接
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
            await self.session.initialize()

            # 获取可用工具
            available_tools = [
                {"name": "query_weather", "description": "查询指定城市代码的天气信息", "inputSchema": {"city_code": "string"}},
                {"name": "google_search", "description": "使用谷歌搜索关键词", "inputSchema": {"query": "string"}},
                {"name": "capture_camera_image", "description": "拍照并进行微表情分析", "inputSchema": {}},
                {"name": "generate_image", "description": "生成图片", "inputSchema": {}}
            ]
            logger.info(f"已连接到服务器，支持以下工具: {[tool['name'] for tool in available_tools]}")

        except Exception as e:
            logger.error(f"连接服务器失败: {str(e)}")
            raise

    async def get_available_tools(self) -> List[str]:
        """获取当前可用的工具列表"""
        if not self.session:
            logger.warning("未连接到服务器")
            return []
        try:
            response = await self.session.list_tools()
            return [tool.name for tool in response.tools]
        except Exception as e:
            logger.error(f"获取工具列表失败: {str(e)}")
            return []

    async def process_query(self, query: str) -> str:
        """使用 DashScope 处理查询，通过代理服务端调用工具"""
        if not self.session:
            return "⚠️ 未连接到服务器"

        try:
            response = await self.session.list_tools()
            tool_descriptions = "\n".join(
                f"- {tool.name}: {tool.description} (输入参数: {json.dumps(tool.inputSchema)})"
                for tool in response.tools
            )

            system_prompt = f"""
                你是一个智能助手，可以根据用户输入决定是否调用工具。当前通过代理服务端支持以下底层工具：
                - query_weather: 查询指定城市代码的天气信息，输入参数为城市代码（如 '110000' 表示北京，'330100' 表示杭州）
                - google_search: 使用 google_search 工具，参数名必须是 query，打开本地谷歌浏览器并搜索指定关键词，输入参数为搜索关键词（如 'Python tutorial'）。
                - capture_camera_image：使用 capture_camera_image 工具，拍照并进行微表情分析。
                - generate_image：使用 generate_image 工具来进行生图。

                代理服务端工具：
                {tool_descriptions}

                你的任务是：
                1. 理解用户的问题。
                2. 如果需要调用工具，返回 JSON 格式的响应，包含：
                   - "action": "call_tool"
                   - "tool": 底层工具名称（如 'query_weather' 或 'google_search'）
                   - "args": 工具参数（字典格式）
                3. 如果不需要工具，直接返回纯文本回答。

                请以以下格式返回：
                - 工具调用: ```json\n{{"action": "call_tool", "tool": "tool_name", "args": {{...}}}}\n```
                - 普通回答: 直接返回文本

                注意：
                - 如果用户提到城市天气，请将城市名转换为高德地图城市代码（例如"北京" -> "110000"，"杭州" -> "330100"）。
                - 代理服务端会将请求转发到正确的工具，你只需指定底层工具名和参数。
            """
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]

            response = await asyncio.to_thread(
                Generation.call,
                model=self.model,
                messages=messages,
                result_format="message"
            )

            if response.status_code != 200:
                logger.error(f"DashScope API 失败: {response.message}")
                return f"⚠️ DashScope API 失败: {response.message}"

            content = response.output.choices[0].message.content
            try:
                if "```json" in content:
                    json_str = content.split("```json")[1].split("```")[0].strip()
                    tool_data = json.loads(json_str)
                    if tool_data.get("action") == "call_tool":
                        tool_name = tool_data.get("tool")
                        tool_args = tool_data.get("args", {})

                        if not tool_name:
                            return "⚠️ 工具名称缺失"

                        proxy_params = {
                            "params": {"tool": tool_name, "args": tool_args}
                        }
                        result = await self.session.call_tool("proxy_tool_call", proxy_params)
                        return result.content[0].text
                return content
            except json.JSONDecodeError as e:
                logger.error(f"JSON 解析失败: {str(e)}")
                return content

        except Exception as e:
            logger.error(f"处理查询时出错: {str(e)}")
            return f"⚠️ 处理查询时出错: {str(e)}"

    async def chat_loop(self):
        """运行交互式聊天循环"""
        print("\n🤖 MCP 客户端已启动！输入 'quit' 退出")
        print("示例：'北京的天气怎么样？' 或 '在谷歌上搜索 Python 教程'")
        while True:
            try:
                query = input("\n你: ").strip()
                if query.lower() == 'quit':
                    break
                response = await self.process_query(query)
                print(f"\n🤖 DashScope: {response}")
            except Exception as e:
                logger.error(f"聊天循环出错: {str(e)}")
                print(f"\n⚠️ 发生错误: {str(e)}")

    async def cleanup(self):
        """清理资源"""
        try:
            await self.exit_stack.aclose()
        except Exception as e:
            logger.error(f"清理资源时出错: {str(e)}")

async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("Usage: python mcp_client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main())