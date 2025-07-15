"""
MCP Price Ranking Server
메인 MCP 서버 클래스
"""

import asyncio
import logging
from typing import Dict, Any, List
from datetime import datetime
from src.tools.registry import ToolRegistry, register_default_tools
from src.utils import setup_logger

# MCP 라이브러리가 설치되면 활성화
# from mcp.server import MCPServer
# from mcp.tools import Tool


class PriceRankingMCPServer:
    """
    가격 순위 분석 MCP 서버
    
    TDD: 현재는 기본 구조만 구현
    향후 MCP 라이브러리 설치 후 실제 MCP 서버로 변경
    """
    
    def __init__(self, name: str = "price-ranking-server"):
        self.name = name
        self.tool_registry = ToolRegistry()
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        self.is_running = False
        
    async def start(self):
        """서버 시작"""
        self.is_running = True
        
        # 기본 도구들 등록
        self._register_default_tools()
        self.logger.info(f"Default tools registered: {self.tool_registry.get_tool_count()} tools")
        
        self.logger.info(f"MCP Server '{self.name}' started")
        
    async def stop(self):
        """서버 중지"""
        self.is_running = False
        
        # 도구들 정리
        await self.tool_registry.cleanup_tools()
        
        self.logger.info(f"MCP Server '{self.name}' stopped")
    
    async def health_check(self) -> Dict[str, Any]:
        """헬스 체크"""
        return {
            "status": "healthy" if self.is_running else "stopped",
            "timestamp": datetime.now().isoformat(),
            "server_name": self.name,
            "registered_tools": [tool.name for tool in self.tool_registry.list_tools()],
            "tool_count": self.tool_registry.get_tool_count(),
            "version": "0.1.0"
        }
    
    def list_tools(self) -> List[Dict[str, Any]]:
        """등록된 도구 스키마 목록 반환"""
        return self.tool_registry.get_tool_schemas()
    
    def get_tool(self, tool_name: str):
        """도구 인스턴스 반환"""
        for tool in self.tool_registry.list_tools():
            if tool.name == tool_name:
                return tool
        return None
    
    async def call_tool(self, tool_name: str, **kwargs) -> Dict[str, Any]:
        """도구 실행"""
        tool = self.get_tool(tool_name)
        if tool is None:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        self.logger.info(f"Executing tool: {tool_name}")
        return await tool.execute(**kwargs)
    
    def _register_default_tools(self):
        """기본 도구들을 레지스트리에 등록"""
        from src.tools.integrated_price_tool import IntegratedPriceRankingTool
        from src.tools.high_low_tools import HighLowTool
        from src.tools.limit_tools import LimitTool
        
        # 기존 도구들 정리
        self.tool_registry.clear()
        
        # 기본 도구들 등록
        self.tool_registry.register_tool("price_ranking", IntegratedPriceRankingTool())
        self.tool_registry.register_tool("high_low", HighLowTool())
        self.tool_registry.register_tool("limit", LimitTool())


# 호환성을 위한 별칭
Server = PriceRankingMCPServer

# 서버 인스턴스 생성 함수
def create_server() -> PriceRankingMCPServer:
    """서버 인스턴스 생성"""
    return PriceRankingMCPServer()


# 개발/테스트용 메인 함수
async def main():
    """개발용 메인 함수"""
    server = create_server()
    await server.start()
    
    # 헬스 체크 테스트
    health = await server.health_check()
    print(f"Health check: {health}")
    
    # 도구 목록 출력
    tools = server.list_tools()
    print(f"Registered tools: {len(tools)}")
    for tool in tools:
        print(f"  - {tool['name']}: {tool['description']}")
    
    await server.stop()


if __name__ == "__main__":
    asyncio.run(main())