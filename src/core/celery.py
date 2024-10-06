from celery import Celery
from core.config import settings

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL,backend=settings.CELERY_RESULT_BACKEND)
celery_app.conf.timezone = settings.CELERY_TIMEZONE

celery_app.conf.beat_schedule = settings.CELERY_BEAT_SCHEDULE