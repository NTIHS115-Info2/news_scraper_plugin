# plugins/news_scraper/strategies/remote/scraper.py
import sys
import json
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
import asyncio

class ForagerStrategy:
    """
    情報採集策略 (Forager Strategy) - V4.0 "情報聚合器"
    核心職責：從一個可配置的 RSS Feed 列表中，並發地獲取並清理新聞內容。
    V4.0 新增功能:
    - fetch_news_from_feed: 專門處理單一 RSS Feed 的爬取邏輯。
    - run_concurrently: 作為總入口，使用 asyncio.gather 並發執行多個爬取任務。
    """
    def __init__(self):
        self.headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br, zstd',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Cache-Control': 'max-age=0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }

    def _clean_html_content(self, html_text: str) -> str:
        soup = BeautifulSoup(html_text, 'lxml')
        article_body = soup.find('article')
        if not article_body:
            article_body = soup
        paragraphs = article_body.find_all('p')
        cleaned_text = '\n'.join([p.get_text(strip=True) for p in paragraphs])
        return cleaned_text

    async def fetch_news_from_feed(self, rss_url: str) -> str:
        """ [V4.0 新增] 處理單一 RSS Feed 的核心邏輯 """
        try:
            loop = asyncio.get_event_loop()
            # 使用 run_in_executor 執行同步的 requests 請求，避免阻塞異步事件循環
            response = await loop.run_in_executor(None, lambda: requests.get(rss_url, headers=self.headers, timeout=15))
            response.raise_for_status()
            
            root = ET.fromstring(response.content)
            article_links = [item.find('link').text for item in root.findall('.//item')]

            all_cleaned_text = ""
            for link in article_links[:2]: # 每個來源取最新的2篇
                if not link: continue
                
                article_response = await loop.run_in_executor(None, lambda: requests.get(link, headers=self.headers, timeout=10))
                article_response.raise_for_status()
                
                cleaned_article = self._clean_html_content(article_response.text)
                all_cleaned_text += f"--- 新聞來源: {link} ---\n\n{cleaned_article}\n\n"
            return all_cleaned_text
        except Exception as e:
            # 在並發環境中，單個來源失敗不應中斷整個任務，只記錄錯誤
            error_message = f"--- 來源 {rss_url} 抓取失敗: {e} ---\n\n"
            print(error_message, file=sys.stderr)
            return error_message


    async def run_concurrently(self, rss_urls: list) -> dict:
        """ [V4.0 核心改造] 總入口，並發執行所有爬取任務 """
        try:
            # 創建一個任務列表，每個任務都是對一個 RSS Feed 的爬取
            tasks = [self.fetch_news_from_feed(url) for url in rss_urls]
            # 使用 asyncio.gather 來並發執行所有任務
            results = await asyncio.gather(*tasks)
            
            # 將所有成功抓取到的文本合併成一個長字串
            combined_text = "".join(results)

            return {
                "success": True,
                "result": { "source_urls": rss_urls, "article_text": combined_text.strip() },
                "resultType": "object"
            }
        except Exception as e:
            return { "success": False, "error": f"ForagerStrategy run_concurrently failed: {e}" }


async def main():
    if len(sys.argv) > 1:
        # 接收以逗號分隔的 URL 列表字符串
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