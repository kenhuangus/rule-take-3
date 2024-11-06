# agents/messaging.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Awaitable
import asyncio
import uuid
import logging
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)


@dataclass
class AgentMessage:
    sender: str
    receiver: str
    content: Dict[str, Any]
    message_type: str
    timestamp: datetime
    message_id: str = None

    def __post_init__(self):
        if self.message_id is None:
            self.message_id = str(uuid.uuid4())


class MessageQueue:
    def __init__(self):
        self._queue = asyncio.Queue()
        self._subscribers: Dict[str, Callable[[AgentMessage], Awaitable[None]]] = {}
        self._running = False
        self._lock = asyncio.Lock()

    async def start(self):
        """Start message processing without creating a background task"""
        async with self._lock:
            if self._running:
                return

            self._running = True
            logger.info("Message queue started")
            await self._process_messages()  # Await directly for sequential execution

    async def stop(self):
        """Stop message processing"""
        async with self._lock:
            if not self._running:
                return

            self._running = False

            # Clear queue
            while not self._queue.empty():
                try:
                    self._queue.get_nowait()
                    self._queue.task_done()
                except asyncio.QueueEmpty:
                    break

            logger.info("Message queue stopped")

    async def send(self, message: AgentMessage):
        """Send a message to the queue"""
        if not self._running:
            logger.warning("Attempting to send message while queue is not running")
            return

        await self._queue.put(message)
        logger.debug(f"Message queued: {message.message_type} from {message.sender}")

    def subscribe(self, receiver: str, callback: Callable[[AgentMessage], Awaitable[None]]):
        """Subscribe to messages"""
        self._subscribers[receiver] = callback
        logger.debug(f"Subscribed: {receiver}")

    def unsubscribe(self, receiver: str):
        """Unsubscribe from messages"""
        if receiver in self._subscribers:
            del self._subscribers[receiver]
            logger.debug(f"Unsubscribed: {receiver}")

    async def _process_messages(self):
        """Process messages from the queue sequentially"""
        while self._running:
            try:
                message = await self._queue.get()

                try:
                    # Get subscriber callback
                    callback = self._subscribers.get(message.receiver)
                    if callback:
                        try:
                            await callback(message)
                        except Exception as e:
                            logger.error(
                                f"Error processing message {message.message_id}: {str(e)}"
                            )
                    else:
                        logger.warning(
                            f"No subscriber found for message to {message.receiver}"
                        )

                finally:
                    self._queue.task_done()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Message processing error: {str(e)}")
                # Continue processing next message
                continue

    @property
    def is_running(self) -> bool:
        """Check if queue is running"""
        return self._running

    async def wait_until_empty(self):
        """Wait until queue is empty"""
        await self._queue.join()
