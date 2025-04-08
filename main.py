import gradio as gr
import subprocess
import os
import asyncio
import sys
from client.common_client import MCPClient

# 设置项目根目录（根据你的路径调整）
BASE_DIR = r"D:\downloads\github_project\mcp-server\mcp-client\mcp-server-for-local"

# 激活虚拟环境并运行命令的函数
def start_mcp_server():
    try:
        # 在 Windows 下激活虚拟环境并运行命令
        activate_cmd = os.path.join(BASE_DIR, ".venv", "Scripts", "activate.bat")
        run_cmd = f"uv run .\client\common_client.py .\server\proxy_server.py"
        full_cmd = f'cmd.exe /c "{activate_cmd} && {run_cmd}"'
        
        # 在后台启动服务器进程
        process = subprocess.Popen(
            full_cmd,
            shell=True,
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        return "✅ MCP 服务器启动成功！", process
    except Exception as e:
        return f"❌ 启动服务器失败: {str(e)}", None

# 处理用户输入并与 MCP 客户端交互
async def process_query(query, client_instance):
    if not client_instance:
        return "⚠️ 请先启动服务器！"
    try:
        response = await client_instance.process_query(query)
        return response
    except Exception as e:
        return f"⚠️ 查询处理失败: {str(e)}"

# 获取工具列表的函数
async def get_tools(client_instance):
    if not client_instance or not client_instance.session:
        return "⚠️ 客户端未初始化！"
    try:
        tools = await client_instance.get_available_tools()
        if not tools:
            return "暂无可用工具"
        return "\n".join([f"- {tool}" for tool in tools])
    except Exception as e:
        return f"⚠️ 获取工具列表失败: {str(e)}"

# Gradio 界面逻辑
def create_gradio_interface():
    # 初始化 MCP 客户端和服务器进程
    client_instance = None
    server_process = None

    with gr.Blocks(title="MCP 调试界面") as demo:
        gr.Markdown("# MCP 客户端调试界面")
        gr.Markdown("启动服务器并与 MCP 客户端交互")

        # 服务器状态显示
        server_status = gr.Textbox(label="服务器状态", value="未启动", interactive=False)
        
        # 工具列表显示
        tools_display = gr.Textbox(label="可用工具列表", value="未加载", interactive=False)

        # 启动服务器按钮
        start_button = gr.Button("启动 MCP 服务器")

        # 输入和输出区域
        query_input = gr.Textbox(label="输入你的查询", placeholder="例如：北京的天气怎么样？")
        output = gr.Textbox(label="响应", interactive=False)
        submit_button = gr.Button("提交查询")

        # 启动服务器并加载工具的回调
        def on_start():
            nonlocal client_instance, server_process
            status, process = start_mcp_server()
            if process:
                server_process = process
                # 初始化 MCP 客户端并连接到服务器
                client_instance = MCPClient()
                asyncio.run(client_instance.connect_to_server(os.path.join(BASE_DIR, "server", "proxy_server.py")))
                # 获取并展示工具列表
                tools = asyncio.run(get_tools(client_instance))
                return status, tools
            return status, "⚠️ 服务器启动失败，无法加载工具"

        # 提交查询的回调
        def on_submit(query):
            nonlocal client_instance
            if not client_instance:
                return "⚠️ 请先启动服务器！"
            return asyncio.run(process_query(query, client_instance))

        # 绑定事件
        start_button.click(fn=on_start, outputs=[server_status, tools_display])
        submit_button.click(fn=on_submit, inputs=query_input, outputs=output)

        # 清理资源（当界面关闭时）
        def cleanup():
            nonlocal server_process, client_instance
            if server_process:
                server_process.terminate()
                server_process.wait()
            if client_instance:
                asyncio.run(client_instance.cleanup())
            return "✅ 资源已清理"

        demo.unload(fn=cleanup, outputs=server_status)

    return demo

if __name__ == "__main__":
    # 确保在正确的目录下运行
    os.chdir(BASE_DIR)
    interface = create_gradio_interface()
    interface.launch()