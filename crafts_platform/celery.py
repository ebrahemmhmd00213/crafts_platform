# crafts_platform/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crafts_platform.settings')

app = Celery('crafts_platform')

# قراءة إعدادات Celery من settings.py مع البادئة CELERY_
app.config_from_object('django.conf:settings', namespace='CELERY')

# اكتشاف المهام تلقائياً في كل تطبيقات Django
app.autodiscover_tasks()