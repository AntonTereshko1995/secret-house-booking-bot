import json
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from singleton_decorator import singleton
from google.cloud import secretmanager
from src.services.logger_service import LoggerService

@singleton
class SecretManagerService:
    def get_secret_by_dict(self, secret_id: str) -> dict:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/the-secret-house/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_string = response.payload.data.decode("UTF-8")
        LoggerService.error(__name__, f"Secret data: {secret_string}")
        secret_dict = dict(line.split("=", 1) for line in secret_string.splitlines() if "=" in line)
        return secret_dict
    
    def get_secret(self, secret_id: str) -> str:
        client = secretmanager.SecretManagerServiceClient()
        secret_path = f"projects/the-secret-house/secrets/{secret_id}/versions/latest"
        response = client.access_secret_version(request={"name": secret_path})
        secret_string = response.payload.data.decode("UTF-8")
        return secret_string
