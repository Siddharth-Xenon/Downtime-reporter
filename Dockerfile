FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Cloud Run expects the app to listen on the PORT environment variable
# monitor.py is already configured to read os.environ.get('PORT')
CMD ["python", "monitor.py"]
