import asyncio
import aiohttp
from aiohttp import web
import feedparser
import yaml
import logging
import os
import time
import calendar
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("DowntimeReporter")

# --- modular architecture ---


class ServiceMonitor(ABC):
    """Abstract base class for a service monitor."""

    def __init__(self, name: str, config: Dict):
        self.name = name
        self.config = config

    @abstractmethod
    def setup(self, app: web.Application):
        """Initializes the monitor (starts tasks or adds routes)."""
        pass


class RSSMonitor(ServiceMonitor):
    """Monitor for RSS-based status pages."""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.url = config["url"]
        # Default to 60 if not in config, can be overridden by global settings later
        self.poll_interval = config.get("poll_interval", 60)
        self.last_etag = None
        self.last_modified = None
        self.latest_entry_date = datetime.now().timestamp()

    def setup(self, app: web.Application):
        # Start polling when the app starts
        app.on_startup.append(self.start_polling)

    async def start_polling(self, app: web.Application):
        asyncio.create_task(self.poll_loop())

    async def poll_loop(self):
        async with aiohttp.ClientSession() as session:
            while True:
                await self.check_status(session)
                await asyncio.sleep(self.poll_interval)

    async def check_status(self, session: aiohttp.ClientSession):
        headers = {}
        if self.last_etag:
            headers["If-None-Match"] = self.last_etag
        if self.last_modified:
            headers["If-Modified-Since"] = self.last_modified

        try:
            async with session.get(self.url, headers=headers) as response:
                if response.status == 304:
                    logger.debug(f"[{self.name}] No changes (304 Not Modified)")
                    return

                if response.status == 200:
                    self.last_etag = response.headers.get("ETag")
                    self.last_modified = response.headers.get("Last-Modified")

                    content = await response.text()
                    feed = feedparser.parse(content)

                    if not feed.entries:
                        return

                    sorted_entries = sorted(
                        feed.entries,
                        key=lambda x: (
                            x.published_parsed if hasattr(x, "published_parsed") else 0
                        ),
                    )

                    new_entries = []
                    for entry in sorted_entries:
                        published_struct = entry.get("published_parsed")
                        if published_struct:
                            published_ts = calendar.timegm(published_struct)
                            if published_ts > self.latest_entry_date:
                                new_entries.append(entry)
                                self.latest_entry_date = published_ts

                    for entry in new_entries:
                        print(
                            f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Product: {self.name} (RSS)",
                            flush=True,
                        )
                        print(f"Update: {entry.title}", flush=True)
                        print(f"Details: {entry.description[:200]}...", flush=True)
                        print("-" * 40, flush=True)
                else:
                    logger.warning(
                        f"[{self.name}] Failed to fetch status: {response.status}"
                    )

        except Exception as e:
            logger.error(f"[{self.name}] Error checking status: {e}")


class WebhookMonitor(ServiceMonitor):
    """Monitor for Webhook-based status updates."""

    def __init__(self, name: str, config: Dict):
        super().__init__(name, config)
        self.route = config["route"]

    def setup(self, app: web.Application):
        logger.info(f"[{self.name}] Registering webhook route: {self.route}")
        app.router.add_post(self.route, self.handle_webhook)

    async def handle_webhook(self, request):
        try:
            data = await request.json()
            # Try to extract title/desc from common webhook formats
            title = (
                data.get("incident", {}).get("name")
                or data.get("page", {}).get("status_description")
                or "Status Update"
            )

            desc = "No details provided."
            if "incident" in data and "incident_updates" in data["incident"]:
                updates = data["incident"]["incident_updates"]
                if updates:
                    desc = updates[0].get("body", desc)

            print(
                f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Product: {self.name} (Webhook)",
                flush=True,
            )
            print(f"Update: {title}", flush=True)
            print(f"Details: {desc[:200]}...", flush=True)
            print("-" * 40, flush=True)

            return web.Response(text="Received")
        except Exception as e:
            logger.error(f"[{self.name}] Webhook error: {e}")
            return web.Response(status=500)


class StatusTracker:
    """Orchestrates the monitoring of multiple services (RSS & Webhook)."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.monitors: List[ServiceMonitor] = []
        self.app = web.Application()

    def load_config(self):
        try:
            with open(self.config_path, "r") as f:
                config = yaml.safe_load(f)

            global_poll = config.get("settings", {}).get("poll_interval", 60)

            for service_conf in config.get("services", []):
                # Inject global poll interval if not set locally
                if "poll_interval" not in service_conf:
                    service_conf["poll_interval"] = global_poll

                if service_conf["type"] == "rss":
                    self.monitors.append(RSSMonitor(service_conf["name"], service_conf))
                elif service_conf["type"] == "webhook":
                    self.monitors.append(
                        WebhookMonitor(service_conf["name"], service_conf)
                    )

            logger.info(f"Loaded {len(self.monitors)} services from config.")

        except Exception as e:
            logger.error(f"Failed to load config: {e}")

    def run(self):
        logger.info("Starting Downtime Reporter (Hybrid Mode)...")
        self.load_config()

        # Setup all monitors BEFORE starting app
        for monitor in self.monitors:
            monitor.setup(self.app)

        port = int(os.environ.get("PORT", 3000))
        logger.info(f"Listening on port {port}")
        web.run_app(self.app, port=port)


if __name__ == "__main__":
    tracker = StatusTracker()
    tracker.run()
