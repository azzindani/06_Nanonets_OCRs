"""
ERP and database connectors for data export.
"""
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime

import requests

from utils.logger import app_logger


class BaseConnector(ABC):
    """Base class for all connectors."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = config.get("name", "unknown")

    @abstractmethod
    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to the destination."""
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test if connection is working."""
        pass

    def transform_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform data according to mapping rules."""
        mapping = self.config.get("field_mapping", {})
        if not mapping:
            return data

        transformed = {}
        for source_field, target_field in mapping.items():
            if source_field in data:
                transformed[target_field] = data[source_field]

        return transformed


class RESTConnector(BaseConnector):
    """REST API connector for generic HTTP integrations."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.base_url = config.get("base_url", "")
        self.endpoint = config.get("endpoint", "")
        self.method = config.get("method", "POST").upper()
        self.headers = config.get("headers", {})
        self.auth_type = config.get("auth_type", "none")
        self.auth_config = config.get("auth", {})

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers."""
        if self.auth_type == "bearer":
            token = self.auth_config.get("token", "")
            return {"Authorization": f"Bearer {token}"}
        elif self.auth_type == "api_key":
            key_name = self.auth_config.get("header_name", "X-API-Key")
            key_value = self.auth_config.get("key", "")
            return {key_name: key_value}
        elif self.auth_type == "basic":
            import base64
            username = self.auth_config.get("username", "")
            password = self.auth_config.get("password", "")
            credentials = base64.b64encode(f"{username}:{password}".encode()).decode()
            return {"Authorization": f"Basic {credentials}"}
        return {}

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data via REST API."""
        url = f"{self.base_url.rstrip('/')}/{self.endpoint.lstrip('/')}"

        headers = {
            "Content-Type": "application/json",
            **self.headers,
            **self._get_auth_headers()
        }

        transformed = self.transform_data(data)

        try:
            response = requests.request(
                method=self.method,
                url=url,
                json=transformed,
                headers=headers,
                timeout=30
            )

            response.raise_for_status()

            app_logger.info(
                "REST connector sent data",
                connector=self.name,
                url=url,
                status_code=response.status_code
            )

            return {
                "status": "success",
                "status_code": response.status_code,
                "response": response.json() if response.text else {}
            }

        except requests.exceptions.RequestException as e:
            app_logger.error(
                "REST connector failed",
                connector=self.name,
                url=url,
                error=str(e)
            )
            raise

    def test_connection(self) -> bool:
        """Test REST API connection."""
        try:
            url = f"{self.base_url.rstrip('/')}/health"
            response = requests.get(url, timeout=10)
            return response.status_code < 500
        except:
            return False


class DatabaseConnector(BaseConnector):
    """Database connector for direct SQL inserts."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.db_type = config.get("db_type", "postgresql")
        self.connection_string = config.get("connection_string", "")
        self.table = config.get("table", "")

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Insert data into database."""
        from sqlalchemy import create_engine, text

        engine = create_engine(self.connection_string)
        transformed = self.transform_data(data)

        # Add metadata
        transformed["created_at"] = datetime.utcnow().isoformat()

        columns = ", ".join(transformed.keys())
        placeholders = ", ".join([f":{k}" for k in transformed.keys()])

        query = text(f"INSERT INTO {self.table} ({columns}) VALUES ({placeholders})")

        with engine.connect() as conn:
            result = conn.execute(query, transformed)
            conn.commit()

            app_logger.info(
                "Database connector inserted data",
                connector=self.name,
                table=self.table,
                rows=result.rowcount
            )

            return {
                "status": "success",
                "rows_affected": result.rowcount
            }

    def test_connection(self) -> bool:
        """Test database connection."""
        try:
            from sqlalchemy import create_engine
            engine = create_engine(self.connection_string)
            with engine.connect() as conn:
                conn.execute("SELECT 1")
            return True
        except:
            return False


class SFTPConnector(BaseConnector):
    """SFTP connector for file-based integrations."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.host = config.get("host", "")
        self.port = config.get("port", 22)
        self.username = config.get("username", "")
        self.password = config.get("password")
        self.key_path = config.get("key_path")
        self.remote_path = config.get("remote_path", "/")
        self.file_format = config.get("file_format", "json")

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Upload data as file to SFTP."""
        import paramiko
        from io import StringIO

        # Connect
        transport = paramiko.Transport((self.host, self.port))

        if self.key_path:
            key = paramiko.RSAKey.from_private_key_file(self.key_path)
            transport.connect(username=self.username, pkey=key)
        else:
            transport.connect(username=self.username, password=self.password)

        sftp = paramiko.SFTPClient.from_transport(transport)

        try:
            # Generate filename
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"export_{timestamp}.{self.file_format}"
            remote_file = f"{self.remote_path.rstrip('/')}/{filename}"

            # Convert data to file content
            transformed = self.transform_data(data)

            if self.file_format == "json":
                content = json.dumps(transformed, indent=2)
            elif self.file_format == "csv":
                import csv
                output = StringIO()
                writer = csv.DictWriter(output, fieldnames=transformed.keys())
                writer.writeheader()
                writer.writerow(transformed)
                content = output.getvalue()
            else:
                content = str(transformed)

            # Upload
            with sftp.file(remote_file, "w") as f:
                f.write(content)

            app_logger.info(
                "SFTP connector uploaded file",
                connector=self.name,
                remote_file=remote_file
            )

            return {
                "status": "success",
                "remote_file": remote_file
            }

        finally:
            sftp.close()
            transport.close()

    def test_connection(self) -> bool:
        """Test SFTP connection."""
        try:
            import paramiko
            transport = paramiko.Transport((self.host, self.port))
            if self.key_path:
                key = paramiko.RSAKey.from_private_key_file(self.key_path)
                transport.connect(username=self.username, pkey=key)
            else:
                transport.connect(username=self.username, password=self.password)
            transport.close()
            return True
        except:
            return False


class SAPConnector(BaseConnector):
    """SAP ERP connector (placeholder for SAP RFC/OData)."""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.system_url = config.get("system_url", "")
        self.client = config.get("client", "")
        self.username = config.get("username", "")
        self.password = config.get("password", "")

    def send(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Send data to SAP."""
        # Placeholder - would use pyrfc or OData
        app_logger.info("SAP connector: sending data", connector=self.name)

        return {
            "status": "success",
            "message": "SAP integration placeholder"
        }

    def test_connection(self) -> bool:
        return True


def get_connector(connector_type: str, config: Dict[str, Any]) -> BaseConnector:
    """
    Factory function to get the appropriate connector.

    Args:
        connector_type: Type of connector (rest, database, sftp, sap)
        config: Connector configuration

    Returns:
        Connector instance
    """
    connectors = {
        "rest": RESTConnector,
        "database": DatabaseConnector,
        "sftp": SFTPConnector,
        "sap": SAPConnector,
    }

    if connector_type not in connectors:
        raise ValueError(f"Unknown connector type: {connector_type}")

    return connectors[connector_type](config)
