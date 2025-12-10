#!/usr/bin/env python3
"""
Speedtest Prometheus Exporter
Runs periodic speed tests and exposes metrics for Prometheus
"""

import os
import time
import threading
import logging
from prometheus_client import start_http_server, Gauge, Info
import speedtest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.environ.get('EXPORTER_PORT', 9798))
INTERVAL = int(os.environ.get('SPEEDTEST_INTERVAL', 300))  # Default 5 minutes

# Prometheus metrics
speedtest_up = Gauge('speedtest_up', 'Speedtest success status (1=success, 0=failure)')
speedtest_download_mbps = Gauge('speedtest_download_mbps', 'Download speed in Mbps')
speedtest_upload_mbps = Gauge('speedtest_upload_mbps', 'Upload speed in Mbps')
speedtest_ping_ms = Gauge('speedtest_ping_ms', 'Ping latency in milliseconds')
speedtest_jitter_ms = Gauge('speedtest_jitter_ms', 'Jitter in milliseconds')
speedtest_bytes_received = Gauge('speedtest_bytes_received', 'Total bytes received during test')
speedtest_bytes_sent = Gauge('speedtest_bytes_sent', 'Total bytes sent during test')
speedtest_last_run_timestamp = Gauge('speedtest_last_run_timestamp', 'Timestamp of last speedtest run')
speedtest_last_run_duration_seconds = Gauge('speedtest_last_run_duration_seconds', 'Duration of last speedtest in seconds')

# Server info
speedtest_server_info = Info('speedtest_server', 'Information about the speedtest server used')


def run_speedtest():
    """Run a speed test and update Prometheus metrics"""
    logger.info("Starting speed test...")
    start_time = time.time()

    try:
        st = speedtest.Speedtest()
        st.get_best_server()

        # Run download test
        logger.info("Testing download speed...")
        download_speed = st.download()

        # Run upload test
        logger.info("Testing upload speed...")
        upload_speed = st.upload()

        # Get results
        results = st.results.dict()

        # Calculate duration
        duration = time.time() - start_time

        # Update metrics
        speedtest_up.set(1)
        speedtest_download_mbps.set(download_speed / 1_000_000)  # Convert to Mbps
        speedtest_upload_mbps.set(upload_speed / 1_000_000)  # Convert to Mbps
        speedtest_ping_ms.set(results['ping'])
        speedtest_bytes_received.set(results.get('bytes_received', 0))
        speedtest_bytes_sent.set(results.get('bytes_sent', 0))
        speedtest_last_run_timestamp.set(time.time())
        speedtest_last_run_duration_seconds.set(duration)

        # Server info
        server = results.get('server', {})
        speedtest_server_info.info({
            'name': server.get('name', 'unknown'),
            'country': server.get('country', 'unknown'),
            'sponsor': server.get('sponsor', 'unknown'),
            'host': server.get('host', 'unknown'),
        })

        logger.info(
            f"Speed test completed: "
            f"Download: {download_speed/1_000_000:.2f} Mbps, "
            f"Upload: {upload_speed/1_000_000:.2f} Mbps, "
            f"Ping: {results['ping']:.2f} ms"
        )

    except Exception as e:
        logger.error(f"Speed test failed: {e}")
        speedtest_up.set(0)
        speedtest_last_run_timestamp.set(time.time())
        speedtest_last_run_duration_seconds.set(time.time() - start_time)


def speedtest_loop():
    """Run speed tests in a loop"""
    while True:
        run_speedtest()
        logger.info(f"Next speed test in {INTERVAL} seconds...")
        time.sleep(INTERVAL)


def main():
    """Main entry point"""
    logger.info(f"Starting Speedtest Exporter on port {PORT}")
    logger.info(f"Speed test interval: {INTERVAL} seconds")

    # Start HTTP server for Prometheus
    start_http_server(PORT)
    logger.info(f"Metrics available at http://localhost:{PORT}/metrics")

    # Run initial speedtest
    run_speedtest()

    # Start speedtest loop in a separate thread
    speedtest_thread = threading.Thread(target=speedtest_loop, daemon=True)
    speedtest_thread.start()

    # Keep main thread alive
    while True:
        time.sleep(1)


if __name__ == '__main__':
    main()
