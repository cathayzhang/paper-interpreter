FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for WeasyPrint and PDF processing
RUN apt-get update && apt-get install -y \
    build-essential \
    libffi-dev \
    libpango1.0-0 \
    libgdk-pixbuf2.0-0 \
    libweasyprint50 \
    fonts-wqy-microhei \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-full.txt .
RUN pip install --no-cache-dir -r requirements-full.txt

# Download Playwright browsers (for PDF export fallback)
RUN playwright install chromium

# Copy application code
COPY . .

# Create output directory
RUN mkdir -p /app/paper_outputs

# Expose ports (8000 for API, 8501 for Streamlit)
EXPOSE 8000 8501

# Default command (can be overridden)
CMD ["uvicorn", "web_api:app", "--host", "0.0.0.0", "--port", "8000"]
