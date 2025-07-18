"""
Admin Service - Manage application settings without a database
"""
import json
import os
from typing import Dict, Any, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class AdminService:
    """Service for managing admin settings using file-based storage"""
    
    def __init__(self, config_file: str = "/app/config/admin_settings.json"):
        self.config_file = Path(config_file)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Default admin settings
        self.default_settings = {
            "max_concurrent_jobs": int(os.getenv("MAX_CONCURRENT_JOBS", 5)),
            "max_urls_per_job": int(os.getenv("MAX_URLS_PER_JOB", 10)),
            "default_max_tokens": int(os.getenv("DEFAULT_MAX_TOKENS", 3000)),
            "allowed_domains": [],  # Empty = allow all
            "blocked_domains": ["localhost", "127.0.0.1", "0.0.0.0"],
            "rate_limits": {
                "requests_per_minute": 10,
                "requests_per_hour": 100
            },
            "ai_settings": {
                "default_provider": "openai",
                "default_model": "gpt-4o-mini",
                "temperature": 0.7,
                "max_retries": 3
            },
            "ui_settings": {
                "site_title": "Bookerizer",
                "site_description": "Transform web content into illustrated children's stories",
                "enable_registration": True,
                "require_auth": False,
                "max_file_size_mb": 50
            },
            "notification_settings": {
                "admin_email": os.getenv("ADMIN_EMAIL", "admin@bookerizer.com"),
                "notify_on_errors": True,
                "notify_on_completions": False
            }
        }
        
        # Load existing settings or create defaults
        self._load_settings()
    
    def _load_settings(self) -> None:
        """Load settings from file or create defaults"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    loaded_settings = json.load(f)
                # Merge with defaults to ensure all keys exist
                self.settings = {**self.default_settings, **loaded_settings}
            else:
                self.settings = self.default_settings.copy()
                self._save_settings()
        except Exception as e:
            logger.error(f"Error loading admin settings: {e}")
            self.settings = self.default_settings.copy()
    
    def _save_settings(self) -> None:
        """Save settings to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving admin settings: {e}")
    
    def get_settings(self) -> Dict[str, Any]:
        """Get all admin settings"""
        return self.settings.copy()
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a specific setting"""
        keys = key.split('.')
        value = self.settings
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value
    
    def update_setting(self, key: str, value: Any) -> bool:
        """Update a specific setting"""
        try:
            keys = key.split('.')
            setting = self.settings
            
            # Navigate to the parent
            for k in keys[:-1]:
                if k not in setting:
                    setting[k] = {}
                setting = setting[k]
            
            # Set the value
            setting[keys[-1]] = value
            self._save_settings()
            return True
        except Exception as e:
            logger.error(f"Error updating setting {key}: {e}")
            return False
    
    def update_settings(self, new_settings: Dict[str, Any]) -> bool:
        """Update multiple settings"""
        try:
            # Deep merge with existing settings
            def deep_merge(base: dict, updates: dict) -> dict:
                for key, value in updates.items():
                    if isinstance(value, dict) and key in base and isinstance(base[key], dict):
                        base[key] = deep_merge(base[key], value)
                    else:
                        base[key] = value
                return base
            
            self.settings = deep_merge(self.settings, new_settings)
            self._save_settings()
            return True
        except Exception as e:
            logger.error(f"Error updating settings: {e}")
            return False
    
    def reset_to_defaults(self) -> bool:
        """Reset all settings to defaults"""
        try:
            self.settings = self.default_settings.copy()
            self._save_settings()
            return True
        except Exception as e:
            logger.error(f"Error resetting settings: {e}")
            return False
    
    def export_settings(self) -> str:
        """Export settings as JSON string"""
        return json.dumps(self.settings, indent=2)
    
    def import_settings(self, json_string: str) -> bool:
        """Import settings from JSON string"""
        try:
            new_settings = json.loads(json_string)
            return self.update_settings(new_settings)
        except Exception as e:
            logger.error(f"Error importing settings: {e}")
            return False

# Global admin service instance
admin_service = AdminService()