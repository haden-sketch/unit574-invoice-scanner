# Gmail Mechanic Invoice Scanner - Unit 574
FROM python:3.11-slim

# Install system dependencies for PDF processing
RUN apt-get update && apt-get install -y \
    poppler-utils \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY config.py scanner.py ./

# Create directory for downloads
RUN mkdir -p /app/downloaded_invoices

# Set environment variables
ENV DOWNLOAD_DIR=/app/downloaded_invoices
ENV GMAIL_CREDENTIALS_PATH=/app/credentials.json
ENV GMAIL_TOKEN_PATH=/app/token.json

# Run scanner
CMD ["python", "scanner.py"]

