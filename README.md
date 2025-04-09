# MCP Server for Local

一个基于 MCP (Multi-Component Platform) 的本地代理服务器和客户端实现，提供多种 AI 工具调用能力。

## 功能特点

### 核心功能
- **天气查询**：实时获取全球任意位置的天气信息，支持温度、湿度、风速等详细数据
- **谷歌搜索**：智能检索互联网信息，支持多语言和高级搜索语法
- **摄像头控制**：支持拍照、视频流和微表情分析，可用于情绪识别
- **图片生成**：集成 ComfyUI，支持文本到图像的 AI 生成
- **智能对话**：基于 DashScope 的 AI 对话能力，支持上下文理解和多轮对话

### 技术特性
- 跨平台支持（Windows 和 Linux）
- 模块化设计，易于扩展新功能
- 完整的日志系统，便于调试和监控
- 支持自定义工具和 API 集成
- 高性能并发处理能力

## 环境配置

### 系统要求
- Python 3.8+
- Node.js (可选，用于运行 JavaScript 服务器)
- Chrome 浏览器（用于谷歌搜索功能）
- 摄像头（用于拍照功能）
- 至少 4GB 内存
- 支持 CUDA 的显卡（可选，用于加速 AI 计算）

### 安装步骤

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
# 使用 uv 安装依赖
uv pip install -r requirements.txt

# 如果遇到网络问题，可以使用国内镜像
uv pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

4. 配置环境变量：
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，设置你的配置
```

### 环境变量配置
编辑 `.env` 文件，设置以下配置：

- `DASHSCOPE_API_KEY`: DashScope API 密钥（必填）
- `MODEL`: 使用的模型名称（默认：qwen-max）
- `CONFIG_FILE`: 服务器配置文件路径
- `GAODE_API_KEY`: 高德地图 API 密钥（用于天气查询）
- `CHROME_PATH`: Chrome 浏览器路径
- `CHROMEDRIVER_PATH`: ChromeDriver 路径
- `BASE_URL`: ComfyUI 服务器地址
- `SERVERS_DIR`: 服务器脚本目录
- `LOG_LEVEL`: 日志级别（可选：DEBUG, INFO, WARNING, ERROR）

## 使用方法

### 基本使用

1. 进入项目目录：
```bash
cd src/mcp
```

2. 运行客户端：
```bash
uv run .\client\mcp_client.py .\proxy\proxy_server.py
```

3. 在客户端中输入命令，例如：
- "北京的天气怎么样？"
- "在谷歌上搜索 Python 教程"
- "拍照"
- "生成一张猫的图片"

### 高级功能

1. **自定义工具**：
   - 在 `src/mcp/tools` 目录下添加新的工具类
   - 实现必要的接口方法
   - 在配置文件中注册新工具

2. **API 扩展**：
   - 支持添加新的 API 服务
   - 可配置 API 密钥和端点
   - 支持自定义请求和响应处理

3. **日志管理**：
   - 支持多级别日志记录
   - 可配置日志输出位置
   - 支持日志轮转和归档

## 常见问题

### 安装问题

1. 依赖安装失败：
```bash
# 尝试清理缓存后重新安装
uv pip cache purge
uv pip install -r requirements.txt
```

2. 虚拟环境问题：
```bash
# 如果激活失败，尝试重新创建虚拟环境
rm -rf .venv
python -m venv .venv
```

### 运行问题

1. 权限问题：
```bash
# Linux
chmod +x src/mcp/proxy/proxy_server.py
chmod +x src/mcp/client/mcp_client.py
```

2. Chrome 相关问题：
- 确保 Chrome 和 ChromeDriver 版本匹配
- 检查 Chrome 路径是否正确
- 确保有足够的权限运行 Chrome
- 如果遇到驱动问题，可以手动下载对应版本的 ChromeDriver

3. API 密钥问题：
- 检查 `.env` 文件中的 API 密钥是否正确
- 确保 API 密钥有足够的配额
- 检查网络连接是否正常

## 开发指南

### 项目结构
```
src/mcp/
├── client/          # 客户端代码
├── proxy/           # 代理服务器代码
├── tools/           # 工具实现
├── utils/           # 工具函数
└── config/          # 配置文件
```

### 添加新功能
1. 在 `tools` 目录下创建新的工具类
2. 实现必要的接口方法
3. 在配置文件中注册新工具
4. 编写测试用例
5. 更新文档

## 贡献指南

欢迎提交 Issue 和 Pull Request！在提交之前，请确保：
1. 代码符合项目规范
2. 添加了必要的测试
3. 更新了相关文档
4. 通过了所有测试

## 许可证

MIT License
