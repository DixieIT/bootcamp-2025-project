import time
import asyncio
import logging

logger = logging.getLogger(__name__)

initial_timestamp = time.monotonic()
timeline_events = []

def log_event(task, event):
    """Log an event with timestamp to visualize when operations start and end"""
    timestamp = time.monotonic() - initial_timestamp
    timeline_events.append({
        "task": task,
        "event": event,
        "timestamp": timestamp,
    })
    logger.info(f"{timestamp:.4f}s - {task} - {event}")
    return timestamp

def timed_sync(func):
    """Decorator to time async functions with logging."""
    async def wrapper(*args, **kwargs):
        task_name = f"{func.__name__}_{kwargs.get('id', 'unknown')}"
        log_event(task_name, "START")

        start_time = time.time()
        result = await func(*args, **kwargs)  # result is (response_text, id)
        end_time = time.time()
        duration = end_time - start_time

        log_event(task_name, "END")
        logger.info(f"Function {func.__name__} took {duration:.2f} seconds.")
        return (result[0], result[1], duration)
    return wrapper

def timed(func):
    """Decorator to time sync functions with logging."""
    def wrapper(*args, **kwargs):
        task_name = f"{func.__name__}"
        log_event(task_name, "START")

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time

        log_event(task_name, "END")
        logger.info(f"Function {func.__name__} took {duration:.2f} seconds.")
        return (result, duration)  # Return tuple with result and duration
    return wrapper