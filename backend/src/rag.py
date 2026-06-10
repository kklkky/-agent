import os
import json
import faiss
import numpy as np
from typing import List, Dict, Optional

class RAGSystem:
    def __init__(self):
        self.model = None
        self.index = None
        self.documents = []
        self.index_path = os.getenv("FAISS_INDEX_PATH", "./data/faiss_index")
        self.documents_path = os.getenv("VECTOR_DB_PATH", "./data/vector_store")
        self.use_simulated = False
        self._load_index()
    
    def _load_index(self):
        try:
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
            
            documents_file = os.path.join(self.documents_path, "documents.json")
            if os.path.exists(documents_file):
                with open(documents_file, 'r', encoding='utf-8') as f:
                    self.documents = json.load(f)
        except Exception as e:
            print(f"加载索引失败: {e}")
            self.index = faiss.IndexFlatL2(384)
    
    def _ensure_model(self):
        if self.model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                self.use_simulated = False
            except Exception as e:
                print(f"无法加载SentenceTransformer模型，使用模拟模式: {e}")
                self.use_simulated = True
    
    def _save_index(self):
        os.makedirs(os.path.dirname(self.index_path), exist_ok=True)
        faiss.write_index(self.index, self.index_path)
        
        documents_file = os.path.join(self.documents_path, "documents.json")
        os.makedirs(os.path.dirname(documents_file), exist_ok=True)
        with open(documents_file, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)
    
    def add_document(self, file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            chunks = self._chunk_text(content, chunk_size=500, chunk_overlap=50)
            
            if not self.use_simulated:
                self._ensure_model()
            
            for chunk in chunks:
                if self.use_simulated:
                    embedding = np.random.rand(384).astype('float32')
                else:
                    embedding = self.model.encode(chunk)
                
                if self.index is None:
                    self.index = faiss.IndexFlatL2(len(embedding))
                self.index.add(np.array([embedding]))
                self.documents.append({"content": chunk, "source": file_path})
            
            self._save_index()
            return len(chunks)
        except Exception as e:
            print(f"添加文档失败: {e}")
            return 0
    
    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = min(start + chunk_size, text_length)
            chunks.append(text[start:end])
            start += chunk_size - chunk_overlap
        
        return chunks
    
    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        if self.index is None or len(self.documents) == 0:
            return []
        
        if not self.use_simulated:
            self._ensure_model()
        
        if self.use_simulated:
            query_embedding = np.random.rand(384).astype('float32')
        else:
            query_embedding = self.model.encode(query)
        
        distances, indices = self.index.search(np.array([query_embedding]), top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if idx >= 0 and idx < len(self.documents):
                results.append({
                    "content": self.documents[idx]["content"],
                    "source": self.documents[idx]["source"],
                    "score": float(distances[0][i])
                })
        
        return results
    
    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        results = self.search(query, top_k)
        context = "\n\n".join([result["content"] for result in results])
        return context