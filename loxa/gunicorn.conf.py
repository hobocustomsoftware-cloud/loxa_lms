import multiprocessing, os
bind = "0.0.0.0:8000"
workers = int(os.getenv("WEB_WORKERS", multiprocessing.cpu_count() * 2 + 1))
threads = int(os.getenv("WEB_THREADS", 1))
worker_class = os.getenv("WEB_WORKER_CLASS", "gthread")  # or "uvicorn.workers.UvicornWorker"
timeout = int(os.getenv("WEB_TIMEOUT", 60))
graceful_timeout = 30
keepalive = 5
accesslog = "-"
errorlog = "-"
