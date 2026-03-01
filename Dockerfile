FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for WeasyPrint
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libgdk-pixbuf-2.0-0 \
    libcairo2 \
    libxml2 \
    fonts-dejavu-core \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python dependencies (lightweight for Render)
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/paper_outputs

# Expose port
EXPOSE 8000

# Start the API server
CMD ["uvicorn", "web_api:app", "--host", "0.0.0.0", "--port", "8000"]
