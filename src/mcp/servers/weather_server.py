import json
import httpx
from typing import Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import os

# 初始化 MCP 服务器
mcp = FastMCP("WeatherServer")

load_dotenv()

class GaodeWeatherTool:
    def __init__(self, api_key = os.getenv("GAODE_API_KEY")):
        """初始化高德天气工具"""
        self.api_key = api_key
        self.base_url = "https://restapi.amap.com/v3/weather/weatherInfo"
        self.headers = {"User-Agent": "weather-app/1.0"}

    async def query_weather(self, city: str, extensions: str = "base") -> dict:
        """
        从高德地图 API 查询天气信息。
        :param city: 高德地图城市代码（例如北京是 '110000'）
        :param extensions: 'base' 为实时天气，'all' 为预报天气
        :return: 天气数据字典，若出错则包含 error 字段
        """
        params = {
            "key": self.api_key,
            "city": city,
            "extensions": extensions,
            "output": "json"
        }
        print(f"DEBUG: Querying weather for city: {city}, params: {params}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(self.base_url, params=params, headers=self.headers, timeout=10.0)
                print(f"DEBUG: Response status: {response.status_code}, content: {response.text}")
                response.raise_for_status()
                data = response.json()
                if data.get("status") != "1":
                    return {"error": f"API error: {data.get('info', 'Unknown error')}"}
                lives = data.get("lives", [])
                if not lives:
                    return {"message": "No weather data found for this city"}
                weather_info = lives[0]
                result = {
                    "city": weather_info.get("city", "Unknown"),
                    "weather": weather_info.get("weather", "Unknown"),
                    "temperature": weather_info.get("temperature", "Unknown"),
                    "winddirection": weather_info.get("winddirection", "Unknown"),
                    "windpower": weather_info.get("windpower", "Unknown"),
                    "humidity": weather_info.get("humidity", "Unknown"),
                    "reporttime": weather_info.get("reporttime", "Unknown")
                }
                return result
            except httpx.RequestException as e:
                return {"error": f"Weather query error: {str(e)}"}

    def format_weather(self, weather_data: dict) -> str:
        """将天气数据格式化为易读文本"""
        if "error" in weather_data:
            return f"⚠️ {weather_data['error']}"
        if "message" in weather_data:
            return f"⚠️ {weather_data['message']}"
        
        return (
            f"🌍 {weather_data['city']}\n"
            f"🌡 温度: {weather_data['temperature']}°C\n"
            f"💧 湿度: {weather_data['humidity']}%\n"
            f"🌬 风向: {weather_data['winddirection']} 风力: {weather_data['windpower']} 级\n"
            f"🌤 天气: {weather_data['weather']}\n"
            f"⏰ 更新时间: {weather_data['reporttime']}\n"
        )

# 实例化天气工具
weather_tool = GaodeWeatherTool()

@mcp.tool()
async def query_weather(city_code: str) -> str:
    """
    输入高德地图城市代码，返回今日天气查询结果。
    :param city_code: 高德地图城市代码（例如北京是 '110000'）
    :return: 格式化后的天气信息
    """
    data = await weather_tool.query_weather(city_code, extensions="base")
    return weather_tool.format_weather(data)

if __name__ == "__main__":
    print("DEBUG: Starting MCP WeatherServer")
    mcp.run(transport='stdio')