import httpx
import json
import time
import asyncio
import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# 初始化 MCP 服务器
mcp = FastMCP("ComfyUIImageGenServer")

# 加载环境变量
load_dotenv()

# ComfyUI API
base_url = os.getenv("BASE_URL", "")

# 你的工作流JSON
workflow = {
    "3": {
        "inputs": {
            "seed": 236765782388867,
            "steps": 20,
            "cfg": 8,
            "sampler_name": "euler",
            "scheduler": "normal",
            "denoise": 1,
            "model": ["4", 0],
            "positive": ["6", 0],
            "negative": ["7", 0],
            "latent_image": ["5", 0]
        },
        "class_type": "KSampler"
    },
    "4": {
        "inputs": {
            "ckpt_name": "1.3.fp16.safetensors"
        },
        "class_type": "CheckpointLoaderSimple"
    },
    "5": {
        "inputs": {
            "width": 512,
            "height": 512,
            "batch_size": 1
        },
        "class_type": "EmptyLatentImage"
    },
    "6": {
        "inputs": {
            "text": "beautiful scenery nature glass bottle landscape, , purple galaxy bottle,",
            "clip": ["4", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "7": {
        "inputs": {
            "text": "text, watermark",
            "clip": ["4", 1]
        },
        "class_type": "CLIPTextEncode"
    },
    "8": {
        "inputs": {
            "samples": ["3", 0],
            "vae": ["4", 2]
        },
        "class_type": "VAEDecode"
    },
    "9": {
        "inputs": {
            "filename_prefix": "ComfyUI",
            "images": ["8", 0]
        },
        "class_type": "SaveImage"
    }
}

# 获取保存路径，默认为当前目录
save_path = os.getenv("IMAGE_SAVE_PATH", os.getcwd())
Path(save_path).mkdir(parents=True, exist_ok=True)

async def queue_prompt(workflow, base_url):
    async with httpx.AsyncClient() as client:
        payload = {"prompt": workflow}
        response = await client.post(f"{base_url}/prompt", json=payload, timeout=60.0)
        print(f"DEBUG: Prompt response: {response.text}")
        response.raise_for_status()
        return response.json()["prompt_id"]

async def get_history(prompt_id, base_url):
    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(f"{base_url}/history/{prompt_id}", timeout=60.0)
            print(f"DEBUG: History response: {response.text}")
            response.raise_for_status()
            data = response.json().get(prompt_id)
            if data:
                return data
            await asyncio.sleep(2)

async def get_image(filename, subfolder, folder_type, base_url):
    params = {"filename": filename, "subfolder": subfolder, "type": folder_type}
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/view", params=params, timeout=60.0)
        print(f"DEBUG: Image response status: {response.status_code}")
        response.raise_for_status()
        return response.content

@mcp.tool()
async def generate_image(prompt: str, negative_prompt: str = "text, watermark", width: int = 512, height: int = 512) -> str:
    """
    使用ComfyUI生成图片。
    :param prompt: 正向提示词（描述想要生成的图片内容）
    :param negative_prompt: 负向提示词（描述不想要的元素，默认：text, watermark）
    :param width: 图片宽度（默认：512）
    :param height: 图片高度（默认：512）
    :return: 生成的图片保存路径或错误信息
    """
    # 动态修改工作流参数
    workflow["6"]["inputs"]["text"] = prompt
    workflow["7"]["inputs"]["text"] = negative_prompt
    workflow["5"]["inputs"]["width"] = width
    workflow["5"]["inputs"]["height"] = height
    workflow["3"]["inputs"]["seed"] = int(time.time())

    try:
        # 提交任务
        prompt_id = await queue_prompt(workflow, base_url)
        print(f"Prompt ID: {prompt_id}")

        # 查询结果
        history = await get_history(prompt_id, base_url)
        print(f"History: {history}")

        # 下载并保存图片
        outputs = history["outputs"]
        for node_id, output in outputs.items():
            if "images" in output:
                for image in output["images"]:
                    filename = image["filename"]
                    subfolder = image["subfolder"]
                    folder_type = image["type"]
                    image_data = await get_image(filename, subfolder, folder_type, base_url)
                    save_file = Path(save_path) / filename
                    with open(save_file, "wb") as f:
                        f.write(image_data)
                    return f"Image generated and saved to: {save_file}"
        return "Error: No image generated"
    except Exception as e:
        return f"Error: Failed to generate image - {str(e)}"

if __name__ == "__main__":
    print("Starting ComfyUI MCP Server")
    mcp.run(transport='stdio')