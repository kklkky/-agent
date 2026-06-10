# 论文生成Agent

基于RAG（检索增强生成）技术的领域论文智能生成系统，支持多领域学术论文自动生成。

## ✨ 功能特性

- **RAG检索增强**：基于FAISS向量数据库实现文献检索
- **多领域支持**：涵盖计算机科学、人工智能、生物学、物理学、化学、医学、经济学、心理学等领域
- **自定义章节**：支持选择摘要、引言、方法、结果、讨论等章节
- **实时进度显示**：可视化论文生成进度
- **Markdown导出**：一键下载生成的论文

## 🛠️ 技术栈

| 组件 | 技术 | 版本 |
|------|------|------|
| 后端框架 | FastAPI | 0.104.1 |
| 向量数据库 | FAISS | 1.7.4 |
| 文本嵌入 | Sentence Transformers | 2.2.2 |
| LLM | DeepSeek API | - |
| 前端 | HTML/CSS/JavaScript | - |

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

在 `backend/.env` 文件中配置：

```env
DEEPSEEK_API_KEY=your-deepseek-api-key
VECTOR_DB_PATH=./data/vector_store
FAISS_INDEX_PATH=./data/faiss_index
```

### 3. 启动服务

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问前端

直接打开 `index.html` 文件即可使用前端界面。

## 📡 API接口

### 生成论文

```bash
POST /api/generate-paper
Content-Type: application/json

{
    "topic": "深度学习在图像识别中的应用",
    "field": "计算机科学",
    "sections": ["摘要", "引言", "方法", "结果", "讨论"],
    "max_tokens": 3000
}
```

### 查询任务状态

```bash
GET /api/task-status/{task_id}
```

### 添加文档到知识库

```bash
POST /api/add-document?file_path=/path/to/document.txt
```

### 搜索知识库

```bash
GET /api/search?query=深度学习&top_k=5
```

## 📁 项目结构

```
paper-generator-agent/
├── backend/                    # 后端FastAPI项目
│   ├── src/
│   │   ├── main.py            # FastAPI主入口
│   │   ├── tasks.py           # 任务处理逻辑
│   │   ├── rag.py             # RAG系统核心
│   │   └── celery_app.py      # Celery配置（可选）
│   ├── data/
│   │   └── sample_paper.txt   # 示例文档
│   ├── .env                   # 环境变量配置
│   └── requirements.txt       # Python依赖
├── frontend/                   # React前端项目（可选）
├── index.html                 # 独立HTML前端
└── .gitignore                 # Git忽略配置
```

## 🔧 RAG实现

### 文档处理流程

1. **文档分块**：将长文档切分为500字符/块，50字符重叠
2. **向量嵌入**：使用`all-MiniLM-L6-v2`模型生成384维向量
3. **索引构建**：使用FAISS构建向量索引
4. **检索匹配**：根据查询向量返回Top-K相似文档
5. **内容生成**：结合检索结果生成论文内容

### 核心代码

```python
# 文档分块
def split_text(text, chunk_size=500, chunk_overlap=50):
    chunks = []
    for i in range(0, len(text), chunk_size - chunk_overlap):
        chunks.append(text[i:i + chunk_size])
    return chunks

# 向量检索
def search(query, top_k=5):
    query_embedding = model.encode(query)
    distances, indices = index.search(query_embedding.reshape(1, -1), top_k)
    return [chunks[i] for i in indices[0] if i != -1]
```

## 📊 使用示例

### 示例1：生成计算机科学论文

```bash
curl -X POST http://localhost:8000/api/generate-paper \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Transformer架构在自然语言处理中的应用",
    "field": "计算机科学",
    "sections": ["摘要", "引言", "方法"],
    "max_tokens": 2000
  }'
```

### 示例2：添加知识库文档

```bash
curl -X POST "http://localhost:8000/api/add-document?file_path=data/sample_paper.txt"
```

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

---

**注意**：本项目仅供研究和学习使用，请遵守相关法律法规和学术规范。