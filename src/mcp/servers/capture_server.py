import logging
from mcp.server.fastmcp import FastMCP
import cv2
import random
import os
import asyncio
from dotenv import load_dotenv
from deepface import DeepFace

# 设置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 初始化 MCP 服务器
mcp = FastMCP("CameraCaptureServer")
load_dotenv()

# 设置保存路径
SAVE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "save")
os.makedirs(SAVE_DIR, exist_ok=True)

def capture_and_analyze():
    try:
        logger.debug("尝试打开摄像头")
        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            return "⚠️ 无法打开摄像头"
        ret, frame = cap.read()
        if not ret:
            cap.release()
            return "⚠️ 无法读取画面"
        random_suffix = random.randint(10000, 99999)
        image_path = os.path.join(SAVE_DIR, f"captured_image_{random_suffix}.jpg")
        cv2.imwrite(image_path, frame)
        cap.release()
        logger.debug(f"图片保存至 {image_path}")

        logger.debug("开始微表情分析")
        analysis = DeepFace.analyze(img_path=image_path, actions=['emotion'], enforce_detection=False)
        emotion = analysis[0]['dominant_emotion']
        logger.debug(f"微表情分析完成: {emotion}")
        return f"成功拍摄并保存至 {image_path}，检测到的表情: {emotion}"
    except Exception as e:
        logger.debug(f"操作失败: {str(e)}")
        return f"⚠️ 操作失败: {str(e)}"

@mcp.tool(description="使用摄像头拍照并分析微表情")
async def capture_camera_image() -> str:
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, capture_and_analyze)
    return result

if __name__ == "__main__":
    logger.debug("启动 CameraCaptureServer")
    mcp.run(transport="stdio")