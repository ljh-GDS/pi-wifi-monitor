FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for nmap and network tools
RUN apt-get update && apt-get install -y \
    nmap \
    iputils-ping \
    net-tools \
    arp-scan \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY exporter.py .

# Note: Running as root is required for network scanning
# The container needs NET_ADMIN and NET_RAW capabilities

EXPOSE 9800

CMD ["python", "exporter.py"]
