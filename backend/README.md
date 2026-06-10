# 论文生成Agent

基于RAG技术的领域论文智能生成系统。

## 技术栈

- **后端**: FastAPI + Python
- **任务队列**: Celery + Redis
- **向量数据库**: FAISS
- **嵌入模型**: Sentence Transformers
- **前端**: React + Vite

## 环境要求

- Python 3.8+
- Redis 7.0+
- Node.js 18+ (前端)

## 安装步骤

### 1. 安装依赖

```bash
cd backend
python -m venv venv
venv/Scripts/activate
pip install -r requirements.txt
```

### 2. 配置环境变量

编辑 `.env` 文件：

```env
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=your-openai-api-key
VECTOR_DB_PATH=./data/vector_store
FAISS_INDEX_PATH=./data/faiss_index
```

### 3. 启动Redis

```bash
redis-server
```

### 4. 启动Celery Worker

```bash
cd backend
celery -A src.celery_app worker --loglevel=info
```

### 5. 启动FastAPI服务

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 6. 启动前端

```bash
cd frontend
npm install
npm start
```

## API接口

### 生成论文

```
POST /api/generate-paper
```

请求体：
```json
{
    "topic": "深度学习在图像识别中的应用",
    "field": "计算机科学",
    "sections": ["摘要", "引言", "方法", "结果", "讨论"],
    "max_tokens": 3000
}
```

响应：
```json
{
    "task_id": "abc123",
    "status": "pending"
}
```

### 查询任务状态

```
GET /api/task-status/{task_id}
```

响应：
```json
{
    "task_id": "abc123",
    "status": "completed",
    "result": {
        "topic": "...",
        "field": "...",
        "content": {...}
    }
}
```

### 添加文档到知识库

```
POST /api/add-document?file_path=/path/to/document.txt
```

### 搜索知识库

```
GET /api/search?query=深度学习&top_k=5
```

## 使用说明

1. 在前端输入论文主题和选择研究领域
2. 选择需要生成的章节
3. 点击"生成论文"按钮
4. 等待生成完成，可下载为Markdown文件

## 项目结构

```
backend/
├── src/
│   ├── main.py          # FastAPI主入口
│   ├── celery_app.py    # Celery配置
│   ├── tasks.py         # 任务定义
│   └── rag.py           # RAG系统
├── data/
│   ├── vector_store/    # 文档存储
│   └── faiss_index      # 向量索引
├── .env                 # 环境变量
└── requirements.txt     # 依赖列表

frontend/
├── src/
│   ├── App.js           # 主应用组件
│   ├── App.css          # 样式文件
│   └── index.js         # 入口文件
├── public/
│   └── index.html       # HTML模板
└── package.json         # 前端依赖
```