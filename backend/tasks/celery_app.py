import os

from celery import Celery


redis_url = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "corre_compara",
    broker=redis_url,
    backend=redis_url,
)

celery_app.conf.update(
    timezone="America/Mexico_City",
    enable_utc=False,
    broker_connection_retry_on_startup=True,
)

# Beat: correr todos los scrapers cada 6 horas.
celery_app.conf.beat_schedule = {
    "scrape_all_products_every_6_hours": {
        "task": "tasks.scraping_jobs.scrape_all_products",
        "schedule": 6 * 60 * 60,
    }
}

