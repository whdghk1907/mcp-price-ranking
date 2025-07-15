"""
기본 도구 클래스
헬스체크, 정보 조회 등 기본적인 도구들
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from src.tools import BaseTool
from src.exceptions import ToolExecutionError


class HealthCheckTool(BaseTool):
    """서버 헬스체크 도구"""
    
    def __init__(self):
        super().__init__(
            name="health_check",
            description="서버 상태 및 헬스체크 정보 조회"
        )
        self.start_time = datetime.now()
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """헬스체크 실행"""
        try:
            current_time = datetime.now()
            uptime = (current_time - self.start_time).total_seconds()
            
            return {
                "status": "healthy",
                "timestamp": current_time.isoformat(),
                "uptime": uptime,
                "version": "0.1.0",
                "server_name": "price-ranking-server"
            }
            
        except Exception as e:
            raise ToolExecutionError(
                f"Health check failed: {str(e)}",
                tool_name=self.name
            )
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마 (헬스체크는 파라미터 없음)"""
        return {
            "type": "object",
            "properties": {},
            "required": []
        }


class InfoTool(BaseTool):
    """서버 정보 조회 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_server_info",
            description="서버 정보 및 사용 가능한 도구 목록 조회"
        )
    
    async def execute(self, detail: bool = False, **kwargs) -> Dict[str, Any]:
        """서버 정보 조회"""
        try:
            info = {
                "server_name": "price-ranking-server",
                "version": "0.1.0",
                "api_version": "1.0",
                "supported_markets": ["ALL", "KOSPI", "KOSDAQ"],
                "available_tools": self._get_available_tools(),
                "timestamp": datetime.now().isoformat()
            }
            
            if detail:
                info["tool_schemas"] = self._get_tool_schemas()
                info["capabilities"] = self._get_capabilities()
            
            return info
            
        except Exception as e:
            raise ToolExecutionError(
                f"Failed to get server info: {str(e)}",
                tool_name=self.name,
                parameters=kwargs
            )
    
    def _get_available_tools(self) -> List[str]:
        """사용 가능한 도구 목록"""
        return [
            "health_check",
            "get_server_info",
            "get_price_change_ranking",
            "get_52week_high_low",
            "get_limit_stocks",
            "get_consecutive_moves",
            "get_gap_stocks",
            "get_volatility_ranking",
            "get_price_alerts"
        ]
    
    def _get_tool_schemas(self) -> List[Dict[str, Any]]:
        """도구 스키마 목록"""
        # 향후 tool_registry에서 가져오도록 구현
        return []
    
    def _get_capabilities(self) -> Dict[str, Any]:
        """서버 기능 정보"""
        return {
            "real_time_data": True,
            "historical_data": True,
            "technical_analysis": True,
            "pattern_detection": True,
            "alert_system": True,
            "caching": True,
            "rate_limiting": True
        }
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "detail": {
                    "type": "boolean",
                    "description": "상세 정보 포함 여부",
                    "default": False
                }
            },
            "required": []
        }


class EchoTool(BaseTool):
    """에코 도구 (테스트용)"""
    
    def __init__(self):
        super().__init__(
            name="echo",
            description="입력된 메시지를 그대로 반환하는 테스트 도구"
        )
    
    async def execute(self, message: str, **kwargs) -> Dict[str, Any]:
        """에코 실행"""
        return {
            "original_message": message,
            "echo": message,
            "timestamp": datetime.now().isoformat(),
            "additional_params": kwargs
        }
    
    def validate_parameters(self, **kwargs) -> bool:
        """파라미터 검증"""
        return "message" in kwargs and isinstance(kwargs["message"], str)
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "반환할 메시지",
                    "minLength": 1
                }
            },
            "required": ["message"]
        }