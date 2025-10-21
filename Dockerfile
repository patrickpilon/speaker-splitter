# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (ffmpeg required by pydub, git and build tools for WhisperX)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY speaker_splitter.py .
COPY web_app.py .
COPY templates/ templates/

# Create directories for uploads and outputs
RUN mkdir -p /tmp/uploads /tmp/outputs

# Expose port for web UI
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=web_app.py
ENV PYTHONUNBUFFERED=1

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health')" || exit 1

# Run the web application
CMD ["python", "web_app.py"]
