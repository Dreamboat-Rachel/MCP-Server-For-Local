import os
import asyncio
from typing import Any
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import sys

# 设置标准输出为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

# 初始化 MCP 服务器
mcp = FastMCP("GoogleSearchServer")

load_dotenv()

# 从 .env 文件中读取配置
CHROME_PATH = os.getenv("CHROME_PATH")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH")
PROXY = os.getenv("PROXY")

@mcp.tool(description="使用 Selenium 搜索 Google，返回前 10 个非广告搜索结果的标题、链接和摘要。输入参数为搜索关键词（如 'Python tutorial'）")
async def google_search(query: str) -> str:
    """
    使用 Selenium 执行 Google 搜索，返回前 10 个非广告结果的标题、链接和摘要。

    Args:
        query (str): 搜索关键词，例如 'Python tutorial'

    Returns:
        str: 前 10 个非广告搜索结果的标题、链接和摘要
    """
    if not query:
        return "⚠️ 请提供搜索关键词"

    try:
        # 配置 Chrome 选项
        chrome_options = Options()
        if CHROME_PATH:
            chrome_options.binary_location = CHROME_PATH
            
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        if PROXY:
            chrome_options.add_argument(f'--proxy-server={PROXY}')

        # 设置 WebDriver 服务
        service = Service(executable_path=CHROMEDRIVER_PATH) if CHROMEDRIVER_PATH else Service()

        # 在异步线程中运行 Selenium
        loop = asyncio.get_event_loop()
        driver = await loop.run_in_executor(
            None,
            lambda: webdriver.Chrome(service=service, options=chrome_options)
        )

        try:
            # 打开谷歌搜索页面
            driver.get("https://www.google.com")
            print(f"DEBUG: Step 1 - Opened Google homepage for query: {query}")

            # 等待搜索框出现
            wait = WebDriverWait(driver, 10)
            search_box = wait.until(EC.presence_of_element_located((By.NAME, "q")))
            print("DEBUG: Step 2 - Search box located")

            # 模拟人工输入
            for char in query:
                search_box.send_keys(char)
                await asyncio.sleep(0.05)
            
            await asyncio.sleep(0.5)
            search_box.send_keys(Keys.RETURN)
            print(f"DEBUG: Step 3 - Search submitted for query: {query}")

            # 等待搜索结果加载
            try:
                wait.until(EC.presence_of_element_located((By.ID, "search")))
                print("DEBUG: Step 4 - Search results container loaded")
            except TimeoutException:
                print("DEBUG: Step 4 - Timeout waiting for results, possible CAPTCHA")
                await asyncio.sleep(10)

            # 确保页面滚动加载更多结果
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            await asyncio.sleep(3)
            print("DEBUG: Step 5 - Scrolled page to load more results")

            # 使用 XPath 提取搜索结果
            results = driver.find_elements(By.XPATH, "//a[descendant::h3]")
            print(f"DEBUG: Step 6 - Found {len(results)} raw results")
            result_list = []
            count = 0

            for result in results:
                if count >= 10:  # 限制前 10 个非广告结果
                    break
                try:
                    # 检查是否为广告
                    parent = result.find_element(By.XPATH, "./ancestor::div[contains(@class, 'tF2Cxc') or contains(@class, 'yuRUbf') or contains(@class, 'g')]")
                    if parent.find_elements(By.XPATH, ".//ancestor::*[contains(text(), 'Ad')]") or \
                       parent.find_elements(By.XPATH, ".//ancestor::*[contains(text(), '赞助')]"):
                        print(f"DEBUG: Skipping ad at position {count + 1}")
                        continue

                    # 获取标题和链接
                    try:
                        title_element = result.find_element(By.TAG_NAME, "h3")
                        title = title_element.text
                        link = result.get_attribute("href")
                        if not link or "google.com" in link:
                            continue
                    except NoSuchElementException:
                        print(f"DEBUG: No title/link found for result {count + 1}")
                        continue
                    
                    # 获取摘要内容
                    try:
                        snippet_candidates = [
                            ".//following-sibling::div//span[@class='aCOpRe']",
                            ".//following-sibling::div[contains(@class, 'VwiC3b') or contains(@class, 'IsZvec')]",
                            ".//following-sibling::div//span"
                        ]
                        snippet = "暂无摘要"
                        for xpath in snippet_candidates:
                            try:
                                snippet_element = parent.find_element(By.XPATH, xpath)
                                snippet = snippet_element.text.strip()
                                if snippet:
                                    break
                            except NoSuchElementException:
                                continue
                        if snippet == "暂无摘要":
                            print(f"DEBUG: No snippet found for result {count + 1}")
                    except Exception as e:
                        print(f"DEBUG: Error finding snippet for result {count + 1}: {str(e)}")

                    count += 1
                    result_list.append(
                        f"{count}. {title}\n"
                        f"   链接: {link}\n"
                        f"   摘要: {snippet}\n"
                    )
                except Exception as e:
                    print(f"DEBUG: Error processing result {count + 1}: {str(e)}")
                    continue

            if not result_list:
                return "未找到非广告搜索结果"
            
            output = "\n\n".join(result_list)
            print(f"DEBUG: Step 7 - Final results: {output}")
            return f"谷歌搜索 '{query}' 的结果：\n\n{output}"

        finally:
            print("DEBUG: Step 8 - Closing browser")
            await loop.run_in_executor(None, driver.quit)

    except Exception as e:
        return f"⚠️ 搜索失败: {str(e)}"

if __name__ == "__main__":
    print("DEBUG: Starting MCP GoogleSearchServer")
    mcp.run(transport="stdio")