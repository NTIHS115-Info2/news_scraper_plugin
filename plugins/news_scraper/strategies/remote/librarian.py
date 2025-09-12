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
    圖書管理員策略 (Librarian Strategy) - V1.0.3
    核心職責：接收長篇文本內容與使用者查詢，利用向量語義搜索，過濾出與查詢最相關的文本片段。
    """
    def __init__(self, model_name='all-MiniLM-L6-v2'):
        self.model = SentenceTransformer(model_name)
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
    """
    用於被外部調用的主函數，或在獨立執行時運行單元測試。
    """
    if len(sys.argv) > 2:
        # 被 Node.js 調用時的模式
        text_content = sys.argv[1]
        query = sys.argv[2]
        librarian = LibrarianStrategy()
        result = await librarian.filter_content(text_content=text_content, query=query)
        # [核心修正] 強制以 UTF-8 編碼輸出 JSON
        sys.stdout.buffer.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
    else:
        # 獨立執行時的單元測試模式
        print("--- 執行 librarian.py 單元測試 ---")
        sample_content = """
        In a major leadership change, The Walt Disney Company's board of directors announced that Bob Iger is returning to lead Disney as Chief Executive Officer, effective immediately. He succeeds Bob Chapek, who has stepped down from his position. Iger has agreed to serve as Disney’s C.E.O. for two years.
        """
        user_query = "Who is the C.E.O. of Disney?"
        
        print("正在初始化圖書管理員策略...")
        librarian = LibrarianStrategy()
        print(f"\n開始執行內容過濾任務...")
        print(f"使用者查詢: '{user_query}'")
        result = await librarian.filter_content(text_content=sample_content, query=user_query)

        print("\n--- 過濾任務完成 ---")
        if result['success']:
            print("任務成功！")
            print("\n--- 找到的相關文本片段 ---")
            print(json.dumps(result['result'], indent=2, ensure_ascii=False))
        else:
            print("任務失敗！")
            print(f"錯誤訊息: {result['error']}")

if __name__ == '__main__':
    asyncio.run(main())