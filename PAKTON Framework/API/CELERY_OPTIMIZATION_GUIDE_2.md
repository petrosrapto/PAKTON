
1. Worker concurrency & process explosion

Typical problem
	•	You set CELERY_WORKER_CONCURRENCY (or --concurrency on celery worker) too high, or left it to the default (which is often #CPU cores).
	•	Each worker process/thread:
	•	imports your app
	•	loads models/clients
	•	uses memory

If each task uses e.g. 500MB and you have concurrency 8, that’s 4GB just for workers, plus OS, RabbitMQ, Redis, etc. On a small EC2 (2–4 GB RAM), this can lead to:
	•	Massive swapping
	•	Machine becomes unresponsive
	•	Tasks “stuck” because workers are actually thrashing, not progressing

What to do
	•	Start with low concurrency and increase slowly:

celery -A your_app worker --loglevel=INFO --concurrency=2


	•	If tasks are CPU-bound → prefer process concurrency (default).
	•	If tasks are I/O-bound → consider eventlet/gevent but only if you understand the implications (monkey patching, libraries need to be compatible).

⸻

2. Long-running or blocking tasks

If a task:
	•	Does a huge loop
	•	Waits on slow external APIs without timeout
	•	Reads/writes huge files
	•	Does heavy ML inference synchronously

…then workers get tied up for a long time.

Symptoms:
	•	Tasks stay in STARTED or RECEIVED forever
	•	New tasks pile up in the queue
	•	EC2 CPU at 100% or network I/O saturated

What to do
	•	Make tasks smaller and faster. Split big jobs into subtasks / a workflow.
	•	Always set timeouts:

# hard_time_limit kills the process, soft gives a SIGUSR1 you can handle
CELERY_TASK_TIME_LIMIT = 600        # hard, seconds
CELERY_TASK_SOFT_TIME_LIMIT = 540


	•	For external services (HTTP/DB/…):
	•	use short timeouts
	•	retries with backoff instead of hanging forever.

⸻

3. Queues filling up (RabbitMQ / Redis)

If consumers (workers) can’t keep up:
	•	Your queue grows in RabbitMQ/Redis
	•	These services eat RAM/disk
	•	Eventually the broker or EC2 chokes

What to check
	•	RabbitMQ management UI (or rabbitmqctl list_queues) → queue sizes
	•	Redis memory usage & eviction policy

Mitigations
	•	Use separate queues for heavy vs light tasks:

@app.task(queue="heavy")
def heavy_task(...):
    ...

@app.task(queue="default")
def light_task(...):
    ...

And then run different workers:

celery -A app worker -Q default --concurrency=4
celery -A app worker -Q heavy --concurrency=1


	•	Limit incoming rate (throttling) or backpressure from the service that produces tasks.
	•	Consider task expiry:

CELERY_TASK_DEFAULT_EXPIRES = 3600  # 1h, drop stale tasks



⸻

4. Memory leaks & not cleaning up

Typical sources:
	•	Keeping large objects (e.g. Pandas dataframes, ML model outputs) in global variables / module-level caches
	•	Appending to lists/dicts in module scope each time a task runs
	•	Big results stored in the backend (e.g. Redis/DB) and never revoked

Over time:
	•	Worker processes grow in memory (check with ps aux).
	•	EC2 runs out of RAM → becomes unresponsive.

What to do
	•	Make sure each task:
	•	doesn’t store huge objects in globals
	•	explicitly deletes big intermediate structures when done (del big_obj)
	•	Use max-tasks-per-child so worker processes are periodically recycled:

celery -A app worker --concurrency=2 --max-tasks-per-child=50

This is a big one for avoiding slow leaks.

	•	Avoid putting very large data in task results. Instead:
	•	Store big data in S3 / DB
	•	Pass only IDs/paths via Celery.

⸻

5. Result backend misuse (Redis/MySQL/etc.)

If you:
	•	Store results for every task
	•	Never call AsyncResult(...).forget() or configure expiry
	•	Return very large objects as the result

…then your result backend (often Redis) fills up and eats memory.

How to be careful
	•	If you don’t actually need results, disable them:

CELERY_RESULT_BACKEND = None

or on task level:

@app.task(ignore_result=True)
def my_task(...):
    ...


	•	Set expiries:

CELERY_RESULT_EXPIRES = 3600  # 1 hour


	•	Keep result payloads small (IDs, not big blobs).

⸻

6. Broker or backend on the same small EC2

RabbitMQ + Redis + Celery workers + your web app all on one small instance = recipe for:
	•	CPU contention
	•	Disk/IO saturation (especially if RabbitMQ persists messages)
	•	Memory exhaustion

Things to consider
	•	For serious workloads:
	•	Use managed RabbitMQ/Redis or separate EC2 instances.
	•	On a single instance:
	•	Monitor with htop, free -m, iostat, df -h.
	•	Give RabbitMQ enough disk and memory.
	•	Avoid huge durable messages; store big payloads elsewhere.

⸻

7. Misconfiguration of prefetch / acks

By default, Celery workers prefetch tasks from the queue.

If prefetch is too high:
	•	One worker can “reserve” many tasks
	•	They appear “stuck” in reserved state even if not executing yet

What to check
	•	worker_prefetch_multiplier:

worker_prefetch_multiplier = 1  # process one at a time per worker
task_acks_late = True           # ack after completion, not receipt



This can reduce perceived “stuckness” and make load more balanced.

⸻

8. EC2 unresponsive: what it usually means

Common root causes when the whole instance dies:
	•	Out of memory → kernel OOM killer massacres processes (check /var/log/syslog or dmesg).
	•	CPU 100% (e.g., too many CPU-bound tasks) → SSH, monitoring feel super slow.
	•	Disk full (RabbitMQ logs, task logs, temp files) → services crash or hang.

So yes, memory issue is very plausible, and often the first thing to investigate.

⸻

9. Concrete checklist for you

When running Celery/Redis/RabbitMQ on EC2, be especially careful about:
	1.	Concurrency
	•	Keep --concurrency low initially (2–4).
	•	Use --max-tasks-per-child to recycle workers.
	2.	Task design
	•	Short, focused tasks.
	•	No blocking forever; use timeouts.
	•	Avoid massive objects returned as results.
	3.	Queues
	•	Separate heavy vs light queues.
	•	Monitor queue lengths & growth.
	•	Use task expiry for stale jobs.
	4.	Memory & cleanup
	•	Watch ps aux --sort=-%mem regularly.
	•	Avoid global caches growing without bounds.
	•	Use result expiry or ignore results.
	5.	Infrastructure
	•	Check EC2 RAM/CPU/disk usage over time.
	•	Consider isolating broker/backend on a separate instance for heavier loads.