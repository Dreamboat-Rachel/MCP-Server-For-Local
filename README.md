## MCP（Model Context Protocol）简介
**官方地址**：https://github.com/modelcontextprotocol/python-sdk

MCP（Model Context Protocol）是由 Anthropic 开发的一种开源协议，旨在为 AI 模型提供与外部数据源和工具交互的标准化方式。它就像 AI 应用的"通用接口"，通过客户端-服务器架构，让语言模型（如 Claude）能够安全、高效地访问实时数据、执行操作并扩展功能。MCP 的核心优势在于其统一性与模块化，开发者无需为每个工具或数据源编写定制集成，只需实现 MCP 协议即可让 AI 无缝连接。

### 我的 MCP 实现：天气查询、谷歌自动检索与摄像头控制进行微表情分析

我基于 MCP 开发了一个多功能配置，集成了以下特性，开发者可根据需求自由调整：

- **天气查询**：通过 MCP 服务器连接外部天气 API（如 OpenWeatherMap），支持实时获取指定位置的天气预报和警报信息。用户只需输入指定地点，即可获得格式化的天气数据。
- **谷歌自动检索**：利用 MCP 工具，AI 可以动态调用谷歌搜索功能，自动检索相关信息并返回结果，适用于需要实时外部知识的场景。
- **拍照实现微表情分析**：集成了摄像头操作功能，通过 MCP 定义的工具，开发者可以控制摄像头执行拍摄、流媒体传输等任务，采用轻量化DeepFace，并支持自定义参数配置。
- **Comfyui生图**：集成Comfyui 进行生图，开发者可以自由的实现自己想要的图片内容。

### 开发者自由配置

此实现的亮点在于其高度可配置性。开发者可以通过修改 MCP 服务器的工具定义（Tools，即 server 服务端）、客户端（client）、服务端代理以及提示模板（Prompts），轻松扩展功能。例如：
- 调整天气查询的 API 端点或返回格式。
- 更改谷歌检索的搜索参数或添加其他搜索引擎。
- 为摄像头控制添加新命令，如调整分辨率或切换设备。

### 使用场景

这个配置适用于多种场景，例如：
- **智能助手**：结合天气和检索功能，为用户提供实时信息支持。
- **自动化工作流**：通过摄像头控制与数据检索，构建监控或内容生成系统。
- **开发测试**：开发者可基于此模板快速集成新工具，探索 MCP 的潜力。

MCP 的标准化设计让 AI 不再局限于静态知识库，而是能主动与世界交互。我的代码提供了一个开箱即用的示例，欢迎开发者在此基础上自由发挥！

---

## MCP 环境配置指南

本指南将帮助你快速搭建 MCP（Model Context Protocol）客户端的开发环境，包括创建项目目录、设置虚拟环境以及安装 MCP SDK。以下是具体步骤：

### 1. 创建项目目录

首先，创建一个新的项目目录并进入其中：

```bash
uv init mcp-client
cd MCP-Server-For-Local
```

### 2. 创建 MCP 客户端虚拟环境
```bash
# 创建虚拟环境
uv venv
.venv\Scripts\activate
source .venv/bin/activate
```

### 3. 安装 MCP SDK
```bash
uv add mcp
uv pip install numpy==1.23.5 tensorflow==2.12.0 keras==2.12.0 deepface==0.0.79
uv pip install dashscope
uv pip install opencv-python
uv pip install selenium
uv pip install gradio
```

### 4. main.py运行代码（可选）
```bash
from mcp import MCPClient
client = MCPClient()
print("MCP Client initialized!")
```
运行代码：
```bash 
python main.py
```

### 注意事项
- **依赖工具**：本教程假设你已安装 `uv`。如果没有，请先运行以下命令安装：
  ```bash
  pip install uv
  Windows 用户使用：.venv\Scripts\activate
  Linux/MacOS 用户使用：source .venv/bin/activate
  ```
  安装完成后，可根据项目需求配置天气查询、谷歌检索或摄像头控制等功能（详见项目文档）。
  通过以上步骤，你已成功搭建 MCP 客户端的开发环境，可以开始开发和测试了！

# MCP Server for Local

一个基于 MCP (Multi-Component Platform) 的本地代理服务器和客户端实现。

## 功能特点

- 支持多种工具调用（天气查询、谷歌搜索、摄像头拍照、图片生成等）
- 跨平台支持（Windows 和 Linux）
- 可扩展的服务器架构
- 基于 DashScope 的智能对话
- 完整的日志系统

## 系统要求

- Python 3.8+
- Node.js (可选，用于运行 JavaScript 服务器)
- Chrome 浏览器（用于谷歌搜索功能）
- 摄像头（用于拍照功能）

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/mcp-server-for-local.git
cd mcp-server-for-local
```

2. 创建并激活虚拟环境：
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 配置环境变量：
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的配置
```

## 配置说明

### 环境变量

编辑 `.env` 文件，设置以下配置：

- `DASHSCOPE_API_KEY`: DashScope API 密钥
- `MODEL`: 使用的模型名称（默认：qwen-max）
- `CONFIG_FILE`: 服务器配置文件路径
- `GAODE_API_KEY`: 高德地图 API 密钥
- `CHROME_PATH`: Chrome 浏览器路径
- `CHROMEDRIVER_PATH`: ChromeDriver 路径
- `BASE_URL`: ComfyUI 服务器地址
- `SERVERS_DIR`: 服务器脚本目录

### 服务器配置

编辑 `servers.json` 文件，配置你的服务器：

```json
[
    {
        "name": "WeatherServer",
        "script": "weather_server.py"
    },
    {
        "name": "GoogleSearchServer",
        "script": "google_search_server.py"
    },
    {
        "name": "CameraCaptureServer",
        "script": "capture_server.py"
    },
    {
        "name": "ComfyUIImageGenServer",
        "script": "generate_image_server.py"
    }
]
```

## 使用方法

1. 启动代理服务器：
```bash
# Windows
python src/mcp/proxy/proxy_server.py

# Linux
python3 src/mcp/proxy/proxy_server.py
```

2. 启动客户端：
```bash
# Windows
python src/mcp/client/mcp_client.py path/to/proxy_server.py

# Linux
python3 src/mcp/client/mcp_client.py path/to/proxy_server.py
```

3. 在客户端中输入命令，例如：
- "北京的天气怎么样？"
- "在谷歌上搜索 Python 教程"
- "拍照"
- "生成一张猫的图片"

## 跨平台注意事项

### Windows 用户
- 使用反斜杠 `\` 或正斜杠 `/` 作为路径分隔符
- Chrome 通常安装在 `C:\Program Files\Google\Chrome\Application\chrome.exe`
- Python 命令使用 `python`

### Linux 用户
- 使用正斜杠 `/` 作为路径分隔符
- Chrome 通常安装在 `/usr/bin/google-chrome`
- Python 命令使用 `python3`
- 确保脚本有执行权限：`chmod +x script.py`

## 故障排除

1. 如果遇到权限问题：
```bash
# Linux
chmod +x src/mcp/proxy/proxy_server.py
chmod +x src/mcp/client/mcp_client.py
```

2. 如果遇到路径问题：
- 确保所有路径使用绝对路径
- 检查路径分隔符是否正确
- 确保文件存在且有正确的权限

3. 如果遇到 Chrome 相关问题：
- 确保 Chrome 和 ChromeDriver 版本匹配
- 检查 Chrome 路径是否正确
- 确保有足够的权限运行 Chrome

## 贡献

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
