# plugins/news_scraper/strategies/remote/librarian.py

import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
import asyncio
import re
import sys
import json

class LibrarianStrategy:
    """
    圖書管理員策略 (Librarian Strategy) - V2.0.1
    核心職責：接收長篇文本內容與使用者查詢，利用向量語義搜索，過濾出與查詢最相關的文本片段。
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        # [V2.0.1 核心修正] 將所有日誌輸出重定向到 stderr
        print(f"正在加載句向量模型: {model_name} ...", file=sys.stderr)
        self.model = SentenceTransformer(model_name)
        print("模型加載完成。", file=sys.stderr)
        self.priority = 100

    def _chunk_text(self, text, min_length=50, max_length=300):
        sentences = re.split(r'(?<=[.!?\n\r。！？])\s*', text)
        chunks = []
        current_chunk = ""
        for sentence in sentences:
            if not sentence: continue
            if len(current_chunk) + len(sentence) <= max_length:
                current_chunk += " " + sentence
            else:
                if len(current_chunk.strip()) >= min_length: chunks.append(current_chunk.strip())
                current_chunk = sentence
        if len(current_chunk.strip()) >= min_length: chunks.append(current_chunk.strip())
        return chunks

    async def filter_content(self, text_content: str, query: str, top_k: int = 3):
        try:
            chunks = self._chunk_text(text_content)
            if not chunks:
                return {"success": True, "result": [], "resultType": "list"}

            chunk_embeddings = self.model.encode(chunks, convert_to_tensor=True).cpu().numpy()

            index = faiss.IndexFlatL2(chunk_embeddings.shape[1])
            index.add(chunk_embeddings)

            query_embedding = self.model.encode([query], convert_to_tensor=True).cpu().numpy()

            distances, indices = index.search(query_embedding, top_k)

            results = []
            for i in range(len(indices[0])):
                idx, dist = indices[0][i], distances[0][i]
                if idx < len(chunks):
                    results.append({"chunk": chunks[idx], "score": float(dist)})

            return {"success": True, "result": results, "resultType": "list"}
        except Exception as e:
            error_message = f"LibrarianStrategy filter_content failed: {str(e)}"
            return {"success": False, "error": error_message}

async def main():
    if len(sys.argv) > 2:
        text_content = sys.argv[1]
        query = sys.argv[2]
        librarian = LibrarianStrategy()
        result = await librarian.filter_content(text_content=text_content, query=query)
        # [核心協議] 強制以 UTF-8 編碼輸出 JSON 到 stdout
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        # 即使是錯誤訊息，也應該是一個乾淨的 JSON
        error_result = {"success": False, "error": "Insufficient arguments for librarian.py"}
        sys.stdout.buffer.write(json.dumps(error_result, ensure_ascii=False).encode('utf-8'))


if __name__ == '__main__':
    asyncio.run(main())