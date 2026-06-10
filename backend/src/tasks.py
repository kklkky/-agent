import os
import asyncio
from typing import Dict, Optional
from pydantic import BaseModel
from src.rag import RAGSystem
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com/v1"
)

rag_system = RAGSystem()

# 存储任务结果
task_results: Dict[str, dict] = {}
task_status: Dict[str, str] = {}

def generate_paper_async(task_id: str, topic: str, field: str, sections: list, max_tokens: int):
    """异步生成论文"""
    global task_results, task_status
    
    try:
        task_status[task_id] = 'processing'
        
        # 检索相关文献
        context = rag_system.get_relevant_context(f"{topic} {field}", top_k=5)
        
        paper_content = {}
        
        for i, section in enumerate(sections):
            prompt = build_prompt(topic, field, section, context)
            
            try:
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": f"你是一位{field}领域的专家学者，请用学术论文的风格写作。"},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens // len(sections),
                    temperature=0.7
                )
                
                paper_content[section] = response.choices[0].message.content.strip()
            except Exception as e:
                paper_content[section] = f"生成{section}时出错: {str(e)}"
            
            # 更新进度
            progress = int((i + 1) / len(sections) * 100)
            task_results[task_id] = {
                "progress": progress,
                "current_section": section
            }
        
        # 完成
        task_results[task_id] = {
            "topic": topic,
            "field": field,
            "content": paper_content,
            "context_used": len(context) > 0
        }
        task_status[task_id] = 'completed'
        
    except Exception as e:
        task_status[task_id] = 'failed'
        task_results[task_id] = {"error": str(e)}

def build_prompt(topic: str, field: str, section: str, context: str) -> str:
    base_prompt = f"""
请为主题"{topic}"撰写一篇{field}领域学术论文的{section}部分。

参考以下相关文献内容：
{context if context else "无可用文献"}

要求：
1. 使用正式的学术写作风格
2. 内容准确、逻辑清晰
3. 适当引用相关研究（如有）
4. 保持专业性和严谨性

请输出{section}的完整内容：
"""
    return base_prompt.strip()

def get_task_result(task_id: str) -> Optional[dict]:
    """获取任务结果"""
    return task_results.get(task_id)

def get_task_status(task_id: str) -> str:
    """获取任务状态"""
    return task_status.get(task_id, 'not_found')