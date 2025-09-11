"""
Configuration settings for Coact Client
"""

import platform
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings
import platformdirs


class ServerConfig(BaseModel):
    """Server connection configuration"""
    api_url: str = "http://localhost:8000"
    ws_url: str = "ws://localhost:8000"
    timeout: int = 30
    max_retries: int = 3
    verify_ssl: bool = False


class DeviceConfig(BaseModel):
    """Device configuration"""
    name: Optional[str] = None
    platform: str = platform.system().lower()
    capabilities: dict = Field(default_factory=lambda: {
        "screen_capture": True,
        "mouse_control": True,
        "keyboard_control": True,
        "file_access": True,
        "shell_access": True,
    })
    max_concurrent_tasks: int = 3
    
    @validator("name", pre=True, always=True)
    def set_default_name(cls, v):
        if v is None:
            hostname = platform.node()
            return f"{hostname}-{platform.system().lower()}"
        return v


class SecurityConfig(BaseModel):
    """Security settings"""
    require_task_confirmation: bool = True
    allowed_file_extensions: List[str] = Field(default_factory=lambda: [
        ".txt", ".log", ".png", ".jpg", ".jpeg", ".pdf", ".json", ".xml", ".csv"
    ])
    max_file_size_mb: int = 100
    enable_shell_commands: bool = False
    shell_whitelist: List[str] = Field(default_factory=lambda: [
        "ls", "dir", "pwd", "whoami", "ps", "netstat"
    ])


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    max_file_size_mb: int = 50
    backup_count: int = 5
    enable_remote_logging: bool = True


class Settings(BaseSettings):
    """Main application settings"""
    
    # App info
    app_name: str = "Coact Client"
    app_version: str = "1.0.0"
    environment: str = "production"
    
    # Configuration sections
    server: ServerConfig = Field(default_factory=ServerConfig)
    device: DeviceConfig = Field(default_factory=DeviceConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    
    # Paths
    config_dir: Path = Field(default_factory=lambda: Path(platformdirs.user_config_dir("coact-client")))
    data_dir: Path = Field(default_factory=lambda: Path(platformdirs.user_data_dir("coact-client")))
    cache_dir: Path = Field(default_factory=lambda: Path(platformdirs.user_cache_dir("coact-client")))
    log_dir: Path = Field(default_factory=lambda: Path(platformdirs.user_log_dir("coact-client")))
    
    # Runtime settings
    debug: bool = False
    auto_start: bool = True
    check_for_updates: bool = True
    
    class Config:
        env_prefix = "COACT_"
        env_nested_delimiter = "__"
        case_sensitive = False
        
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure all required directories exist"""
        for path in [self.config_dir, self.data_dir, self.cache_dir, self.log_dir]:
            path.mkdir(parents=True, exist_ok=True)
    
    def get_config_file(self) -> Path:
        """Get path to main config file"""
        return self.config_dir / "config.yaml"
    
    def get_credentials_file(self) -> Path:
        """Get path to credentials file"""
        return self.config_dir / "credentials.json"
    
    def get_log_file(self) -> Path:
        """Get path to main log file"""
        return self.log_dir / "coact-client.log"


# Global settings instance
settings = Settings()