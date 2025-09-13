# plugins/news_scraper/strategies/remote/summarizer.py

import sys
import json
import asyncio
from transformers import pipeline

class SummarizerStrategy:
    """
    情報分析師策略 (Summarizer Strategy) - V2.0.1
    核心職責：接收一段長文本，利用預訓練的摘要模型，生成一段精煉的總結。
    """
    def __init__(self, model_name='sshleifer/distilbart-cnn-12-6'):
        # [V2.0.1 核心修正] 將所有日誌輸出重定向到 stderr
        print(f"正在加載摘要模型: {model_name} ...", file=sys.stderr)
        self.summarizer = pipeline("summarization", model=model_name)
        print("模型加載完成。", file=sys.stderr)

    async def summarize_text(self, text_content: str) -> dict:
        try:
            if not text_content or not text_content.strip():
                 return {"success": True, "result": {"summary": "No relevant content found to summarize."}, "resultType": "object"}

            summary_list = self.summarizer(text_content, max_length=150, min_length=30, do_sample=False)
            summary_text = summary_list[0]['summary_text']

            return {
                "success": True,
                "result": {"summary": summary_text},
                "resultType": "object"
            }
        except Exception as e:
            error_message = f"SummarizerStrategy failed: {str(e)}"
            return {"success": False, "error": error_message}

async def main():
    if len(sys.argv) > 1:
        text_content = sys.argv[1]
        summarizer = SummarizerStrategy()
        result = await summarizer.summarize_text(text_content)
        # [核心協議] 強制以 UTF-8 編碼輸出 JSON 到 stdout
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        error_result = {"success": False, "error": "No text content provided to summarizer.py"}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())