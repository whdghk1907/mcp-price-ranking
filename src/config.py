"""
설정 관리 모듈
환경 변수 및 설정 값들을 관리
"""

import os
from typing import Optional
from pathlib import Path
from dataclasses import dataclass


@dataclass
class APIConfig:
    """API 설정"""
    app_key: str
    app_secret: str
    base_url: str = "https://openapi.koreainvestment.com:9443"
    timeout: int = 30


@dataclass
class CacheConfig:
    """캐시 설정"""
    ttl_seconds: int = 30
    max_size: int = 10000
    redis_url: Optional[str] = None


@dataclass
class LogConfig:
    """로그 설정"""
    level: str = "INFO"
    file_path: Optional[str] = None
    max_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5


@dataclass
class ServerConfig:
    """서버 설정"""
    name: str = "price-ranking-server"
    host: str = "0.0.0.0"
    port: int = 8080
    max_requests_per_minute: int = 1000


class Config:
    """메인 설정 클래스"""
    
    def __init__(self):
        self.api = self._load_api_config()
        self.cache = self._load_cache_config()
        self.log = self._load_log_config()
        self.server = self._load_server_config()
        
    def _load_api_config(self) -> APIConfig:
        """API 설정 로드"""
        app_key = os.getenv("KOREA_INVESTMENT_APP_KEY")
        app_secret = os.getenv("KOREA_INVESTMENT_APP_SECRET")
        
        if not app_key or not app_secret:
            # 개발/테스트 환경에서는 더미 값 사용
            app_key = app_key or "dummy_app_key"
            app_secret = app_secret or "dummy_app_secret"
            
        return APIConfig(
            app_key=app_key,
            app_secret=app_secret,
            base_url=os.getenv("API_BASE_URL", "https://openapi.koreainvestment.com:9443"),
            timeout=int(os.getenv("API_TIMEOUT", "30"))
        )
    
    def _load_cache_config(self) -> CacheConfig:
        """캐시 설정 로드"""
        return CacheConfig(
            ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "30")),
            max_size=int(os.getenv("CACHE_MAX_SIZE", "10000")),
            redis_url=os.getenv("REDIS_URL")
        )
    
    def _load_log_config(self) -> LogConfig:
        """로그 설정 로드"""
        return LogConfig(
            level=os.getenv("LOG_LEVEL", "INFO"),
            file_path=os.getenv("LOG_FILE_PATH"),
            max_size=int(os.getenv("LOG_MAX_SIZE", str(10 * 1024 * 1024))),
            backup_count=int(os.getenv("LOG_BACKUP_COUNT", "5"))
        )
    
    def _load_server_config(self) -> ServerConfig:
        """서버 설정 로드"""
        return ServerConfig(
            name=os.getenv("SERVER_NAME", "price-ranking-server"),
            host=os.getenv("SERVER_HOST", "0.0.0.0"),
            port=int(os.getenv("SERVER_PORT", "8080")),
            max_requests_per_minute=int(os.getenv("MAX_REQUESTS_PER_MINUTE", "1000"))
        )
    
    def load_env_file(self, env_file: str = ".env"):
        """환경 변수 파일 로드"""
        env_path = Path(env_file)
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        key, value = line.split('=', 1)
                        os.environ[key] = value


# 전역 설정 인스턴스
config = Config()