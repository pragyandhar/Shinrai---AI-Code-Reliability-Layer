# WHAT DOES THIS FILE DO: Creates the Celery app instance — connects to Redis as broker and backend.

# ================== IMPORTS ==================
from celery import Celery

from app.config import settings
# ================== IMPORTS ==================


# =========== VARIABLES : Celery app instance used across all tasks ===========
celery_app = Celery(
    "shinrai",
    broker=settings.redis_url,
    backend=settings.redis_api,
)
# =========== VARIABLES : Celery app instance used across all tasks ===========


# =========== CELERY CONFIG ===========
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json", 
    accept_content=["json"], # USE: Prevents Pickle Attacks
    timezone="UTC",
    enable_utc=True,
)

celery_app.autodiscover_tasks(["app.tasks"])
# =========== CELERY CONFIG ===========
