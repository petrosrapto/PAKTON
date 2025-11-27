# PAKTON Celery/Redis/RabbitMQ Optimization Guide

## 🚨 Critical Issues Found in Your Setup

### 1. **Memory Issues**
- **Global singleton Archivist**: Created once and never garbage collected, accumulates memory
- **ML model caching**: HuggingFace models stay in memory indefinitely
- **Event loop leaks**: `asyncio.run()` creates new event loops repeatedly without cleanup
- **No task cleanup**: Resources not released after task completion
- **Database connection pool**: `pool_size=10, max_overflow=20` can create up to 30 connections per worker

### 2. **Worker Configuration Issues**
- **Too many concurrent workers**: `--concurrency=4` for ML workloads = 4 workers × heavy models = memory explosion
- **No task time limits**: Tasks can run forever and block workers
- **No memory limits**: Workers can consume all available RAM
- **Missing prefetch settings**: Workers grab too many tasks at once
- **Debug logging in production**: `--loglevel=debug` creates excessive I/O

### 3. **Redis/RabbitMQ Issues**
- **Results never expire**: Redis fills up with old task results
- **No result cleanup**: Task metadata accumulates indefinitely
- **Missing queue limits**: Queues can grow unbounded
- **No memory limits**: Redis/RabbitMQ can consume all RAM
- **No connection pooling limits**: Can exhaust file descriptors

---

## ⚡ Quick Emergency Actions

If your EC2 is currently unresponsive:

```bash
# 1. Stop workers first (preserves queue)
docker stop multiagentframework_worker

# 2. Check what's consuming resources
docker stats
free -m
df -h

# 3. Clear Redis if full (WARNING: loses task results)
docker exec -it redis redis-cli FLUSHDB

# 4. Purge stuck queues (WARNING: loses pending tasks)
docker exec -it rabbitmq rabbitmqctl purge_queue multiagentframework_service_queue

# 5. Restart services in order
docker-compose restart redis rabbitmq
docker-compose up -d multiagentframework_worker
```

---

## 🔧 Immediate Configuration Fixes

### Step 1: Update `config.py`

Add comprehensive Celery configuration:

```python
class Config:
    # ... existing config ...
    
    ############################# Celery Configuration #########################
    CELERY_BROKER_URL = get_required_env("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = get_required_env("CELERY_RESULT_BACKEND")
    TASK_ROUTES = { f"{SERVICE_NAME}.tasks.*": {"queue": SERVICE_QUEUE} }
    
    # Task execution limits - CRITICAL for preventing hung tasks
    CELERY_TASK_TIME_LIMIT = 600  # 10 minutes hard limit (kills task)
    CELERY_TASK_SOFT_TIME_LIMIT = 540  # 9 minutes soft limit (raises exception)
    
    # Result backend settings - PREVENTS Redis from filling up
    CELERY_RESULT_EXPIRES = 3600  # Results expire after 1 hour
    CELERY_TASK_RESULT_EXPIRES = 3600
    CELERY_TASK_IGNORE_RESULT = False  # Change to True if you don't need results
    
    # Worker settings - PREVENTS memory leaks
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1  # Only prefetch 1 task per worker
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 10  # Restart worker after 10 tasks
    CELERY_WORKER_MAX_MEMORY_PER_CHILD = 512000  # 512MB limit per worker (adjust for your EC2)
    
    # Task acknowledgment - PREVENTS task loss on worker crash
    CELERY_TASK_ACKS_LATE = True  # Acknowledge task only after completion
    CELERY_TASK_REJECT_ON_WORKER_LOST = True  # Requeue if worker dies
    
    # Broker settings
    CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
    CELERY_BROKER_CONNECTION_MAX_RETRIES = 10
    CELERY_BROKER_POOL_LIMIT = 10  # Limit broker connections
    
    # Performance optimizations
    CELERY_RESULT_COMPRESSION = None  # Saves CPU
    CELERY_TASK_COMPRESSION = 'gzip'  # Compress task messages
    
    # Monitoring
    CELERY_WORKER_SEND_TASK_EVENTS = True
    CELERY_TASK_SEND_SENT_EVENT = True
    CELERY_TASK_TRACK_STARTED = True
    
    # Serialization (use JSON for safety)
    CELERY_TASK_SERIALIZER = 'json'
    CELERY_RESULT_SERIALIZER = 'json'
    CELERY_ACCEPT_CONTENT = ['json']
    
    # Timezone
    CELERY_TIMEZONE = 'UTC'
    CELERY_ENABLE_UTC = True
    ############################################################################
```

Then update `tasks.py` to use these settings:

```python
# Update celery_app configuration
celery_app.conf.update(
    task_time_limit=Config.CELERY_TASK_TIME_LIMIT,
    task_soft_time_limit=Config.CELERY_TASK_SOFT_TIME_LIMIT,
    result_expires=Config.CELERY_RESULT_EXPIRES,
    worker_prefetch_multiplier=Config.CELERY_WORKER_PREFETCH_MULTIPLIER,
    worker_max_tasks_per_child=Config.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_max_memory_per_child=Config.CELERY_WORKER_MAX_MEMORY_PER_CHILD,
    task_acks_late=Config.CELERY_TASK_ACKS_LATE,
    task_reject_on_worker_lost=Config.CELERY_TASK_REJECT_ON_WORKER_LOST,
    broker_connection_retry_on_startup=Config.CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP,
    broker_pool_limit=Config.CELERY_BROKER_POOL_LIMIT,
    task_serializer=Config.CELERY_TASK_SERIALIZER,
    result_serializer=Config.CELERY_RESULT_SERIALIZER,
    accept_content=Config.CELERY_ACCEPT_CONTENT,
    timezone=Config.CELERY_TIMEZONE,
    enable_utc=Config.CELERY_ENABLE_UTC,
)
```

### Step 2: Fix `tasks.py` - Critical Memory Issues

**Problem**: Global `archivist` instance with `asyncio.run()` creates event loop leaks.

**Solution**: Use per-task instances with proper cleanup.

Replace the global archivist pattern:

```python
# REMOVE THIS - causes memory leaks
# archivist = None
# def get_archivist():
#     global archivist
#     if archivist is None:
#         from Archivist import Archivist
#         archivist = Archivist()
#     return archivist

# NEW APPROACH - per-task instance with cleanup
@celery_app.task(
    name=f'{Config.SERVICE_NAME}.tasks.process_query',
    bind=True,
    default_retry_delay=5,
    max_retries=3,
    soft_time_limit=540,  # 9 minutes
    time_limit=600,  # 10 minutes hard limit
    acks_late=True,
)
def async_process_query(self, query: str, thread_id: str = None, config: dict = None, user_email: str = None):
    """Process query with proper resource cleanup"""
    archivist = None
    loop = None
    
    try:
        from Archivist import Archivist
        archivist = Archivist()  # Create fresh instance per task
        
        # Use existing event loop if available, else create one
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        async def process_query_async():
            async with archivist:
                result = await archivist.process_query(query, thread_id, config)
                return result
        
        # Run with the managed event loop
        result = loop.run_until_complete(process_query_async())
        
        # Database tracking logic (unchanged)
        if user_email and result.get('thread_id'):
            try:
                with get_db_session() as db:
                    thread_id = result['thread_id']
                    conversation = ConversationRepository.get_by_thread_id(db, thread_id)
                    if not conversation:
                        title = query[:500] if len(query) <= 500 else query[:497] + "..."
                        ConversationRepository.create(
                            db=db,
                            thread_id=thread_id,
                            user_email=user_email,
                            title=title
                        )
                    messages = result['response']['messages']
                    message_count = ConversationRepository.count_human_and_ai_messages(messages)
                    ConversationRepository.update_message_count_and_timestamp(
                        db=db,
                        thread_id=thread_id,
                        message_count=message_count
                    )
                    logger.info(f"Conversation tracked for user {user_email}, thread {thread_id}")
            except Exception as db_error:
                logger.error(f"Failed to track conversation: {str(db_error)}")
        
        return create_task_response(
            status="SUCCESS",
            task_id=self.request.id,
            message="Query processed successfully",
            data={
                "thread_id": result['thread_id'],
                "response_content": result['response']['messages'][-1].content,
            }
        )
        
    except Exception as e:
        logger.error(f"Error in async_process_query: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying... Attempt {self.request.retries + 1}/{self.max_retries}")
            raise self.retry(exc=e, countdown=5)
        
        return create_task_response(
            status="FAILURE",
            task_id=self.request.id,
            message=f"Failed to process query: {e}"
        )
    
    finally:
        # CRITICAL: Cleanup resources
        if archivist is not None:
            try:
                # Close any open connections in archivist
                if hasattr(archivist, 'close'):
                    archivist.close()
                if hasattr(archivist, '__del__'):
                    archivist.__del__()
                del archivist
            except Exception as cleanup_error:
                logger.error(f"Archivist cleanup error: {cleanup_error}")
        
        # Don't close the event loop if we're reusing it
        # Let Python garbage collect it
        
        # Force garbage collection to free ML models
        import gc
        gc.collect()
        
        logger.debug("Task cleanup completed")
```

Apply same pattern to other tasks:

```python
@celery_app.task(
    name=f'{Config.SERVICE_NAME}.tasks.index_document',
    bind=True,
    soft_time_limit=540,
    time_limit=600,
    acks_late=True,
)
def async_index_document(self, file_content: bytes, metadata: dict):
    archivist = None
    temp_file_path = None
    
    try:
        from Archivist import Archivist
        archivist = Archivist(config={"enable_vectordb": True, "run_name": "Example Index"})
        
        # ... existing logic ...
        
    finally:
        # Cleanup temp file
        if temp_file_path and os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        
        # Cleanup archivist
        if archivist is not None:
            try:
                if hasattr(archivist, 'close'):
                    archivist.close()
                del archivist
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
        
        import gc
        gc.collect()
```

**REMOVE** the worker initialization hook at the bottom:

```python
# DELETE THIS - causes memory leaks
# @celery_app.on_after_configure.connect
# def setup_worker_initialization(sender, **kwargs):
#     ...
```

### Step 3: Update `docker-compose.yml`

**Critical changes for ML workloads:**

```yaml
services:
  # ... rabbitmq and redis (updated below) ...

  multiagentframework_worker:
    container_name: multiagentframework_worker
    build:
      context: ..
      dockerfile: API/Dockerfile
    depends_on:
      - multiagentframework_service
      - rabbitmq
      - redis
      - postgres
    working_dir: /app
    command: [
      "celery",
      "-A", "API.tasks.celery_app",
      "worker",
      "-Q", "multiagentframework_service_queue",
      "--concurrency=1",  # CHANGED: 1 worker for ML (not 4!)
      "--loglevel=info",  # CHANGED: info instead of debug (less I/O)
      "--max-tasks-per-child=10",  # NEW: restart after 10 tasks (prevents leaks)
      "--max-memory-per-child=512000",  # NEW: 512MB limit per worker
      "--prefetch-multiplier=1"  # NEW: only fetch 1 task at a time
    ]
    env_file:
      - .env
    environment:
      CELERY_BROKER_URL: "amqp://rabbitmq:5672"
      CELERY_RESULT_BACKEND: "redis://redis:6379/0"
      SERVICE_NAME: "multiagentframework_service"
      PYTHONUNBUFFERED: "1"
    restart: always
    volumes:
      - ~/.cache/huggingface:/root/.cache/huggingface
    # NEW: Resource limits
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G

  # Redis with memory limits
  redis:
    image: redis:latest
    container_name: redis
    ports:
      - "6379:6379"
    restart: always
    command: redis-server --maxmemory 512mb --maxmemory-policy allkeys-lru
    # LRU eviction when memory limit reached
    deploy:
      resources:
        limits:
          memory: 1G

  # RabbitMQ with memory limits
  rabbitmq:
    image: rabbitmq:3-management
    container_name: rabbitmq
    ports:
      - "5672:5672"
      - "15672:15672"
    restart: always
    environment:
      RABBITMQ_VM_MEMORY_HIGH_WATERMARK: 512MB
      RABBITMQ_DISK_FREE_LIMIT: 2GB
    deploy:
      resources:
        limits:
          memory: 1G
```

### Step 4: Update `database/config.py`

Reduce connection pool to prevent exhaustion:

```python
# Create SQLAlchemy engine
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,  # CHANGED: reduced from 10
    max_overflow=10,  # CHANGED: reduced from 20
    pool_recycle=3600,  # NEW: recycle connections every hour
    pool_timeout=30,  # NEW: timeout after 30 seconds
    echo=False,
)
```

---

## 📊 Monitoring & Debugging

### Add Celery Flower for Real-time Monitoring

Add to `docker-compose.yml`:

```yaml
  flower:
    image: mher/flower
    container_name: flower
    command: celery --broker=amqp://rabbitmq:5672 flower --port=5555
    ports:
      - "5555:5555"
    depends_on:
      - rabbitmq
      - redis
    restart: always
```

Access at `http://localhost:5555` (or your EC2 IP) to monitor:
- Active tasks
- Worker status
- Memory usage per worker
- Queue lengths
- Task success/failure rates

### Health Check Endpoint

Add to `tasks.py`:

```python
@celery_app.task(name='health_check')
def health_check():
    """Simple health check task"""
    import gc
    from datetime import datetime
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "garbage_collector": {
            "collected": gc.collect(),
            "stats": gc.get_stats()
        }
    }
```

### Monitor Redis Memory

```bash
# Check Redis memory usage
docker exec -it redis redis-cli INFO memory

# Check key count
docker exec -it redis redis-cli DBSIZE

# See all task keys
docker exec -it redis redis-cli --scan --pattern 'celery-task-meta-*'

# Clean old results manually (if needed)
docker exec -it redis redis-cli --scan --pattern 'celery-task-meta-*' | \
  xargs docker exec -i redis redis-cli DEL
```

### Monitor RabbitMQ Queues

```bash
# Check queue lengths
docker exec rabbitmq rabbitmqctl list_queues

# See queue details
docker exec rabbitmq rabbitmqctl list_queues name messages consumers

# Check memory usage
docker exec rabbitmq rabbitmqctl status
```

### EC2 Monitoring Commands

```bash
# Memory usage (run every 5 seconds)
watch -n 5 'free -m'

# Docker container stats
docker stats --no-stream

# Disk usage
df -h

# Check for OOM killer logs
dmesg | grep -i "out of memory"
sudo grep -i "out of memory" /var/log/syslog

# File descriptors
lsof | wc -l
ulimit -n

# CPU and memory by process
htop
```

---

## 🎯 Best Practices Checklist

### Task Design
- ✅ Keep tasks small (< 10 minutes execution time)
- ✅ Add timeouts to all tasks (`soft_time_limit`, `time_limit`)
- ✅ Make tasks idempotent (can be safely retried)
- ✅ Always use `try/finally` for resource cleanup
- ✅ Delete large objects explicitly (`del large_obj`)

### Worker Management
- ✅ Use `--concurrency=1` for ML tasks (not 4!)
- ✅ Use `--max-tasks-per-child=10` to prevent memory leaks
- ✅ Set `--max-memory-per-child` appropriate to your EC2
- ✅ Use `--prefetch-multiplier=1` to prevent task hoarding
- ✅ Monitor worker memory with `docker stats`

### Result Management
- ✅ Set `CELERY_RESULT_EXPIRES` to prevent Redis bloat
- ✅ Use `ignore_result=True` for fire-and-forget tasks
- ✅ Keep result payloads small (< 1MB)
- ✅ Store large data in S3/DB, pass only IDs

### Queue Management
- ✅ Monitor queue depth regularly
- ✅ Implement separate queues for different priority tasks
- ✅ Set up alerts for queue depth > 100
- ✅ Consider task expiry for non-critical tasks

### Error Handling
- ✅ Use exponential backoff on retries
- ✅ Log full tracebacks for debugging
- ✅ Set up dead letter queue for failed tasks
- ✅ Alert on repeated failures

---

## 🚀 Deployment Steps

1. **Backup current configuration**:
   ```bash
   cd /Users/petrosrapto/Desktop/PAKTON/PAKTON/PAKTON\ Framework/API
   cp config.py config.py.backup
   cp tasks.py tasks.py.backup
   cp docker-compose.yml docker-compose.yml.backup
   ```

2. **Apply configuration changes** (as detailed above)

3. **Test locally first**:
   ```bash
   docker-compose down
   docker-compose up --build
   ```

4. **Monitor during first deployment**:
   - Open Flower at `http://localhost:5555`
   - Run `watch -n 5 'docker stats --no-stream'`
   - Monitor logs: `docker-compose logs -f multiagentframework_worker`

5. **Deploy to EC2**:
   ```bash
   # SSH to EC2
   cd /path/to/PAKTON/API
   
   # Pull latest code
   git pull
   
   # Stop workers gracefully
   docker-compose stop multiagentframework_worker
   
   # Rebuild and restart
   docker-compose up --build -d
   
   # Monitor
   docker-compose logs -f multiagentframework_worker
   ```

---

## 🔥 Troubleshooting Common Issues

### Issue: Tasks stuck in "RECEIVED" state
**Cause**: Workers crashed or too busy
**Solution**:
```bash
docker-compose restart multiagentframework_worker
docker exec rabbitmq rabbitmqctl list_queues
```

### Issue: EC2 becomes unresponsive
**Cause**: Out of memory
**Solution**:
```bash
# Check memory
free -m
# Check what's using memory
docker stats
# Stop workers if needed
docker stop multiagentframework_worker
```

### Issue: Redis memory full
**Cause**: Old task results not expiring
**Solution**:
```bash
# Check Redis memory
docker exec -it redis redis-cli INFO memory
# Flush if necessary (WARNING: loses all data)
docker exec -it redis redis-cli FLUSHDB
```

### Issue: Queue growing indefinitely
**Cause**: Workers can't keep up
**Solution**:
- Reduce incoming task rate
- Add more workers (carefully!)
- Purge old tasks: `docker exec rabbitmq rabbitmqctl purge_queue multiagentframework_service_queue`

---

## 📈 Scaling Strategies

### Current Setup (Single EC2)
- **Best for**: Development, light production
- **Limits**: ~10-20 concurrent tasks

### Horizontal Scaling
1. **Separate worker instances**:
   - Run workers on different EC2 instances
   - Point to same RabbitMQ/Redis
   
2. **Use managed services**:
   - ElastiCache for Redis
   - Amazon MQ for RabbitMQ
   - Reduces operational burden

3. **Auto-scaling workers**:
   - Use ECS/Kubernetes
   - Scale based on queue depth

### Vertical Scaling
- Upgrade EC2 instance type
- More RAM = more concurrent workers
- But fix memory leaks first!

---

## ⚠️ What NOT to Do

❌ **Don't** increase `--concurrency` without fixing memory leaks
❌ **Don't** run without `--max-tasks-per-child`
❌ **Don't** use debug logging in production
❌ **Don't** store large results in Redis
❌ **Don't** use global singletons for ML models
❌ **Don't** create new event loops with `asyncio.run()` repeatedly
❌ **Don't** ignore worker memory usage
❌ **Don't** let queues grow unbounded

---

## 📞 Quick Reference Commands

```bash
# Check worker status
docker-compose ps

# Restart workers
docker-compose restart multiagentframework_worker

# View logs
docker-compose logs -f multiagentframework_worker

# Check queue length
docker exec rabbitmq rabbitmqctl list_queues

# Check Redis memory
docker exec -it redis redis-cli INFO memory

# Monitor resources
docker stats --no-stream

# Purge queue (CAREFUL!)
docker exec rabbitmq rabbitmqctl purge_queue multiagentframework_service_queue

# Clear Redis (CAREFUL!)
docker exec -it redis redis-cli FLUSHDB

# Access Flower
http://localhost:5555

# Access RabbitMQ Management
http://localhost:15672 (guest/guest)
```

---

## Summary

The main issues are:
1. **Memory leaks** from global Archivist + asyncio.run()
2. **Too many workers** (4 instead of 1 for ML)
3. **No cleanup** of resources after tasks
4. **No limits** on Redis/RabbitMQ memory
5. **No task timeouts** or worker recycling

After applying these fixes, your system should be stable. Monitor with Flower and adjust limits based on your EC2 instance size.
