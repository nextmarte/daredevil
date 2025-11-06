"""
Celery configuration for asynchronous task processing
"""
import os
from celery import Celery
from kombu import Queue

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

# Create Celery app
app = Celery('daredevil')

# Load config from Django settings with CELERY_ prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# ✅ CRITICAL FIX: Configurações para robustez contra desconexão Redis
app.conf.update(
    # Retry automático em caso de falha de conexão
    broker_connection_retry_on_startup=True,  # Retry conexão no startup
    broker_connection_retry=True,  # Retry em caso de perda de conexão
    broker_connection_max_retries=10,  # Máximo de 10 tentativas
    broker_connection_timeout=10,  # Timeout de 10 segundos por tentativa
    
    # Configurações de resiliência
    result_backend_transport_options={
        'master_name': 'mymaster',  # Para Redis Sentinel (se usado)
        'socket_keepalive': True,  # Keep-alive TCP
        'socket_keepalive_options': {
            1: 1,  # TCP_KEEPIDLE
            2: 1,  # TCP_KEEPINTVL
            3: 5,  # TCP_KEEPCNT
        },
        'retry_on_timeout': True,
        'health_check_interval': 30,  # Verificar saúde a cada 30s
    },
    
    # Configurações do broker
    broker_transport_options={
        'visibility_timeout': 43200,  # 12 horas
        'fanout_prefix': True,
        'fanout_patterns': True,
        'socket_keepalive': True,
        'socket_keepalive_options': {
            1: 1,
            2: 1,
            3: 5,
        },
        'retry_on_timeout': True,
        'health_check_interval': 30,
    },
    
    # Política de retry para tasks
    task_default_retry_delay=60,  # 1 minuto
    task_max_retry_delay=600,  # 10 minutos
)

# Auto-discover tasks from installed apps
app.autodiscover_tasks()


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task for testing Celery"""
    print(f'Request: {self.request!r}')
