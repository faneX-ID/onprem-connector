"""
faneX-ID OnPrem Connector
A lightweight connector bridging on-premises infrastructure with faneX-ID SaaS platform.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import httpx
import configparser
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

app = FastAPI(title="faneX-ID OnPrem Connector", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CONFIG_FILE = os.getenv("CONFIG_FILE", "config.ini")
config = configparser.ConfigParser()


class ConnectorConfig:
    """Connector configuration manager."""

    def __init__(self):
        self.name: str = "OnPrem-Connector"
        self.role: str = "primary"
        self.version: str = "1.0.0"
        self.api_url: str = ""
        self.api_token: str = ""
        self.verify_ssl: bool = True
        self.timeout: int = 30
        self.listen_host: str = "0.0.0.0"
        self.listen_port: int = 8080
        self.allowed_ips: list = []
        self.token_refresh_interval: int = 3600
        self.max_retries: int = 3
        self.retry_delay: int = 5
        self.log_level: str = "INFO"
        self.last_token_refresh: Optional[datetime] = None

    def load(self):
        """Load configuration from file."""
        if not os.path.exists(CONFIG_FILE):
            logger.warning(f"Config file {CONFIG_FILE} not found, using defaults")
            return

        config.read(CONFIG_FILE)

        # Connector settings
        if config.has_section('connector'):
            self.name = config.get('connector', 'name', fallback=self.name)
            self.role = config.get('connector', 'role', fallback=self.role)
            self.version = config.get('connector', 'version', fallback=self.version)

        # Cloud settings
        if config.has_section('cloud'):
            self.api_url = config.get('cloud', 'api_url', fallback=self.api_url)
            self.api_token = config.get('cloud', 'api_token', fallback=self.api_token)
            self.verify_ssl = config.getboolean('cloud', 'verify_ssl', fallback=self.verify_ssl)
            self.timeout = config.getint('cloud', 'timeout', fallback=self.timeout)

        # Network settings
        if config.has_section('network'):
            self.listen_host = config.get('network', 'listen_host', fallback=self.listen_host)
            self.listen_port = config.getint('network', 'listen_port', fallback=self.listen_port)
            allowed_ips_str = config.get('network', 'allowed_ips', fallback='')
            self.allowed_ips = [ip.strip() for ip in allowed_ips_str.split(',') if ip.strip()]

        # Security settings
        if config.has_section('security'):
            self.token_refresh_interval = config.getint('security', 'token_refresh_interval', fallback=self.token_refresh_interval)
            self.max_retries = config.getint('security', 'max_retries', fallback=self.max_retries)
            self.retry_delay = config.getint('security', 'retry_delay', fallback=self.retry_delay)

        # Logging settings
        if config.has_section('logging'):
            self.log_level = config.get('logging', 'level', fallback=self.log_level)

        logger.info(f"Configuration loaded: {self.name} (role: {self.role})")

    def validate(self) -> bool:
        """Validate configuration."""
        if not self.api_url:
            logger.error("api_url not configured")
            return False
        if not self.api_token:
            logger.error("api_token not configured")
            return False
        return True


connector_config = ConnectorConfig()
connector_config.load()

# HTTP client for cloud API
http_client = httpx.AsyncClient(
    timeout=connector_config.timeout,
    verify=connector_config.verify_ssl,
    headers={
        "Authorization": f"Bearer {connector_config.api_token}",
        "User-Agent": f"faneX-ID-Connector/{connector_config.version}"
    }
)


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: str
    connector_name: str
    connector_role: str
    version: str
    cloud_connection: str


class StatusResponse(BaseModel):
    """Detailed status response."""
    connector: dict
    cloud: dict
    network: dict
    uptime: str


async def verify_token(authorization: Optional[str] = Header(None)) -> bool:
    """Verify API token for protected endpoints."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    # In production, implement proper token validation
    # For now, use a simple check
    expected_token = os.getenv("ADMIN_TOKEN", "admin-token-change-in-production")
    if token != expected_token:
        raise HTTPException(status_code=403, detail="Invalid token")
    return True


@app.on_event("startup")
async def startup():
    """Startup event handler."""
    logger.info(f"Starting faneX-ID OnPrem Connector v{connector_config.version}")
    logger.info(f"Connector: {connector_config.name} (Role: {connector_config.role})")

    # Validate configuration
    if not connector_config.validate():
        logger.error("Invalid configuration, exiting")
        sys.exit(1)

    # Test cloud connection
    try:
        response = await http_client.get(f"{connector_config.api_url}/system/status")
        if response.status_code == 200:
            logger.info("Successfully connected to faneX-ID cloud platform")
        else:
            logger.warning(f"Cloud connection test returned status {response.status_code}")
    except Exception as e:
        logger.error(f"Failed to connect to cloud platform: {e}")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event handler."""
    logger.info("Shutting down connector")
    await http_client.aclose()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    # Test cloud connection
    cloud_status = "disconnected"
    try:
        response = await http_client.get(f"{connector_config.api_url}/system/status")
        if response.status_code == 200:
            cloud_status = "connected"
    except Exception as e:
        logger.debug(f"Cloud connection check failed: {e}")

    return HealthResponse(
        status="healthy" if cloud_status == "connected" else "degraded",
        timestamp=datetime.utcnow().isoformat(),
        connector_name=connector_config.name,
        connector_role=connector_config.role,
        version=connector_config.version,
        cloud_connection=cloud_status
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Get detailed connector status."""
    # Test cloud connection
    cloud_info = {"status": "unknown", "response_time": None}
    try:
        start_time = datetime.utcnow()
        response = await http_client.get(f"{connector_config.api_url}/system/status")
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        cloud_info = {
            "status": "connected" if response.status_code == 200 else "error",
            "response_time_ms": round(response_time, 2),
            "status_code": response.status_code
        }
    except Exception as e:
        cloud_info = {"status": "error", "error": str(e)}

    return StatusResponse(
        connector={
            "name": connector_config.name,
            "role": connector_config.role,
            "version": connector_config.version
        },
        cloud={
            "api_url": connector_config.api_url,
            **cloud_info
        },
        network={
            "listen_host": connector_config.listen_host,
            "listen_port": connector_config.listen_port,
            "allowed_ips": connector_config.allowed_ips
        },
        uptime="N/A"  # Would need to track start time
    )


@app.get("/metrics")
async def get_metrics():
    """Prometheus-compatible metrics endpoint."""
    # Basic metrics - extend as needed
    metrics = [
        "# HELP fanexid_connector_health Connector health status (1=healthy, 0=unhealthy)",
        "# TYPE fanexid_connector_health gauge",
        "fanexid_connector_health 1",
        "# HELP fanexid_connector_version Connector version",
        "# TYPE fanexid_connector_version gauge",
        f'fanexid_connector_version{{version="{connector_config.version}"}} 1',
    ]
    return "\n".join(metrics)


@app.post("/reload")
async def reload_config(token: bool = Depends(verify_token)):
    """Reload configuration (requires authentication)."""
    connector_config.load()
    if connector_config.validate():
        # Update HTTP client headers
        http_client.headers["Authorization"] = f"Bearer {connector_config.api_token}"
        return {"status": "success", "message": "Configuration reloaded"}
    else:
        raise HTTPException(status_code=400, detail="Invalid configuration")


@app.post("/sync/employees")
async def sync_employees(data: dict):
    """Sync employee data to cloud platform."""
    try:
        response = await http_client.post(
            f"{connector_config.api_url}/onprem/sync/employees",
            json=data
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as e:
        logger.error(f"Sync failed: {e.response.status_code} - {e.response.text}")
        raise HTTPException(status_code=e.response.status_code, detail=e.response.text)
    except Exception as e:
        logger.error(f"Sync error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "faneX-ID OnPrem Connector",
        "version": connector_config.version,
        "status": "running",
        "endpoints": {
            "health": "/health",
            "status": "/status",
            "metrics": "/metrics"
        }
    }


if __name__ == "__main__":
    # Create logs directory
    Path("logs").mkdir(exist_ok=True)

    # Load configuration
    connector_config.load()

    if not connector_config.validate():
        logger.error("Invalid configuration. Please check config.ini")
        sys.exit(1)

    # Run server
    uvicorn.run(
        app,
        host=connector_config.listen_host,
        port=connector_config.listen_port,
        log_level=connector_config.log_level.lower()
    )
