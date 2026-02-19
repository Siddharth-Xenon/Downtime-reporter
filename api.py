import asyncio
import logging
from collections import deque
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
import uvicorn
import os

# Import the existing monitor logic
from monitor import StatusTracker


# --- Custom Logger ---
class BufferHandler(logging.Handler):
    """
    Custom logging handler that stores the last N logs in a memory buffer.
    """

    def __init__(self, capacity=100):
        super().__init__()
        self.buffer = deque(maxlen=capacity)

    def emit(self, record):
        try:
            msg = self.format(record)
            self.buffer.append(msg)
        except Exception:
            self.handleError(record)


# Create the buffer handler
log_buffer = BufferHandler(capacity=200)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
)
log_buffer.setFormatter(formatter)

# Attach to the root logger so we capture everything
logging.getLogger().addHandler(log_buffer)

# --- FastAPI App ---
app = FastAPI()

# Initialize the tracker (which loads config)
tracker = StatusTracker()


@app.on_event("startup")
async def startup_event():
    """
    Start the background monitoring tasks when FastAPI starts.
    """
    tracker.load_config()
    # Setup monitors with the internal app if needed,
    # but primarily we just want to run their loops

    print("Starting background monitoring loops...", flush=True)

    # We need to manually start the loops for RSS monitors
    # valid monitors have a 'poll_loop' method or similar logic
    for monitor in tracker.monitors:
        # In monitor.py, RSSMonitor has a `poll_loop`
        if hasattr(monitor, "poll_loop"):
            asyncio.create_task(monitor.poll_loop())

        # Webhooks are tricky because in monitor.py they expect aiohttp routes.
        # Since we are using FastAPI now, we should register them here if we want them to work.
        if hasattr(monitor, "route") and hasattr(monitor, "handle_webhook"):
            # Register webhook route dynamically
            # We wrap the handle_webhook to adapt aiohttp request to FastAPI request if needed
            # But monitor.py code uses `await request.json()` which is compatible-ish
            # if we pass a FastAPI Request object that has a similar interface.

            # Simple adapter for webhooks
            from fastapi import Request

            async def webhook_adapter(request: Request, m=monitor):
                try:
                    # Create a dummy object or just pass request if it's compatible
                    # aiohttp request.json() is a coroutine, FastAPI request.json() is also a coroutine
                    await m.handle_webhook(request)
                    return {"status": "received"}
                except Exception as e:
                    logging.error(f"Webhook error: {e}")
                    return {"status": "error"}

            app.add_api_route(monitor.route, webhook_adapter, methods=["POST"])


@app.get("/", response_class=PlainTextResponse)
async def get_logs():
    """
    Return the buffered logs as plain text.
    Similar to viewing a log file in terminal.
    """
    return "\n".join(log_buffer.buffer)


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
