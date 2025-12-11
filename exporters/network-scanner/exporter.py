#!/usr/bin/env python3
"""
Network Scanner Prometheus Exporter
Scans local network for devices and exposes metrics for Prometheus
"""

import os
import time
import threading
import logging
import subprocess
import re
import socket
from prometheus_client import start_http_server, Gauge, Info
from mac_vendor_lookup import MacLookup

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
PORT = int(os.environ.get('EXPORTER_PORT', 9800))
INTERVAL = int(os.environ.get('SCAN_INTERVAL', 300))  # Default 5 minutes
NETWORK_RANGE = os.environ.get('NETWORK_RANGE', '192.168.1.0/24')

# Initialize MAC vendor lookup
mac_lookup = MacLookup()
try:
    mac_lookup.update_vendors()
    logger.info("MAC vendor database updated successfully")
except Exception as e:
    logger.warning(f"Could not update MAC vendor database: {e}")

# Prometheus metrics
network_devices_total = Gauge('network_devices_total', 'Total number of devices on the network')
network_scan_duration_seconds = Gauge('network_scan_duration_seconds', 'Duration of the last network scan in seconds')
network_scan_timestamp = Gauge('network_scan_timestamp', 'Timestamp of the last network scan')

# Device info metric (will have labels for each device)
network_device_info = Gauge(
    'network_device_info',
    'Information about a network device',
    ['ip', 'mac', 'hostname', 'vendor']
)

# Store discovered devices
discovered_devices = {}

def get_hostname(ip):
    """Try to resolve hostname for an IP address"""
    try:
        hostname = socket.gethostbyaddr(ip)[0]
        return hostname
    except (socket.herror, socket.gaierror):
        return "unknown"

def get_vendor(mac):
    """Look up vendor from MAC address"""
    try:
        vendor = mac_lookup.lookup(mac)
        return vendor if vendor else "Unknown"
    except Exception:
        return "Unknown"

def parse_arp_output(output):
    """Parse ARP table output to extract IP and MAC addresses"""
    devices = []
    # Pattern for Linux arp -a output: hostname (ip) at mac [ether] on interface
    # Pattern for macOS: hostname (ip) at mac on interface
    pattern = r'\((\d+\.\d+\.\d+\.\d+)\)\s+at\s+([0-9a-fA-F:]+)'

    for line in output.split('\n'):
        match = re.search(pattern, line)
        if match:
            ip = match.group(1)
            mac = match.group(2).upper()
            if mac != 'FF:FF:FF:FF:FF:FF' and mac != '00:00:00:00:00:00':
                devices.append({'ip': ip, 'mac': mac})

    return devices

def scan_with_arp():
    """Scan network using ARP"""
    devices = []

    try:
        # First, ping the broadcast address to populate ARP cache
        # This helps discover more devices
        network_base = '.'.join(NETWORK_RANGE.split('.')[:3])

        # Ping sweep (quick)
        logger.info(f"Running ping sweep on {NETWORK_RANGE}...")
        for i in range(1, 255):
            ip = f"{network_base}.{i}"
            subprocess.Popen(
                ['ping', '-c', '1', '-W', '1', ip],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )

        # Wait a bit for pings to complete
        time.sleep(3)

        # Get ARP table
        result = subprocess.run(['arp', '-a'], capture_output=True, text=True)
        devices = parse_arp_output(result.stdout)

        logger.info(f"ARP scan found {len(devices)} devices")

    except Exception as e:
        logger.error(f"ARP scan failed: {e}")

    return devices

def scan_with_nmap():
    """Scan network using nmap (more thorough but slower)"""
    devices = []

    try:
        import nmap
        nm = nmap.PortScanner()

        logger.info(f"Running nmap scan on {NETWORK_RANGE}...")
        nm.scan(hosts=NETWORK_RANGE, arguments='-sn -T4')

        for host in nm.all_hosts():
            if 'mac' in nm[host]['addresses']:
                devices.append({
                    'ip': host,
                    'mac': nm[host]['addresses']['mac'].upper()
                })
            elif nm[host].state() == 'up':
                # Local machine or device without MAC visible
                devices.append({
                    'ip': host,
                    'mac': 'LOCAL'
                })

        logger.info(f"nmap scan found {len(devices)} devices")

    except ImportError:
        logger.warning("nmap module not available, falling back to ARP only")
    except Exception as e:
        logger.error(f"nmap scan failed: {e}")

    return devices

def scan_network():
    """Scan the network for devices"""
    global discovered_devices

    logger.info(f"Starting network scan on {NETWORK_RANGE}...")
    start_time = time.time()

    # Try ARP scan first (faster)
    devices = scan_with_arp()

    # If ARP found few devices, try nmap
    if len(devices) < 3:
        nmap_devices = scan_with_nmap()
        # Merge results
        existing_ips = {d['ip'] for d in devices}
        for device in nmap_devices:
            if device['ip'] not in existing_ips:
                devices.append(device)

    # Enrich device information
    enriched_devices = {}
    for device in devices:
        ip = device['ip']
        mac = device['mac']
        hostname = get_hostname(ip)
        vendor = get_vendor(mac) if mac != 'LOCAL' else 'Local Machine'

        enriched_devices[ip] = {
            'ip': ip,
            'mac': mac,
            'hostname': hostname,
            'vendor': vendor
        }

    # Filter out Docker network interfaces
    filtered_devices = {}
    for ip, dev in enriched_devices.items():
        if ip.startswith("172.18."):
            continue
        filtered_devices[ip] = dev

    enriched_devices = filtered_devices

    # Calculate scan duration
    duration = time.time() - start_time

    # Clear old device metrics
    network_device_info._metrics.clear()

    # Update Prometheus metrics
    network_devices_total.set(len(enriched_devices))
    network_scan_duration_seconds.set(duration)
    network_scan_timestamp.set(time.time())

    # Set device info metrics
    for ip, device in enriched_devices.items():
        network_device_info.labels(
            ip=device['ip'],
            mac=device['mac'],
            hostname=device['hostname'],
            vendor=device['vendor']
        ).set(1)

    # Store for later reference
    discovered_devices = enriched_devices

    # Log summary
    logger.info(f"Network scan completed in {duration:.2f}s: {len(enriched_devices)} devices found")
    for ip, device in enriched_devices.items():
        logger.debug(f"  {ip} - {device['mac']} - {device['hostname']} ({device['vendor']})")

    return enriched_devices

def scan_loop():
    """Run network scans in a loop"""
    while True:
        try:
            scan_network()
        except Exception as e:
            logger.error(f"Network scan error: {e}")

        logger.info(f"Next scan in {INTERVAL} seconds...")
        time.sleep(INTERVAL)

def main():
    """Main entry point"""
    logger.info(f"Starting Network Scanner Exporter on port {PORT}")
    logger.info(f"Scan interval: {INTERVAL} seconds")
    logger.info(f"Network range: {NETWORK_RANGE}")

    # Start HTTP server for Prometheus
    start_http_server(PORT)
    logger.info(f"Metrics available at http://localhost:{PORT}/metrics")

    # Run initial scan
    scan_network()

    # Start scan loop in a separate thread
    scan_thread = threading.Thread(target=scan_loop, daemon=True)
    scan_thread.start()

    # Keep main thread alive
    while True:
        time.sleep(1)

if __name__ == '__main__':
    main()
