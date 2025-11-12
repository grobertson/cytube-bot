# Rosey Bot Monitoring

This directory contains monitoring and alerting configuration for Rosey Bot deployments.

## Components

### Prometheus (`prometheus.yml`)
Time-series database and monitoring system. Scrapes metrics from:
- Metrics exporter (port 9090)
- Bot health endpoints (ports 8000, 8001)
- Deployment dashboard (port 5000)

### Alert Rules (`alert_rules.yml`)
Defines alerting conditions:
- **RoseyBotDown**: Bot process is down
- **RoseyBotDisconnected**: Bot can't connect to CyTube
- **RoseyBotHighErrorRate**: Error rate > 5%
- **RoseyBotCriticalErrorRate**: Error rate > 10%
- **RoseyBotRestarted**: Recent restart detected
- **RoseyBotNoUsers**: No users in production channel
- **RoseyBotMetricsStale**: Metrics not updating
- **DeploymentFailed**: Deployment failure detected
- **DeploymentSlow**: Deployment taking > 5 minutes

### Alertmanager (`alertmanager.yml`)
Alert routing and notification system:
- Groups alerts by environment and severity
- Routes critical alerts immediately
- Sends notifications via webhook to dashboard
- Supports email notifications (configured but commented out)

## Installation

### Prerequisites
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-2.45.0.linux-amd64.tar.gz
sudo mv prometheus-2.45.0.linux-amd64/prometheus /usr/local/bin/
sudo mv prometheus-2.45.0.linux-amd64/promtool /usr/local/bin/

# Install Alertmanager
wget https://github.com/prometheus/alertmanager/releases/download/v0.26.0/alertmanager-0.26.0.linux-amd64.tar.gz
tar xvfz alertmanager-0.26.0.linux-amd64.tar.gz
sudo mv alertmanager-0.26.0.linux-amd64/alertmanager /usr/local/bin/
```

### Configuration
```bash
# Create Prometheus directories
sudo mkdir -p /etc/prometheus
sudo mkdir -p /var/lib/prometheus

# Copy configuration files
sudo cp monitoring/prometheus.yml /etc/prometheus/
sudo cp monitoring/alert_rules.yml /etc/prometheus/
sudo cp monitoring/alertmanager.yml /etc/prometheus/
```

### Running

#### Standalone (development)
```bash
# Start Prometheus
prometheus --config.file=monitoring/prometheus.yml \
           --storage.tsdb.path=/var/lib/prometheus

# Start Alertmanager
alertmanager --config.file=monitoring/alertmanager.yml

# Start metrics exporter
python web/metrics_exporter.py --port 9090
```

#### Systemd Services (production)
```bash
# Enable and start services
sudo systemctl enable prometheus alertmanager rosey-bot-metrics
sudo systemctl start prometheus alertmanager rosey-bot-metrics

# Check status
sudo systemctl status prometheus
sudo systemctl status alertmanager
sudo systemctl status rosey-bot-metrics
```

## Access

- **Prometheus UI**: http://localhost:9090
- **Alertmanager UI**: http://localhost:9093
- **Metrics Endpoint**: http://localhost:9090/metrics
- **Dashboard**: http://localhost:5000

## Metrics

### Bot Metrics
- `rosey_bot_up`: Bot process status (1=up, 0=down)
- `rosey_bot_connected`: CyTube connection status
- `rosey_bot_uptime_seconds`: Bot uptime in seconds
- `rosey_bot_channel_users`: Number of users in channel
- `rosey_bot_requests_total`: Total requests handled
- `rosey_bot_errors_total`: Total errors encountered
- `rosey_bot_error_rate_percent`: Current error rate

### Deployment Metrics
- `rosey_bot_deployment_duration_seconds`: Time taken for deployment
- `rosey_bot_deployment_failures_total`: Number of failed deployments
- `rosey_bot_scrape_timestamp_ms`: Last metrics scrape timestamp

## Alert Severity Levels

- **Critical**: Requires immediate attention (bot down, critical errors)
- **Warning**: Should be investigated soon (high error rate, disconnections)
- **Info**: Informational only (restarts, low user count)

## Notification Channels

Current configuration sends webhooks to the dashboard at:
- Critical: `http://localhost:5000/api/alerts/critical`
- Warning: `http://localhost:5000/api/alerts/warning`
- Info: `http://localhost:5000/api/alerts/info`

### Adding Email Notifications

Uncomment the `email_configs` section in `alertmanager.yml` and configure:
```yaml
email_configs:
  - to: 'your-email@example.com'
    from: 'rosey-bot-alerts@example.com'
    smarthost: 'smtp.gmail.com:587'
    auth_username: 'your-email@example.com'
    auth_password: 'your-app-password'
```

### Adding Slack Notifications

Add to receiver configuration:
```yaml
slack_configs:
  - api_url: 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'
    channel: '#rosey-bot-alerts'
    title: '{{ .GroupLabels.alertname }}'
    text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Testing Alerts

```bash
# Test Prometheus config
promtool check config monitoring/prometheus.yml

# Test alert rules
promtool check rules monitoring/alert_rules.yml

# Test Alertmanager config
amtool check-config monitoring/alertmanager.yml

# Trigger test alert
curl -X POST http://localhost:9093/api/v1/alerts -d '[{
  "labels": {"alertname": "TestAlert", "severity": "warning"},
  "annotations": {"summary": "Test alert"}
}]'
```

## Troubleshooting

### Metrics not appearing
1. Check metrics exporter is running: `curl http://localhost:9090/metrics`
2. Check Prometheus targets: http://localhost:9090/targets
3. Verify bot health endpoints are accessible

### Alerts not firing
1. Check alert rules in Prometheus: http://localhost:9090/alerts
2. Verify Alertmanager is receiving alerts: http://localhost:9093/#/alerts
3. Check Alertmanager logs: `journalctl -u alertmanager -f`

### Dashboard not receiving alerts
1. Check webhook endpoint: `curl http://localhost:5000/api/alerts`
2. Verify dashboard is running: `systemctl status rosey-bot-dashboard`
3. Check dashboard logs for webhook errors

## Grafana Integration (Optional)

To visualize metrics in Grafana:

```bash
# Install Grafana
sudo apt-get install -y grafana

# Start Grafana
sudo systemctl enable grafana-server
sudo systemctl start grafana-server

# Access: http://localhost:3000 (admin/admin)
```

1. Add Prometheus as data source (http://localhost:9090)
2. Import dashboard from `monitoring/grafana-dashboard.json` (to be created)
3. Configure alerts in Grafana to send to same channels

## Maintenance

### Backup Prometheus Data
```bash
# Prometheus data is stored in /var/lib/prometheus
tar czf prometheus-backup-$(date +%Y%m%d).tar.gz /var/lib/prometheus
```

### Cleanup Old Data
```bash
# Prometheus retention is configured in systemd service (default: 15 days)
# To change: edit /etc/systemd/system/prometheus.service
--storage.tsdb.retention.time=30d
```

### Update Alert Rules
```bash
# Edit rules
vim monitoring/alert_rules.yml

# Reload Prometheus config
curl -X POST http://localhost:9090/-/reload
# OR
sudo systemctl reload prometheus
```
