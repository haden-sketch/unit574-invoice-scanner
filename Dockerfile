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

# Create directory for downloads and credentials
RUN mkdir -p /var/invoices/unit_574 /app/credentials

# Set environment variables
ENV DOWNLOAD_DIR=/var/invoices/unit_574
ENV GMAIL_CREDENTIALS_PATH=/app/credentials/credentials.json
ENV GMAIL_TOKEN_PATH=/app/credentials/token.json

# Volume for persistent storage
VOLUME ["/var/invoices/unit_574", "/app/credentials"]

# Run scanner
CMD ["python", "scanner.py"]

