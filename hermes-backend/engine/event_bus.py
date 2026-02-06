from typing import Callable, List, Dict, Type
from collections import defaultdict
from .events import Event
import queue

class EventBus:
    """
    Simple Event Bus (Publisher/Subscriber).
    """
    def __init__(self):
        self._listeners: Dict[Type[Event], List[Callable[[Event], None]]] = defaultdict(list)
        self._queue = queue.Queue()

    def subscribe(self, event_type: Type[Event], listener: Callable[[Event], None]):
        """Subscribe a listener to a specific event type."""
        self._listeners[event_type].append(listener)

    def publish(self, event: Event):
        """Push event to queue."""
        self._queue.put(event)

    def process_next(self):
        """Process the next event in the queue."""
        if self._queue.empty():
            return False
            
        event = self._queue.get()
        event_type = type(event)
        
        if event_type in self._listeners:
            for listener in self._listeners[event_type]:
                listener(event)
        
        return True

    def process_all(self):
        """Process all events currently in queue."""
        while not self._queue.empty():
            self.process_next()
