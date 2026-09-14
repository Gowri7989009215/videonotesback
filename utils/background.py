"""Lightweight background job execution engine in asyncio."""

import asyncio
from typing import Callable, Dict, Any, Optional

_handlers: Dict[str, Callable] = {}
_tasks = set()

def register_handler(name: str, fn: Callable):
    _handlers[name] = fn

async def dispatch_background(task_name: str, payload: Dict[str, Any]):
    if task_name not in _handlers:
        raise ValueError(f"No background handler registered for '{task_name}'")
    handler = _handlers[task_name]
    task = asyncio.create_task(handler(payload))
    _tasks.add(task)
    task.add_done_callback(_tasks.discard)

def shutdown():
    for task in list(_tasks):
        task.cancel()
