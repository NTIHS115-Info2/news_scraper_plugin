# plugins/news_scraper/strategies/remote/scraper.py
import sys
import json
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import asyncio
from pathlib import Path
import time
from loguru import logger
import random
from data_models import ScraperOutput, ScraperResult
from playwright.async_api import async_playwright # [V7.0] 引入 Playwright

# ... (日誌和快取配置不變) ...
log_path = Path(__file__).parent.parent.parent.parent.parent / "logs" / "plugin.log"
logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO")
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_EXPIRATION = 3600
CACHE_DIR.mkdir(exist_ok=True)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
]


class ForagerStrategy:
    """ V7.0: Browser Automation Fallback """
    def __init__(self):
        logger.info("ForagerStrategy (V7.0) 已初始化。")

    def _get_random_headers(self) -> dict:
        return {'User-Agent': random.choice(USER_AGENTS)}

    def _clean_html_content(self, html_text: str) -> str:
        # ... (此函數不變) ...
        soup = BeautifulSoup(html_text, 'lxml')
        article_body = soup.find('article')
        if not article_body:
            article_body = soup
        paragraphs = article_body.find_all('p')
        cleaned_text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
        return cleaned_text
        
    async def _fetch_with_browser(self, url: str) -> str:
        """ [V7.0 新增] 使用 Playwright 作為備用抓取方案 """
        logger.info(f"使用瀏覽器自動化抓取: {url}")
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
            await page.goto(url, wait_until='domcontentloaded', timeout=20000)
            content = await page.content()
            await browser.close()
            return content

    async def fetch_news_from_feed(self, rss_url: str) -> tuple[str, str | None]:
        # ... (重試與快取邏輯不變) ...
        for attempt in range(2): # 減少重試次數，為瀏覽器模式留出機會
            try:
                # ... 快取命中邏輯 ...
                cache_key = rss_url.replace("https://", "").replace("http://", "").replace("/", "_") + ".json"
                cache_file = CACHE_DIR / cache_key
                if cache_file.exists():
                    cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
                    if time.time() - cached_data["timestamp"] < CACHE_EXPIRATION:
                        logger.info(f"從快取命中: {rss_url}")
                        return cached_data["content"], None

                logger.info(f"正在使用 Requests 抓取 (嘗試 {attempt + 1}/2): {rss_url}")
                # ... requests 抓取邏輯 ...
                loop = asyncio.get_event_loop()
                headers = self._get_random_headers()
                response = await loop.run_in_executor(None, lambda: requests.get(rss_url, headers=headers, timeout=15))
                response.raise_for_status()
                root = ET.fromstring(response.content)
                article_links = [item.find('link').text for item in root.findall('.//item')]
                all_cleaned_text = ""
                for link in article_links[:1]: # 每個來源只精準打擊1篇
                    if not link: continue
                    link_headers = self._get_random_headers()
                    try:
                        # [V7.0] 首先嘗試 requests
                        article_response = await loop.run_in_executor(None, lambda: requests.get(link, headers=link_headers, timeout=10))
                        article_response.raise_for_status()
                        html_content = article_response.text
                    except requests.exceptions.HTTPError as http_err:
                        # [V7.0] 如果遇到 403 等錯誤，則啟動攻城槌
                        if http_err.response.status_code == 403:
                            logger.warning(f"Requests 遭遇 403 Forbidden，切換至 Playwright 模式: {link}")
                            html_content = await self._fetch_with_browser(link)
                        else:
                            raise # 其他 HTTP 錯誤則正常拋出
                    
                    cleaned_article = self._clean_html_content(html_content)
                    all_cleaned_text += f"--- 新聞來源: {link} ---\n\n{cleaned_article}\n\n"
                
                cache_content = {"timestamp": time.time(), "content": all_cleaned_text}
                cache_file.write_text(json.dumps(cache_content, ensure_ascii=False), encoding="utf-8")
                return all_cleaned_text, None

            except Exception as e:
                # ... (錯誤處理與重試邏輯不變) ...
                error_message = f"來源 {rss_url} 抓取失敗 (嘗試 {attempt + 1}): {e}"
                logger.warning(error_message)
                if attempt < 1:
                    await asyncio.sleep(2)
                else:
                    logger.error(f"來源 {rss_url} 連續2次抓取失敗。")
                    return "", error_message
        return "", "所有重試均失敗。"


    async def run_concurrently(self, rss_urls: list) -> ScraperOutput:
        # ... (此函數不變) ...
        try:
            tasks = [self.fetch_news_from_feed(url) for url in rss_urls]
            results = await asyncio.gather(*tasks)
            successful_contents = [content for content, error in results if error is None]
            failed_sources = [error for content, error in results if error is not None]
            combined_text = "".join(successful_contents)
            return ScraperOutput(
                success=True,
                result=ScraperResult(source_urls=rss_urls, article_text=combined_text.strip()),
                errors=failed_sources
            )
        except Exception as e:
            logger.exception("run_concurrently 發生未知錯誤")
            return ScraperOutput(success=False, errors=[f"ForagerStrategy run_concurrently failed: {e}"])

async def main():
    # ... (此函數不變) ...
    if len(sys.argv) > 1:
        urls_string = sys.argv[1]
        url_list = [url.strip() for url in urls_string.split(',')]
        forager = ForagerStrategy()
        result_model = await forager.run_concurrently(rss_urls=url_list)
        sys.stdout.buffer.write(result_model.model_dump_json().encode('utf-8'))
    else:
        error_result = ScraperOutput(success=False, errors=["No RSS URL list provided to scraper.py"])
        sys.stdout.buffer.write(error_result.model_dump_json().encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())