# faneX-ID OnPrem Connector

A lightweight connector that bridges on-premises infrastructure with the faneX-ID SaaS platform.

## Overview

The OnPrem Connector enables organizations to connect their on-premises Active Directory, LDAP, and other local systems to faneX-ID's cloud platform while keeping sensitive data on-premises. The connector acts as a secure proxy, forwarding only necessary information to the cloud platform.

## Features

- 🔐 **Secure Token Authentication**: Uses RBAC-managed API tokens for authentication
- 🌐 **Dual Network Support**: Works over private networks and the internet
- 🔄 **Automatic Failover**: Supports primary and backup connector configurations
- 📊 **Health Monitoring**: Built-in health checks and status reporting
- 🛡️ **Encrypted Communication**: All data transmitted over HTTPS/TLS
- 🔌 **FastAPI Integration**: RESTful API compatible with faneX-ID backend
- 🐧 **Cross-Platform**: Supports Windows and Linux

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  OnPrem AD/LDAP │ ◄─────► │  OnPrem Connector │ ◄─────► │  faneX-ID Cloud │
│   (Local)       │         │   (This Service)  │         │   (SaaS)        │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## Installation

### Windows

1. Download the latest Windows release
2. Extract to `C:\Program Files\faneX-ID-Connector\`
3. Run `install.bat` as Administrator
4. Configure `config.ini`
5. Start the service: `net start fanexid-connector`

### Linux

```bash
# Download and extract
wget https://github.com/faneX-ID/onprem-connector/releases/latest/download/connector-linux.tar.gz
tar -xzf connector-linux.tar.gz
cd fanexid-connector

# Install dependencies
pip install -r requirements.txt

# Install as systemd service
sudo ./install.sh

# Configure
sudo nano /etc/fanexid-connector/config.ini

# Start service
sudo systemctl start fanexid-connector
sudo systemctl enable fanexid-connector
```

## Configuration

### Basic Configuration (`config.ini`)

```ini
[connector]
name = MyCompany-Connector
role = primary  # or "backup"
version = 1.0.0

[cloud]
api_url = https://fanexid.example.com/api
api_token = your_secure_token_here
verify_ssl = true
timeout = 30

[network]
listen_host = 0.0.0.0
listen_port = 8080
allowed_ips = 10.0.0.0/8,192.168.0.0/16

[security]
token_refresh_interval = 3600
max_retries = 3
retry_delay = 5

[logging]
level = INFO
file = logs/connector.log
max_size = 10MB
backup_count = 5
```

### Network Modes

#### Private Network Mode

For connections within a private network (VPN, direct connection):

```ini
[network]
mode = private
api_url = http://10.0.1.100:8000/api  # Internal IP
verify_ssl = false  # Optional for private networks
```

#### Internet Mode

For connections over the public internet:

```ini
[network]
mode = internet
api_url = https://fanexid.example.com/api
verify_ssl = true
cert_file = /path/to/ca-cert.pem  # Optional custom CA
```

## API Token Setup

1. Log into your faneX-ID instance as an administrator
2. Navigate to **Admin → API Tokens**
3. Click **Create New Token**
4. Configure token permissions (RBAC-based)
5. Copy the generated token
6. Add token to `config.ini`:

```ini
[cloud]
api_token = fanexid_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

## Usage

### Start Connector

**Windows:**
```cmd
net start fanexid-connector
```

**Linux:**
```bash
sudo systemctl start fanexid-connector
```

### Check Status

**Windows:**
```cmd
fanexid-connector status
```

**Linux:**
```bash
sudo systemctl status fanexid-connector
```

### View Logs

**Windows:**
```cmd
type "C:\Program Files\faneX-ID-Connector\logs\connector.log"
```

**Linux:**
```bash
sudo journalctl -u fanexid-connector -f
```

## API Endpoints

The connector exposes a local FastAPI server for monitoring and management:

- `GET /health` - Health check endpoint
- `GET /status` - Detailed connector status
- `GET /metrics` - Prometheus-compatible metrics
- `POST /reload` - Reload configuration (requires auth)

## Primary/Backup Configuration

Configure multiple connectors for high availability:

### Primary Connector

```ini
[connector]
name = Primary-Connector
role = primary
priority = 1
```

### Backup Connector

```ini
[connector]
name = Backup-Connector
role = backup
priority = 2
```

The faneX-ID cloud platform automatically detects and uses backup connectors if the primary fails.

## Security Best Practices

1. **Token Security**
   - Store tokens in encrypted configuration files
   - Use environment variables for production
   - Rotate tokens regularly

2. **Network Security**
   - Use VPN for private network connections
   - Enable TLS/SSL for internet connections
   - Restrict allowed IPs in firewall

3. **Access Control**
   - Run connector with minimal privileges
   - Use dedicated service account
   - Enable audit logging

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to cloud platform

**Solutions:**
- Verify `api_url` is correct
- Check network connectivity
- Verify API token is valid
- Check firewall rules

### Authentication Errors

**Problem:** Token authentication fails

**Solutions:**
- Verify token hasn't expired
- Check token permissions in faneX-ID admin panel
- Regenerate token if needed

### High Latency

**Problem:** Slow response times

**Solutions:**
- Check network bandwidth
- Verify connector is on same network segment
- Consider using backup connector in different location

## Development

### Building from Source

```bash
# Clone repository
git clone https://github.com/faneX-ID/onprem-connector.git
cd onprem-connector

# Install dependencies
pip install -r requirements.txt

# Run in development mode
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### Testing

```bash
# Run tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## License

MIT License - See LICENSE file for details

## Support

- **Documentation**: [https://fanex-id.github.io/it/onprem-connector/](https://fanex-id.github.io/it/onprem-connector/)
- **Issues**: [GitHub Issues](https://github.com/faneX-ID/onprem-connector/issues)
- **Community**: [GitHub Discussions](https://github.com/faneX-ID/onprem-connector/discussions)
