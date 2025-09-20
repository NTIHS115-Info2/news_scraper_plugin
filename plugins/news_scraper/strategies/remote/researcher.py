# plugins/news_scraper/strategies/remote/researcher.py
import sys, json, asyncio, requests, time, hashlib
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from loguru import logger
from typing import List
from pathlib import Path
from data_models import ResearcherOutput, ResearcherResult

log_path = Path(__file__).parent.parent.parent.parent.parent / "logs" / "plugin.log"
logger.add(log_path, rotation="10 MB", retention="7 days", level="INFO")
CACHE_DIR = Path(__file__).parent / "cache"
CACHE_EXPIRATION = 86400
CACHE_DIR.mkdir(exist_ok=True)

class ResearcherStrategy:
    """ V12.0.4: Final Alpha Version """
    def __init__(self):
        self.ua = UserAgent()
        self.base_url = "https://html.duckduckgo.com/html/"
        logger.info("ResearcherStrategy (V12.0.4) 已初始化。")

    async def discover_sources(self, topic: str, num_results: int = 5) -> ResearcherOutput:
        cache_key = hashlib.md5(topic.encode('utf-8')).hexdigest() + f"_n{num_results}.json"
        cache_file = CACHE_DIR / cache_key
        if cache_file.exists():
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            if time.time() - cached_data["timestamp"] < CACHE_EXPIRATION:
                logger.info(f"從快取命中主題: {topic}")
                return ResearcherOutput.model_validate(cached_data["content"])
        try:
            logger.info(f"正在使用 [DuckDuckGo Direct Scrape] 為主題 '{topic}' 發現來源...")
            headers = {'User-Agent': self.ua.random}
            params = {"q": f"{topic} news"}
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: requests.get(self.base_url, headers=headers, params=params, timeout=15))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            link_tags = soup.select('a.result__a')
            links = []
            for tag in link_tags[:num_results]:
                href = tag['href']
                if href.startswith('//'):
                    links.append('https:' + href)
                else:
                    links.append(href)
            logger.info(f"成功發現 {len(links)} 個潛在來源。")
            result_obj = ResearcherResult(discovered_urls=links)
            output_obj = ResearcherOutput(success=True, result=result_obj)
            cache_content = {"timestamp": time.time(), "content": output_obj.model_dump()}
            cache_file.write_text(json.dumps(cache_content, ensure_ascii=False), encoding="utf-8")
            return output_obj
        except Exception as e:
            error_message = f"ResearcherStrategy (DuckDuckGo Scrape) failed: {e}"
            logger.exception(error_message)
            return ResearcherOutput(success=False, error=error_message)

def main():
    if len(sys.argv) > 2:
        try:
            topic = sys.argv[1]
            num_results = int(sys.argv[2])
            async def async_main():
                researcher = ResearcherStrategy()
                result_model = await researcher.discover_sources(topic, num_results=num_results)
                sys.stdout.buffer.write(result_model.model_dump_json().encode('utf-8'))
            asyncio.run(async_main())
        except Exception as e:
            error_output = ResearcherOutput(success=False, error=str(e))
            sys.stdout.buffer.write(error_output.model_dump_json().encode('utf-8'))
    else:
        error_result = ResearcherOutput(success=False, error="Insufficient arguments.")
        sys.stdout.buffer.write(error_result.model_dump_json().encode('utf-8'))

if __name__ == '__main__':
    main()