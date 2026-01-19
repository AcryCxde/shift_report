import os

bind = '0.0.0.0:8000'

workers = int(os.getenv('GUNICORN_WORKERS', '2'))
threads = int(os.getenv('GUNICORN_THREADS', '2'))

timeout = 120

max_requests = 1000
max_requests_jitter = 100

log_file = '-'
capture_output = True
