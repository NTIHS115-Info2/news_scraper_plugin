# plugins/news_scraper/strategies/remote/researcher.py
import sys
import json
import asyncio
import os
from typing import List # [V8.0.3 核心修正] 新增缺失的導入語句
from googlesearch import search as fallback_search
from serpapi import GoogleSearch
from loguru import logger

class ResearcherStrategy:
    """
    研究員策略 (Researcher Strategy) - V8.0.3 "專業偵察兵"
    核心職責：採用主副武器策略發現情報來源。
    """
    def __init__(self):
        self.api_key = os.getenv("SERPAPI_API_KEY")
        logger.info("ResearcherStrategy (V8.0.3) 已初始化。")

    async def _discover_with_api(self, topic: str, num_results: int) -> List[str]:
        if not self.api_key:
            raise ValueError("SERPAPI_API_KEY 環境變數未設置。")
        
        logger.info(f"正在使用 [主武器 SerpApi] 為主題 '{topic}' 發現來源...")
        
        params = {
            "q": f"{topic} news",
            "engine": "google",
            "num": num_results,
            "api_key": self.api_key
        }
        
        loop = asyncio.get_event_loop()
        search_result = await loop.run_in_executor(None, lambda: GoogleSearch(params).get_dict())
        
        links = [result["link"] for result in search_result.get("organic_results", [])]
        return links

    async def _discover_with_fallback(self, topic: str, num_results: int) -> List[str]:
        logger.warning(f"主武器 SerpApi 失效，切換至 [副武器 Fallback Search]...")
        loop = asyncio.get_event_loop()
        links = await loop.run_in_executor(
            None, 
            lambda: list(fallback_search(f"{topic} news", num_results=num_results, lang="en"))
        )
        return links

    async def discover_sources(self, topic: str, num_results: int = 5) -> dict:
        try:
            links = []
            try:
                links = await self._discover_with_api(topic, num_results)
            except Exception as api_error:
                logger.critical(f"主武器 SerpApi 遭遇嚴重錯誤: {api_error}")
                links = await self._discover_with_fallback(topic, num_results)

            logger.info(f"最終發現 {len(links)} 個潛在來源。")
            
            return {
                "success": True,
                "result": {"discovered_urls": links},
                "resultType": "object"
            }
        except Exception as e:
            error_message = f"ResearcherStrategy 在所有嘗試後均失敗: {e}"
            logger.exception(error_message)
            return {"success": False, "error": error_message}

async def main():
    if len(sys.argv) > 2:
        topic = sys.argv[1]
        num_results = int(sys.argv[2])
        researcher = ResearcherStrategy()
        result = await researcher.discover_sources(topic, num_results=num_results)
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        error_result = {"success": False, "error": "Insufficient arguments."}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())