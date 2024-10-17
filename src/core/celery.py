from celery import Celery
from celery.schedules import crontab

from core.config import settings

celery_app = Celery("worker", broker=settings.CELERY_BROKER_URL, backend=settings.CELERY_RESULT_BACKEND)
celery_app.autodiscover_tasks(['src.notifications'])

celery_app.conf.timezone = settings.CELERY_TIMEZONE
celery_app.conf.beat_schedule = {
    "send_quiz_remind_notifications": {
        "task": "src.notifications.tasks.quiz_remind_notification",
        "schedule": crontab(hour=0, minute=0),
    },
}
