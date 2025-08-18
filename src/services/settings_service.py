import json
import os
from singleton_decorator import singleton
from src.services.logger_service import LoggerService

@singleton
class SettingsService:
    FILE_PATH = "data/settings.json"

    def __init__(self):
        self._data = self._load_from_json()

    def _load_from_json(self):
        if os.path.exists(self.FILE_PATH):
            try:
                with open(self.FILE_PATH, "r", encoding="utf-8") as file:
                    return json.load(file)
            except json.JSONDecodeError as e:
                LoggerService.error(__name__, f"_load_from_json", e)
                print("⚠️ Ошибка при загрузке JSON, файл поврежден. Используем значения по умолчанию.")
                return {}
        return {}

    def _save_to_json(self):
        os.makedirs(os.path.dirname(self.FILE_PATH), exist_ok=True)
        with open(self.FILE_PATH, "w", encoding="utf-8") as file:
            json.dump(self._data, file, indent=4, ensure_ascii=False)   

    @property
    def password(self):
        return self._data.get("password", "")

    @password.setter
    def password(self, value):
        self._data["password"] = value
        self._save_to_json()

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self._save_to_json()
