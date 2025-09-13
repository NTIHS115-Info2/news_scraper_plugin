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

# [V5.0] 配置 Loguru，所有日誌將寫入文件
log_path = Path(__file__).parent.parent.parent.parent.parent / "logs" / "plugin.log"
logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO")

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_EXPIRATION = 3600 # 快取有效期：1小時 (3600秒)
CACHE_DIR.mkdir(exist_ok=True)


class ForagerStrategy:
    """ V5.0: Production-Grade Robustness """
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }
        logger.info("ForagerStrategy (V5.0) 已初始化。")

    def _clean_html_content(self, html_text: str) -> str:
        # ... (此函數不變)
        soup = BeautifulSoup(html_text, 'lxml')
        article_body = soup.find('article')
        if not article_body:
            article_body = soup
        paragraphs = article_body.find_all('p')
        cleaned_text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
        return cleaned_text


    async def fetch_news_from_feed(self, rss_url: str) -> tuple[str, str | None]:
        # [V5.0] 快取邏輯
        cache_key = rss_url.replace("https://", "").replace("http://", "").replace("/", "_") + ".json"
        cache_file = CACHE_DIR / cache_key

        if cache_file.exists():
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            if time.time() - cached_data["timestamp"] < CACHE_EXPIRATION:
                logger.info(f"從快取命中: {rss_url}")
                return cached_data["content"], None # 返回內容和 None (無錯誤)

        # [V5.0] 錯誤處理與日誌記錄
        try:
            logger.info(f"正在從網路抓取: {rss_url}")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(rss_url, headers=self.headers, timeout=15))
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            article_links = [item.find('link').text for item in root.findall('.//item')]

            all_cleaned_text = ""
            for link in article_links[:2]:
                if not link: continue
                article_response = await loop.run_in_executor(None, lambda: requests.get(link, headers=self.headers, timeout=10))
                article_response.raise_for_status()
                cleaned_article = self._clean_html_content(article_response.text)
                all_cleaned_text += f"--- 新聞來源: {link} ---\n\n{cleaned_article}\n\n"

            # 寫入快取
            cache_content = {"timestamp": time.time(), "content": all_cleaned_text}
            cache_file.write_text(json.dumps(cache_content, ensure_ascii=False), encoding="utf-8")

            return all_cleaned_text, None
        except Exception as e:
            error_message = f"來源 {rss_url} 抓取失敗: {e}"
            logger.error(error_message) # 將詳細錯誤寫入日誌
            return "", error_message # 返回空內容和錯誤訊息


    async def run_concurrently(self, rss_urls: list) -> dict:
        try:
            tasks = [self.fetch_news_from_feed(url) for url in rss_urls]
            results = await asyncio.gather(*tasks)
            
            successful_contents = [content for content, error in results if error is None]
            failed_sources = [error for content, error in results if error is not None]
            
            combined_text = "".join(successful_contents)

            # [V5.0] 即使部分失敗，也回傳成功，並在 errors 字段中報告
            return {
                "success": True,
                "result": { "source_urls": rss_urls, "article_text": combined_text.strip() },
                "errors": failed_sources,
                "resultType": "object"
            }
        except Exception as e:
            logger.exception("run_concurrently 發生未知錯誤")
            return { "success": False, "error": f"ForagerStrategy run_concurrently failed: {e}" }


async def main():
    if len(sys.argv) > 1:
        urls_string = sys.argv[1]
        url_list = [url.strip() for url in urls_string.split(',')]
        forager = ForagerStrategy()
        result = await forager.run_concurrently(rss_urls=url_list)
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        error_result = {"success": False, "error": "No RSS URL list provided to scraper.py"}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())