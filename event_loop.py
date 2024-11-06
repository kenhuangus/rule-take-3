# event_loop.py
import asyncio
import logging
from typing import Any
import traceback
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)
DEBUG = False


def debug_log(msg: str, data: Any = None):
    if DEBUG:
        call_frame = traceback.extract_stack()[-2]
        calling_func = call_frame.name
        if data:
            logger.debug(f"[{calling_func}] {msg} | Data: {data}")
        else:
            logger.debug(f"[{calling_func}] {msg}")


def run_async(coroutine):
    """Run async code in Streamlit with proper event loop handling"""
    debug_log("Running async coroutine")
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        return loop.run_until_complete(
            asyncio.wait_for(coroutine, timeout=60)
        )
    except asyncio.TimeoutError:
        debug_log("Operation timed out")
        raise TimeoutError("Operation timed out after 60 seconds")
    except Exception as e:
        debug_log(f"Async execution failed: {str(e)}")
        raise
    finally:
        try:
            pending = asyncio.all_tasks(loop)
            for task in pending:
                task.cancel()

            if pending:
                loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))

            loop.close()
        except Exception as e:
            debug_log(f"Error during cleanup: {str(e)}")


def cleanup():
    """Clean up system resources safely"""
    debug_log("Performing system cleanup")
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        if not loop.is_closed():
            pending = [task for task in asyncio.all_tasks(loop) if not task.done()]
            if pending:
                async def cancel_tasks():
                    for task in pending:
                        task.cancel()
                    await asyncio.sleep(0.1)

                try:
                    loop.run_until_complete(asyncio.wait_for(cancel_tasks(), timeout=1.0))
                except Exception:
                    pass
                finally:
                    if not loop.is_closed():
                        loop.close()
    except Exception as e:
        debug_log(f"Cleanup error: {str(e)}")


async def init_event_loop():
    """Initialize the event loop"""
    try:
        if asyncio.get_event_loop().is_closed():
            asyncio.set_event_loop(asyncio.new_event_loop())
    except Exception as e:
        debug_log(f"Error initializing event loop: {str(e)}")
        raise