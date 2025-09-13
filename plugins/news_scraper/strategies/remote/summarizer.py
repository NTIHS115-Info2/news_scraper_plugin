# plugins/news_scraper/strategies/remote/summarizer.py

import sys
import json
import asyncio
from transformers import pipeline

class SummarizerStrategy:
    """
    情報分析師策略 (Summarizer Strategy) - V3.0
    核心職責：接收文本片段，並根據指定的模式和長度要求，生成精煉的摘要。
    V3.0 新增功能:
    - 支持 'multi' 模式，為每個獨立的文本片段生成摘要。
    - 支持 'length' 參數 ('short', 'medium', 'long')，動態控制摘要長度。
    """
    def __init__(self, model_name='sshleifer/distilbart-cnn-12-6'):
        print(f"正在加載摘要模型: {model_name} ...", file=sys.stderr)
        self.summarizer = pipeline("summarization", model=model_name)
        print("模型加載完成。", file=sys.stderr)

    async def summarize_text(self, text_chunks: list, mode: str = 'single', length: str = 'medium') -> dict:
        try:
            # 根據 length 參數設定摘要的最小和最大長度
            length_config = {
                'short': {'min_length': 20, 'max_length': 50},
                'medium': {'min_length': 40, 'max_length': 100},
                'long': {'min_length': 80, 'max_length': 200}
            }
            config = length_config.get(length, length_config['medium'])

            if mode == 'multi':
                # 多角度摘要模式：為每個 chunk 生成摘要
                if not text_chunks:
                    return {"success": True, "result": {"multi_angle_summaries": []}, "resultType": "object"}
                summaries = self.summarizer(text_chunks, **config)
                # 將原始 chunk 與其摘要配對
                multi_angle_result = [
                    {"original_chunk": chunk, "summary": item['summary_text']}
                    for chunk, item in zip(text_chunks, summaries)
                ]
                final_result = {"multi_angle_summaries": multi_angle_result}

            else: # 預設為 'single' 模式
                # 單一總結模式：合併所有 chunk 後生成一個總摘要
                combined_text = ' '.join(text_chunks)
                if not combined_text.strip():
                    return {"success": True, "result": {"summary": "No content to summarize."}, "resultType": "object"}
                
                summary_list = self.summarizer(combined_text, **config)
                summary_text = summary_list[0]['summary_text']
                final_result = {"summary": summary_text}

            return {
                "success": True,
                "result": final_result,
                "resultType": "object"
            }
        except Exception as e:
            error_message = f"SummarizerStrategy failed: {str(e)}"
            return {"success": False, "error": error_message}

async def main():
    if len(sys.argv) > 1:
        # 從命令行接收 JSON 字符串格式的輸入
        input_data = json.loads(sys.argv[1])
        chunks = input_data.get("chunks", [])
        mode = input_data.get("mode", "single")
        length = input_data.get("length", "medium")

        summarizer = SummarizerStrategy()
        result = await summarizer.summarize_text(text_chunks=chunks, mode=mode, length=length)
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        error_result = {"success": False, "error": "No JSON input provided to summarizer.py"}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))

if __name__ == '__main__':
    asyncio.run(main())