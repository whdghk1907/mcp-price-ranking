"""
도구 레지스트리
MCP 서버에서 사용할 도구들을 등록하고 관리하는 레지스트리
"""

from typing import Dict, List, Optional, Any
from src.tools import BaseTool
from src.exceptions import ToolExecutionError
from src.utils import setup_logger


class ToolRegistry:
    """도구 레지스트리 클래스"""
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
    
    def register_tool(self, key: str, tool: BaseTool) -> None:
        """도구 등록
        
        Args:
            key: 도구 식별 키
            tool: 등록할 도구 인스턴스
            
        Raises:
            ToolExecutionError: 중복 키로 도구 등록 시
        """
        if key in self._tools:
            raise ToolExecutionError(
                f"Tool with key '{key}' is already registered",
                tool_name=tool.name if tool else "unknown"
            )
        
        self._tools[key] = tool
        self.logger.info(f"Tool registered: {key} -> {tool.name}")
    
    def get_tool(self, key: str) -> Optional[BaseTool]:
        """등록된 도구 조회
        
        Args:
            key: 도구 식별 키
            
        Returns:
            등록된 도구 인스턴스 또는 None
        """
        return self._tools.get(key)
    
    def list_tools(self) -> List[BaseTool]:
        """등록된 모든 도구 목록 반환
        
        Returns:
            등록된 도구들의 리스트
        """
        return list(self._tools.values())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """모든 도구의 스키마 반환
        
        Returns:
            도구 스키마들의 리스트
        """
        schemas = []
        for tool in self._tools.values():
            try:
                schema = tool.get_schema()
                schemas.append(schema)
            except Exception as e:
                self.logger.error(f"Failed to get schema for tool {tool.name}: {str(e)}")
        
        return schemas
    
    def unregister_tool(self, key: str) -> bool:
        """도구 등록 해제
        
        Args:
            key: 도구 식별 키
            
        Returns:
            성공 여부
        """
        if key in self._tools:
            tool = self._tools.pop(key)
            self.logger.info(f"Tool unregistered: {key} -> {tool.name}")
            return True
        return False
    
    def clear(self) -> None:
        """모든 도구 등록 해제"""
        self._tools.clear()
        self.logger.info("All tools unregistered")
    
    def get_tool_count(self) -> int:
        """등록된 도구 개수 반환
        
        Returns:
            등록된 도구 개수
        """
        return len(self._tools)
    
    async def cleanup_tools(self) -> None:
        """모든 도구의 리소스 정리"""
        for key, tool in self._tools.items():
            try:
                if hasattr(tool, 'cleanup') and callable(tool.cleanup):
                    await tool.cleanup()
                    self.logger.info(f"Cleaned up tool: {key}")
            except Exception as e:
                self.logger.error(f"Failed to cleanup tool {key}: {str(e)}")


# 전역 도구 레지스트리 인스턴스
_global_registry = None


def get_registry() -> ToolRegistry:
    """전역 도구 레지스트리 인스턴스 반환
    
    Returns:
        전역 도구 레지스트리 인스턴스
    """
    global _global_registry
    if _global_registry is None:
        _global_registry = ToolRegistry()
    return _global_registry


def register_default_tools() -> ToolRegistry:
    """기본 도구들을 레지스트리에 등록
    
    Returns:
        도구들이 등록된 레지스트리 인스턴스
    """
    from src.tools.integrated_price_tool import IntegratedPriceRankingTool
    from src.tools.high_low_tools import HighLowTool
    from src.tools.limit_tools import LimitTool
    
    registry = get_registry()
    
    # 기존 도구들 정리
    registry.clear()
    
    # 기본 도구들 등록
    registry.register_tool("price_ranking", IntegratedPriceRankingTool())
    registry.register_tool("high_low", HighLowTool())
    registry.register_tool("limit", LimitTool())
    
    return registry