from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# 使用SQLite作为后端，无需Redis
db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'celery.db')
result_db_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'results.db')

# 确保data目录存在
os.makedirs(os.path.dirname(db_path), exist_ok=True)

celery_app = Celery(
    "paper_generator",
    broker=f"sqla+sqlite:///{db_path}",
    backend=f"db+sqlite:///{result_db_path}",
    include=["src.tasks"]
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,
    worker_prefetch_multiplier=1,
)