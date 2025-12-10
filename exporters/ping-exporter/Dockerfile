FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY exporter.py .

# Note: Running as root is required for raw socket access (ICMP ping)
# If you want to run as non-root, you need to set capabilities:
# setcap cap_net_raw+ep /usr/local/bin/python3.11

EXPOSE 9799

CMD ["python", "exporter.py"]
