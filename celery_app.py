from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Initialize Celery
celery_app = Celery(
    'image_processing',
    broker=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    backend=os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
    include=['app']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Add result expiration (0.5 hours)
    result_expires=30*60,
    
    # Configure Redis backend
    redis_max_connections=20,
    redis_socket_timeout=30,
    
    # Task settings
    task_time_limit=300,  # 5 minutes
    task_soft_time_limit=240,  # 4 minutes
    
    # Result backend settings
    result_backend_transport_options={
        'retry_policy': {
            'timeout': 5.0
        }
    }
)
