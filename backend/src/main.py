from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.tasks import generate_paper_async, get_task_result, get_task_status
from src.rag import RAGSystem
import uuid
import os

app = FastAPI(title="论文生成Agent", description="基于RAG的领域论文生成系统")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_system = RAGSystem()

class PaperRequest(BaseModel):
    topic: str
    field: str
    sections: list = ["摘要", "引言", "方法", "结果", "讨论"]
    max_tokens: int = 3000

class TaskStatus(BaseModel):
    task_id: str
    status: str
    result: dict = None
    error: str = None

@app.post("/api/generate-paper", response_model=dict)
async def generate_paper(request: PaperRequest, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())
    
    background_tasks.add_task(
        generate_paper_async,
        task_id,
        request.topic,
        request.field,
        request.sections,
        request.max_tokens
    )
    
    return {"task_id": task_id, "status": "pending"}

@app.get("/api/task-status/{task_id}", response_model=TaskStatus)
async def get_status(task_id: str):
    status = get_task_status(task_id)
    result = get_task_result(task_id)
    
    if status == 'not_found':
        return {"task_id": task_id, "status": "not_found"}
    elif status == 'pending':
        return {"task_id": task_id, "status": "pending"}
    elif status == 'processing':
        return {"task_id": task_id, "status": "processing", "result": result}
    elif status == 'completed':
        return {"task_id": task_id, "status": "completed", "result": result}
    elif status == 'failed':
        return {"task_id": task_id, "status": "failed", "error": result.get("error", "Unknown error")}
    else:
        return {"task_id": task_id, "status": status}

@app.post("/api/add-document")
async def add_document(file_path: str):
    count = rag_system.add_document(file_path)
    return {"status": "success", "message": f"已添加{count}个文档块到知识库"}

@app.get("/api/search")
async def search(query: str, top_k: int = 5):
    results = rag_system.search(query, top_k)
    return {"results": results}

@app.get("/")
async def root():
    return {"message": "论文生成Agent API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)