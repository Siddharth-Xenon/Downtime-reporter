import asyncio
from aiohttp import web
import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("Simulator")

# State
current_status = "operational"
incidents = []

def generate_feed():
    """Generates a minimal RSS 2.0 feed based on current incidents."""
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    
    items_xml = ""
    for incident in reversed(incidents):
        items_xml += f"""
        <item>
            <title>{incident['title']}</title>
            <description>{incident['description']}</description>
            <pubDate>{incident['pubDate']}</pubDate>
            <guid>{incident['guid']}</guid>
            <link>http://localhost:8080/incident/{incident['guid']}</link>
        </item>
        """

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
    <channel>
        <title>Simulated Status Page</title>
        <link>http://localhost:8080/</link>
        <description>Status updates for Simulator</description>
        <lastBuildDate>{now}</lastBuildDate>
        {items_xml}
    </channel>
</rss>
"""

async def handle_feed(request):
    """Serves the RSS feed."""
    logger.info("Serving RSS feed")
    return web.Response(text=generate_feed(), content_type='application/xml')

async def handle_trigger_down(request):
    """Triggers a simulated outage."""
    global current_status
    current_status = "major_outage"
    
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    incident_id = int(datetime.datetime.now().timestamp())
    
    incidents.append({
        "title": "Major Service Outage",
        "description": "We are currently investigating a major outage impacting all services.",
        "pubDate": now,
        "guid": f"incident_{incident_id}"
    })
    
    logger.info("Triggered DOWN incident")
    return web.Response(text="Simulated Outage Triggered")

async def handle_trigger_up(request):
    """Resolves the outage."""
    global current_status
    current_status = "operational"
    
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")
    incident_id = int(datetime.datetime.now().timestamp())

    incidents.append({
        "title": "All Systems Operational",
        "description": "The incident has been resolved.",
        "pubDate": now,
        "guid": f"resolved_{incident_id}"
    })
    
    logger.info("Triggered UP (Resolution)")
    return web.Response(text="Simulated Resolution Triggered")

app = web.Application()
app.add_routes([
    web.get('/feed.xml', handle_feed),
    web.post('/trigger/down', handle_trigger_down),
    web.post('/trigger/up', handle_trigger_up)
])

if __name__ == '__main__':
    web.run_app(app, port=8080)
