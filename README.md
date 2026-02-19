# Modular Downtime Reporter

A robust, modular Python tool for tracking service status updates via **RSS feeds** (e.g., OpenAI, GitHub) and **Webhooks** (e.g., Anthropic, PagerDuty).

It features a **Hybrid Architecture** that runs a web server for incoming webhooks while simultaneously polling RSS feeds in the background.

## 🚀 Features

-   **Hybrid Monitoring**: Supports both **Push** (Webhooks) and **Pull** (RSS) models in a single process.
-   **Efficient Polling**: Uses `If-Modified-Since` and `ETag` headers to minimize bandwidth.
-   **Scalable**: Built on `asyncio` and `aiohttp` to monitor 100+ services efficiently.
-   **Extensible**: Modular `ServiceMonitor` class makes it easy to add new integration types.
-   **Local Simulator**: Includes a `simulator.py` to test outages without waiting for real downtime.

## 🛠️ Installation

1.  **Clone the repository** (or download the files).
2.  **Set up a Virtual Environment**:
    ```powershell
    # Windows
    python -m venv venv
    .\venv\Scripts\Activate.ps1
    ```
    ```bash
    # Mac/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## ⚙️ Configuration

Define your services in `config.yaml`:

```yaml
services:
  - name: OpenAI
    type: rss
    url: https://status.openai.com/feed.rss

  - name: Anthropic
    type: webhook
    route: /webhook/anthropic  # Local route to listen on

settings:
  poll_interval: 60  # Seconds between RSS checks
```

## 🏃 Usage

### 1. Start the Monitor
```bash
python monitor.py
```
This starts the application on **Port 3000**.
-   It will begin polling RSS feeds immediately.
-   It will listen for POST requests on configured webhook routes.

### 2. Exposing Webhooks (ngrok)
To receive webhooks from external providers (like Anthropic), expose your local server:

1.  Run **ngrok**: `ngrok http 3000`
2.  Copy the HTTPS URL (e.g., `https://xyz.ngrok-free.app`).
3.  Configure the provider to send webhooks to: `https://xyz.ngrok-free.app/webhook/anthropic`

### 3. Testing Locally
You can test without real outages using the included simulator.

**Terminal 1 (Simulator - Port 8080):**
```bash
python simulator.py
```

**Terminal 2 (Trigger RSS Outage):**
```bash
curl -X POST http://localhost:8080/trigger/down
```

**Terminal 3 (Simulate Webhook):**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"incident": {"name": "Test Alert"}}' \
     http://localhost:3000/webhook/anthropic
```

## 📂 Project Structure

-   `monitor.py`: Main application (StatusTracker, RSSMonitor, WebhookMonitor).
-   `config.yaml`: Configuration file.
-   `simulator.py`: Testing tool for RSS feeds.
-   `requirements.txt`: Python dependencies.
