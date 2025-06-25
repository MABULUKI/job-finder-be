"""Gunicorn configuration file for the Job Finder application."""
import multiprocessing

# Bind to this socket
bind = "0.0.0.0:8000"

# Number of worker processes
# A good rule of thumb is 2-4 x $(NUM_CORES)
workers = multiprocessing.cpu_count() * 2 + 1

# Worker class - use gevent for better concurrency
worker_class = "sync"  # You can change to "gevent" if you install it

# Timeout for worker processes (seconds)
timeout = 120

# Maximum number of requests a worker will process before restarting
max_requests = 1000
max_requests_jitter = 50

# Process name
proc_name = "job_finder_gunicorn"

# Log level
loglevel = "info"

# Access log format
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr

# Preload application code before worker processes are forked
preload_app = True

# Clean up worker processes when they die
worker_tmp_dir = "/dev/shm"
