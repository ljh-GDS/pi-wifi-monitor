FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY exporter.py .

# Run as non-root user
RUN useradd -m -u 1000 exporter
USER exporter

EXPOSE 9798

CMD ["python", "exporter.py"]
