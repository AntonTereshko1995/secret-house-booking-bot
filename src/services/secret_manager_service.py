import logging

from singleton_decorator import singleton
from google.cloud import secretmanager

_logger = logging.getLogger(__name__)


@singleton
class SecretManagerService:
    def get_secret_by_dict(self, secret_id: str) -> dict:
        _logger.info("Fetching secret dict: %s", secret_id)
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/the-secret-house/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            secret_string = response.payload.data.decode("UTF-8")
            secret_dict = dict(
                line.split("=", 1) for line in secret_string.splitlines() if "=" in line
            )
            return secret_dict
        except Exception as e:
            _logger.error("Failed to fetch secret dict %s: %s", secret_id, e)
            raise

    def get_secret(self, secret_id: str) -> str:
        _logger.info("Fetching secret: %s", secret_id)
        try:
            client = secretmanager.SecretManagerServiceClient()
            secret_path = f"projects/the-secret-house/secrets/{secret_id}/versions/latest"
            response = client.access_secret_version(request={"name": secret_path})
            secret_string = response.payload.data.decode("UTF-8")
            return secret_string
        except Exception as e:
            _logger.error("Failed to fetch secret %s: %s", secret_id, e)
            raise
