# Problem Statement

Your task is to build a Python script or lightweight app that automatically tracks and logs service updates from the [OpenAI Status Page](https://status.openai.com/).

Whenever there's a new incident, outage, or degradation update related to any OpenAI API product (e.g., Chat Completions, Responses, etc.), your program should automatically detect the update and print:

- the affected product/service, and
- the latest status message or event.

Note: You should not rely on manually refreshing the page or polling it inefficiently — the expectation is to use a more event-based approach that can scale efficiently if the same solution were used to track 100+ similar status pages from different providers.

You do not need to persist the data or build a UI — simple console output is sufficient.

# Example
```
[2025-11-03 14:32:00] Product: OpenAI API - Chat Completions
Status: Degraded performance due to upstream issue
```
