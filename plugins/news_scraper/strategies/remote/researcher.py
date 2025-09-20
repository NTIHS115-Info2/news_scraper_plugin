# plugins/news_scraper/strategies/remote/researcher.py
import sys
import json
import asyncio
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from typing import List

class ResearcherStrategy:
    """
    研究員策略 - V11.0 (繼承自 V10.0 "游擊偵察兵")
    核心職責：直接爬取 DuckDuckGo 搜尋結果頁面，發現情報來源。
    """
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://html.duckduckgo.com/html/"
        logger.info("ResearcherStrategy (V11.0) 已初始化。")

    async def discover_sources(self, topic: str, num_results: int = 5) -> dict:
        try:
            logger.info(f"正在使用 [DuckDuckGo Direct Scrape] 為主題 '{topic}' 發現來源...")
            headers = {'User-Agent': self.ua.random}
            params = {"q": f"{topic} news"}

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.get(self.base_url, headers=headers, params=params, timeout=15)
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'lxml')
            link_tags = soup.select('a.result__a')
            links = [tag['href'] for tag in link_tags[:num_results]]

            logger.info(f"成功發現 {len(links)} 個潛在來源。")
            return {
                "success": True,
                "result": {"discovered_urls": links},
                "resultType": "object"
            }
        except Exception as e:
            error_message = f"ResearcherStrategy (DuckDuckGo Scrape) failed: {e}"
            logger.exception(error_message)
            return {"success": False, "error": error_message}

def main():
    if len(sys.argv) > 2:
        topic = sys.argv[1]
        num_results = int(sys.argv[2])
    
        async def async_main():
            researcher = ResearcherStrategy()
            result = await researcher.discover_sources(topic, num_results=num_results)
            sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
        
        asyncio.run(async_main())
    else:
        error_result = {"success": False, "error": "Insufficient arguments."}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    main()