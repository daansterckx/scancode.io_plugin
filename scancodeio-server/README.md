# ScanCode.io Server Setup

Complete Docker Compose setup for ScanCode.io with:
- **ClamAV antivirus scanning** - Automatic virus detection on uploaded files
- **CSRF fixes** - Configured to accept API requests from any host (for remote access)
- **Nginx reverse proxy** - Production-ready with SSL support
- **Health checks** - All services with proper health monitoring

## Quick Start

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` and set your configuration:**
   ```bash
   # Required: Set your server's IP or hostname
   ALLOWED_HOSTS=your-server-ip,your-domain.com,*
   
   # Required: Change the secret key
   SECRET_KEY=$(openssl rand -base64 32)
   
   # Required: Change database password
   DB_PASSWORD=your-secure-password
   ```

3. **Run the setup:**
   ```bash
   ./setup.sh
   ```

4. **Start the services:**
   ```bash
   ./start.sh
   ```

5. **Access ScanCode.io:**
   - Web UI: http://your-server-ip:8000
   - API: http://your-server-ip:8000/api/

## Configuration

### CSRF / Remote Access Settings

To allow API access from remote hosts, these settings are pre-configured:

```
ALLOWED_HOSTS=*                    # Allow all hosts
CORS_ALLOWED_ORIGINS=*             # Allow all CORS origins  
CSRF_TRUSTED_ORIGINS=http://*,https://*  # Trust all origins
```

**⚠️ Security Warning:** These settings allow requests from ANY host. For production:
- Replace `*` with your specific domain(s)
- Use HTTPS with proper SSL certificates
- Set `CSRF_COOKIE_SECURE=True` and `SESSION_COOKIE_SECURE=True`

### ClamAV Antivirus

ClamAV is included and automatically scans uploaded files. Configuration:
- Max file size: 100MB
- Max scan size: 100MB
- Virus database updates: Every 12 hours

### Memory Requirements

Minimum recommended specs:
- **RAM**: 4GB minimum, 8GB+ recommended
- **Disk**: 50GB for scans and database
- **CPU**: 2+ cores (scans use all available CPUs)

## Services

| Service | Description | Port |
|---------|-------------|------|
| web | Django web application | 8000 |
| worker | Background scan processor | - |
| db | PostgreSQL database | 5432 (internal) |
| redis | Redis cache/queue | 6379 (internal) |
| clamav | ClamAV antivirus | 3310 (internal) |
| nginx | Reverse proxy (optional) | 80, 443 |

## Scripts

- `setup.sh` - Initial setup, generates secrets, pulls images
- `start.sh` - Start all services
- `stop.sh` - Stop all services
- `logs.sh` - View logs (use `-f` to follow)

## Troubleshooting

### CSRF Errors from Remote Access

If you get CSRF errors when accessing from another host:
1. Check `ALLOWED_HOSTS` includes your server's IP/hostname
2. Ensure `CSRF_TRUSTED_ORIGINS` is set correctly
3. The default `*` should work for testing

### ClamAV Not Starting

First startup may take a few minutes as ClamAV downloads virus definitions.
Check status with:
```bash
docker-compose logs -f clamav
```

### Permission Errors

If you see permission errors after updating:
```bash
docker-compose run --rm web chown -R app:app /var/scancodeio/
```

## Production Deployment

1. Use Nginx with SSL:
   ```bash
   docker-compose --profile production up -d
   ```

2. Place SSL certificates in `nginx/ssl/`:
   - `cert.pem` - SSL certificate
   - `key.pem` - Private key

3. Update `.env` with secure settings:
   ```
   DEBUG=False
   ALLOWED_HOSTS=your-domain.com
   CSRF_TRUSTED_ORIGINS=https://your-domain.com
   CSRF_COOKIE_SECURE=True
   SESSION_COOKIE_SECURE=True
   ```

## API Usage

Once running, you can use the Python client:

```python
from scancodeio_client import ScanCodeIOClient

client = ScanCodeIOClient(
    base_url="http://your-server-ip:8000",
    api_key="your-api-key"  # Optional
)

result = client.scan_file("/path/to/file.zip", wait=True)
```

## License

MIT License - See LICENSE file