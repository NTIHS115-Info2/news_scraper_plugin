# plugins/news_scraper/strategies/remote/scraper.py
import sys
import json
import requests
from bs4 import BeautifulSoup
import asyncio
from pathlib import Path
from loguru import logger
from playwright.async_api import async_playwright
import random

# ... (日誌和 User Agent 配置繼承自 V8.0.3，不變) ...
log_path = Path(__file__).parent.parent.parent.parent.parent / "logs" / "plugin.log"
logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO")

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]

class ForagerStrategy:
    """
    情報採集策略 - V9.0.1 "通用內容提取器" (歷史恢復版)
    核心職責：恢復 V7.0 的混合抓取策略，以應對通用 HTML 網頁的反爬蟲機制。
    """
    def __init__(self):
        logger.info("ForagerStrategy (V9.0.1) 已初始化。")

    def _get_random_headers(self) -> dict:
        return {'User-Agent': random.choice(USER_AGENTS)}

    def _clean_html_content(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, 'lxml')
        article_body = soup.find('article')
        if not article_body:
            logger.warning("在頁面中未找到 <article> 標籤，將採用通用的 <p> 標籤提取策略。")
            article_body = soup
        paragraphs = article_body.find_all('p')
        cleaned_text = '\n'.join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
        return cleaned_text

    async def _fetch_with_browser(self, url: str) -> str:
        logger.info(f"檢測到反爬蟲機制，切換至 Playwright 攻城槌模式: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            content = await page.content()
            await browser.close()
            return content

    async def fetch_content(self, url: str) -> dict:
        """
        [V9.0.1 核心改造] 恢復 V7.0 的 requests -> playwright 降級策略
        """
        try:
            html_content = ""
            logger.info(f"正在使用 Requests 抓取: {url}")
            try:
                response = requests.get(url, headers=self._get_random_headers(), timeout=15)
                response.raise_for_status()
                html_content = response.text
            except requests.exceptions.RequestException as req_err:
                logger.warning(f"Requests 抓取失敗: {req_err}。將嘗試使用 Playwright。")
                html_content = await self._fetch_with_browser(url)

            if not html_content:
                 raise ValueError("兩種抓取方法均未能獲取到頁面內容。")

            cleaned_article = self._clean_html_content(html_content)

            return {
                "success": True,
                "result": { "source_url": url, "article_text": cleaned_article.strip() },
                "resultType": "object"
            }
        except Exception as e:
            error_message = f"ForagerStrategy 在所有嘗試後均失敗 for URL {url}: {e}"
            logger.error(error_message)
            return {"success": False, "error": error_message}


def main():
    if len(sys.argv) > 1:
        url = sys.argv[1]
        forager = ForagerStrategy()
        # [V9.0.1] 由於 playwright 的引入，我們必須在異步環境中運行
        async def async_main():
            result = await forager.fetch_content(url=url)
            sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        asyncio.run(async_main())
    else:
        error_result = {"success": False, "error": "No URL provided to scraper.py"}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    main()