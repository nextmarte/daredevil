"""
Celery configuration for asynchronous task processing
"""
import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('daredevil')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Configurações de retry para conexão com broker (Redis)
# Evita crash quando Redis está temporariamente indisponível
app.conf.update(
    # Retry automático ao conectar com broker
    broker_connection_retry=True,
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,  # Tentar até 10 vezes
    
    # Retry automático ao conectar com result backend
    result_backend_transport_options={
        'max_retries': 10,
        'interval_start': 0,
        'interval_step': 0.2,
        'interval_max': 0.5,
    },
    
    # Configurações de pool de conexões
    broker_pool_limit=10,
    
    # Health check do broker
    broker_heartbeat=10,  # Heartbeat a cada 10 segundos
)

# Auto-discover tasks from installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
