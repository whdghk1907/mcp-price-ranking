"""
커스텀 예외 정의
프로젝트별 예외 클래스들
"""

from typing import Optional, Dict, Any


class PriceRankingError(Exception):
    """기본 예외 클래스"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
    
    def __str__(self):
        return f"{self.message} (code: {self.error_code})" if self.error_code else self.message


class APIError(PriceRankingError):
    """API 관련 예외"""
    
    def __init__(self, message: str, status_code: Optional[int] = None, api_response: Optional[Dict] = None):
        super().__init__(message, error_code="API_ERROR")
        self.status_code = status_code
        self.api_response = api_response or {}


class AuthenticationError(APIError):
    """인증 관련 예외"""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(message)


class DataValidationError(PriceRankingError):
    """데이터 검증 예외"""
    
    def __init__(self, message: str, field: Optional[str] = None, value: Optional[Any] = None):
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field
        self.value = value
        
    def __str__(self):
        base = super().__str__()
        if self.field:
            return f"{base} (field: {self.field}, value: {self.value})"
        return base


class CacheError(PriceRankingError):
    """캐시 관련 예외"""
    
    def __init__(self, message: str, cache_key: Optional[str] = None):
        super().__init__(message, error_code="CACHE_ERROR")
        self.cache_key = cache_key


class RateLimitError(PriceRankingError):
    """요청 제한 예외"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None):
        super().__init__(message, error_code="RATE_LIMIT_ERROR")
        self.retry_after = retry_after


class DataNotFoundError(PriceRankingError):
    """데이터 없음 예외"""
    
    def __init__(self, message: str, resource: Optional[str] = None):
        super().__init__(message, error_code="DATA_NOT_FOUND")
        self.resource = resource


class ConfigurationError(PriceRankingError):
    """설정 관련 예외"""
    
    def __init__(self, message: str, config_key: Optional[str] = None):
        super().__init__(message, error_code="CONFIG_ERROR")
        self.config_key = config_key


class AnalysisError(PriceRankingError):
    """분석 관련 예외"""
    
    def __init__(self, message: str, analysis_type: Optional[str] = None):
        super().__init__(message, error_code="ANALYSIS_ERROR")
        self.analysis_type = analysis_type


class ToolExecutionError(PriceRankingError):
    """도구 실행 예외"""
    
    def __init__(self, message: str, tool_name: Optional[str] = None, parameters: Optional[Dict] = None):
        super().__init__(message, error_code="TOOL_EXECUTION_ERROR")
        self.tool_name = tool_name
        self.parameters = parameters or {}