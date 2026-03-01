FROM python:3.10-slim

WORKDIR /app

# Install minimal system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/paper_outputs

# Expose port (Render uses $PORT environment variable)
EXPOSE 8000

# Health check disabled (Render has its own health check)
# HEALTHCHECK not needed as Render uses healthCheckPath in render.yaml

# Run with uvicorn
# Note: Render will override this with startCommand from render.yaml
CMD ["sh", "-c", "uvicorn web_api:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
