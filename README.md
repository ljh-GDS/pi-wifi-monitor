# 🌐 Pi WiFi Monitor

A comprehensive WiFi and network monitoring solution for Raspberry Pi. Monitor your home internet speed, network latency, connected devices, and receive alerts via Telegram - all visualized in a beautiful Grafana dashboard.

![Dashboard Preview](https://img.shields.io/badge/Grafana-Dashboard-orange?style=flat-square&logo=grafana)
![Docker](https://img.shields.io/badge/Docker-Compose-blue?style=flat-square&logo=docker)
![Raspberry Pi](https://img.shields.io/badge/Raspberry%20Pi-Compatible-red?style=flat-square&logo=raspberry-pi)

## ✨ Features

- **📊 Internet Speed Monitoring**
  - Download/Upload speed tests every 5 minutes
  - Ping latency tracking
  - Historical speed data visualization

- **🏓 Network Latency Monitoring**
  - Continuous ping to multiple DNS providers (Google, Cloudflare, OpenDNS)
  - Packet loss detection
  - Jitter measurement

- **📱 Network Device Scanner**
  - Discover all devices on your network
  - MAC address vendor lookup
  - Device count tracking over time
  - Works without router admin access!

- **🔔 Telegram Alerts**
  - Internet down notifications
  - Slow speed warnings
  - High latency alerts
  - New device detection
  - Packet loss warnings

- **📈 Beautiful Grafana Dashboard**
  - Real-time metrics visualization
  - Historical data analysis
  - System health monitoring

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Raspberry Pi 4                               │
├─────────────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────────┐ │
│  │  Speedtest   │  │    Ping      │  │     Network Scanner        │ │
│  │   Exporter   │  │   Exporter   │  │   (ARP + nmap)             │ │
│  │   :9798      │  │   :9799      │  │   :9800                    │ │
│  └──────┬───────┘  └──────┬───────┘  └─────────────┬──────────────┘ │
│         │                 │                        │                │
│         └─────────────────┼────────────────────────┘                │
│                           ▼                                         │
│                    ┌─────────────┐                                  │
│                    │ Prometheus  │                                  │
│                    │   :9090     │                                  │
│                    └──────┬──────┘                                  │
│                           │                                         │
│              ┌────────────┼────────────┐                            │
│              ▼                         ▼                            │
│       ┌─────────────┐          ┌─────────────┐                      │
│       │   Grafana   │◄────────►│ Alertmanager│                      │
│       │   :3000     │          │   :9093     │                      │
│       └─────────────┘          └──────┬──────┘                      │
│                                       │                             │
│                                       ▼                             │
│                              ┌─────────────────┐                    │
│                              │  Telegram Bot   │                    │
│                              └─────────────────┘                    │
└─────────────────────────────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Raspberry Pi 4** (8GB recommended, but 4GB works fine)
- **Raspberry Pi OS** (64-bit recommended) or any Debian-based Linux
- **Docker** and **Docker Compose**
- **Network connection** (WiFi or Ethernet)

## 🚀 Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ljh-GDS/pi-wifi-monitor.git
cd pi-wifi-monitor
```

### 2. Run the Setup Script

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

The setup script will:
- Check Docker installation
- Detect your network configuration
- Help you configure Telegram alerts
- Build and start all services

### 3. Access the Dashboard

Open your browser and navigate to:
- **Grafana Dashboard**: `http://<raspberry-pi-ip>:3000`
  - Default username: `admin`
  - Default password: `admin`

## 📦 Manual Installation

If you prefer manual setup:

### 1. Copy Environment File

```bash
cp .env.example .env
```

### 2. Configure Settings

Edit `.env` with your preferences:

```bash
# Network range (auto-detected by setup script)
NETWORK_RANGE=192.168.1.0/24

# Telegram Bot (for alerts)
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### 3. Configure Alertmanager

Edit `alertmanager/alertmanager.yml` and update the `chat_id`:

```yaml
telegram_configs:
  - bot_token: '${TELEGRAM_BOT_TOKEN}'
    chat_id: YOUR_CHAT_ID_HERE  # Replace with your actual chat ID
```

### 4. Build and Start

```bash
docker compose build
docker compose up -d
```

## 🔔 Setting Up Telegram Alerts

### Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token (looks like `123456789:ABCdefGHIjklMNOpqrsTUVwxyz`)

### Get Your Chat ID

1. Search for `@userinfobot` or `@get_id_bot` on Telegram
2. Start the bot and it will show your chat ID
3. Copy the chat ID (a number like `123456789`)

### Configure the Bot

1. Add your bot token to `.env`:
   ```
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   ```

2. Update `alertmanager/alertmanager.yml` with your chat ID:
   ```yaml
   chat_id: YOUR_CHAT_ID
   ```

3. Restart Alertmanager:
   ```bash
   docker compose restart alertmanager
   ```

## 📊 Dashboard Panels

The Grafana dashboard includes:

| Section | Metrics |
|---------|---------|
| **Internet Speed** | Download/Upload speeds, Ping, Connection status |
| **Speed History** | Historical speed graph with averages |
| **Network Latency** | Average latency, Packet loss, Jitter |
| **Latency by Target** | Per-target latency graphs |
| **Network Devices** | Device count, Device list with vendor info |
| **System Health** | Exporter status, Last test duration |

## ⚙️ Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SPEEDTEST_INTERVAL` | `300` | Seconds between speed tests |
| `PING_INTERVAL` | `10` | Seconds between ping cycles |
| `PING_TARGETS` | `8.8.8.8,1.1.1.1,208.67.222.222` | Comma-separated ping targets |
| `SCAN_INTERVAL` | `300` | Seconds between network scans |
| `NETWORK_RANGE` | `192.168.1.0/24` | Network CIDR to scan |
| `GRAFANA_ADMIN_USER` | `admin` | Grafana admin username |
| `GRAFANA_ADMIN_PASSWORD` | `admin` | Grafana admin password |

### Alert Thresholds

Default alert thresholds (configurable in `prometheus/alert_rules.yml`):

| Alert | Threshold |
|-------|-----------|
| Slow Download | < 50 Mbps |
| Slow Upload | < 10 Mbps |
| High Latency | > 100 ms |
| Packet Loss | > 5% |
| Critical Packet Loss | > 20% |
| Unusual Device Count | > 20 devices |

## 🔧 Useful Commands

```bash
# View all logs
docker compose logs -f

# View specific service logs
docker compose logs -f speedtest-exporter
docker compose logs -f network-scanner

# Restart all services
docker compose restart

# Stop all services
docker compose down

# Rebuild after changes
docker compose build
docker compose up -d

# Check service status
docker compose ps

# Run a manual speed test (view logs)
docker compose logs -f speedtest-exporter

# Check Prometheus targets
# Visit http://<pi-ip>:9090/targets
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# Check Docker daemon
sudo systemctl status docker

# View detailed logs
docker compose logs --tail=50
```

### Network Scanner Not Finding Devices

- Ensure `NETWORK_RANGE` matches your network
- The scanner needs to run on the host network
- Check if ARP/nmap have proper permissions

```bash
# Test network range manually
docker compose exec network-scanner ping -c 1 192.168.1.1
```

### Telegram Alerts Not Working

1. Verify bot token and chat ID in `.env`
2. Make sure you've started a conversation with your bot
3. Check Alertmanager logs:
   ```bash
   docker compose logs alertmanager
   ```

### High Resource Usage

If the Pi is running slow:
- Increase `SPEEDTEST_INTERVAL` to reduce bandwidth usage
- Increase `SCAN_INTERVAL` to reduce CPU usage

## 📁 Project Structure

```
pi-wifi-monitor/
├── docker-compose.yml          # Docker services configuration
├── .env.example                # Environment variables template
├── README.md                   # This file
├── prometheus/
│   ├── prometheus.yml          # Prometheus configuration
│   └── alert_rules.yml         # Alert rules
├── alertmanager/
│   └── alertmanager.yml        # Alertmanager + Telegram config
├── grafana/
│   └── provisioning/
│       ├── dashboards/
│       │   ├── dashboard.yml   # Dashboard provider config
│       │   └── wifi-monitor.json  # Main dashboard
│       └── datasources/
│           └── prometheus.yml  # Prometheus datasource
├── exporters/
│   ├── speedtest-exporter/     # Internet speed monitoring
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── exporter.py
│   ├── ping-exporter/          # Latency monitoring
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── exporter.py
│   └── network-scanner/        # Device discovery
│       ├── Dockerfile
│       ├── requirements.txt
│       └── exporter.py
└── scripts/
    └── setup.sh                # Interactive setup script
```

## 🔮 Future Enhancements

- [ ] WiFi signal strength monitoring (requires additional setup)
- [ ] Bandwidth usage per device
- [ ] Historical device tracking (first seen, last seen)
- [ ] Web-based configuration UI
- [ ] Mobile app integration
- [ ] Multiple network support

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

## 🙏 Acknowledgments

- [Prometheus](https://prometheus.io/) - Monitoring system
- [Grafana](https://grafana.com/) - Visualization platform
- [speedtest-cli](https://github.com/sivel/speedtest-cli) - Speed testing
- [python-nmap](https://github.com/savon-noir/python-nmap) - Network scanning
