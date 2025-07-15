"""
Tools 패키지
MCP 도구들을 정의하고 관리
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class BaseTool(ABC):
    """기본 도구 인터페이스"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
    
    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """도구 실행 (추상 메서드)"""
        pass
    
    def validate_parameters(self, **kwargs) -> bool:
        """파라미터 검증 (기본 구현)"""
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """도구 스키마 반환"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self._get_parameters_schema()
        }
    
    @abstractmethod
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마 정의 (추상 메서드)"""
        pass


class ToolRegistry:
    """도구 등록 및 관리"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
    
    def register(self, tool: BaseTool):
        """도구 등록"""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[BaseTool]:
        """도구 조회"""
        return self._tools.get(name)
    
    def list_tools(self) -> list[str]:
        """등록된 도구 목록"""
        return list(self._tools.keys())
    
    def get_all_schemas(self) -> list[Dict[str, Any]]:
        """모든 도구 스키마 반환"""
        return [tool.get_schema() for tool in self._tools.values()]


# 전역 도구 레지스트리
tool_registry = ToolRegistry()