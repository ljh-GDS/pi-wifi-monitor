#!/usr/bin/env python3
"""
Ping Prometheus Exporter
Continuously monitors latency and packet loss to multiple targets
"""

import os
import time
import threading
import logging
import statistics
from prometheus_client import start_http_server, Gauge
from pythonping import ping

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.environ.get('EXPORTER_PORT', 9799))
INTERVAL = int(os.environ.get('PING_INTERVAL', 10))  # Default 10 seconds
PING_COUNT = int(os.environ.get('PING_COUNT', 5))  # Number of pings per target
PING_TIMEOUT = int(os.environ.get('PING_TIMEOUT', 2))  # Timeout in seconds

# Parse targets from environment variable
TARGETS_ENV = os.environ.get('PING_TARGETS', '8.8.8.8,1.1.1.1,208.67.222.222')
TARGETS = [t.strip() for t in TARGETS_ENV.split(',') if t.strip()]

# Target names for better labeling
TARGET_NAMES = {
    '8.8.8.8': 'Google DNS',
    '1.1.1.1': 'Cloudflare DNS',
    '208.67.222.222': 'OpenDNS',
    '9.9.9.9': 'Quad9 DNS',
    '8.8.4.4': 'Google DNS Secondary',
}

# Prometheus metrics
ping_latency_ms = Gauge('ping_latency_ms', 'Ping latency in milliseconds', ['target', 'target_name'])
ping_packet_loss_percent = Gauge('ping_packet_loss_percent', 'Packet loss percentage', ['target', 'target_name'])
ping_jitter_ms = Gauge('ping_jitter_ms', 'Ping jitter (latency variation) in milliseconds', ['target', 'target_name'])
ping_min_latency_ms = Gauge('ping_min_latency_ms', 'Minimum ping latency in milliseconds', ['target', 'target_name'])
ping_max_latency_ms = Gauge('ping_max_latency_ms', 'Maximum ping latency in milliseconds', ['target', 'target_name'])
ping_success = Gauge('ping_success', 'Ping success status (1=reachable, 0=unreachable)', ['target', 'target_name'])

def ping_target(target):
    """Ping a single target and return metrics"""
    target_name = TARGET_NAMES.get(target, target)

    try:
        response = ping(target, count=PING_COUNT, timeout=PING_TIMEOUT)

        # Calculate metrics
        rtts = [r.time_elapsed_ms for r in response if r.success]

        if rtts:
            avg_latency = statistics.mean(rtts)
            min_latency = min(rtts)
            max_latency = max(rtts)
            jitter = statistics.stdev(rtts) if len(rtts) > 1 else 0
            packet_loss = ((PING_COUNT - len(rtts)) / PING_COUNT) * 100
            success = 1
        else:
            avg_latency = 0
            min_latency = 0
            max_latency = 0
            jitter = 0
            packet_loss = 100
            success = 0

        # Update Prometheus metrics
        ping_latency_ms.labels(target=target, target_name=target_name).set(avg_latency)
        ping_min_latency_ms.labels(target=target, target_name=target_name).set(min_latency)
        ping_max_latency_ms.labels(target=target, target_name=target_name).set(max_latency)
        ping_jitter_ms.labels(target=target, target_name=target_name).set(jitter)
        ping_packet_loss_percent.labels(target=target, target_name=target_name).set(packet_loss)
        ping_success.labels(target=target, target_name=target_name).set(success)

        if success:
            logger.debug(f"Ping {target} ({target_name}): {avg_latency:.2f}ms, loss: {packet_loss:.1f}%")
        else:
            logger.warning(f"Ping {target} ({target_name}): UNREACHABLE")

        return {
            'target': target,
            'target_name': target_name,
            'latency': avg_latency,
            'packet_loss': packet_loss,
            'success': success
        }

    except Exception as e:
        logger.error(f"Error pinging {target}: {e}")
        ping_latency_ms.labels(target=target, target_name=target_name).set(0)
        ping_min_latency_ms.labels(target=target, target_name=target_name).set(0)
        ping_max_latency_ms.labels(target=target, target_name=target_name).set(0)
        ping_jitter_ms.labels(target=target, target_name=target_name).set(0)
        ping_packet_loss_percent.labels(target=target, target_name=target_name).set(100)
        ping_success.labels(target=target, target_name=target_name).set(0)
        return None

def ping_all_targets():
    """Ping all configured targets"""
    results = []
    for target in TARGETS:
        result = ping_target(target)
        if result:
            results.append(result)
    return results

def ping_loop():
    """Continuously ping targets in a loop"""
    while True:
        results = ping_all_targets()

        # Log summary
        successful = sum(1 for r in results if r and r['success'])
        logger.info(f"Ping cycle complete: {successful}/{len(TARGETS)} targets reachable")

        time.sleep(INTERVAL)

def main():
    """Main entry point"""
    logger.info(f"Starting Ping Exporter on port {PORT}")
    logger.info(f"Ping interval: {INTERVAL} seconds")
    logger.info(f"Targets: {', '.join(TARGETS)}")

    # Start HTTP server for Prometheus
    start_http_server(PORT)
    logger.info(f"Metrics available at http://localhost:{PORT}/metrics")

    # Run initial ping
    ping_all_targets()

    # Start ping loop in a separate thread
    ping_thread = threading.Thread(target=ping_loop, daemon=True)
    ping_thread.start()

    # Keep main thread alive
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
