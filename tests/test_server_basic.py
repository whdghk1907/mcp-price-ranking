"""
MCP 서버 기본 기능 테스트
TDD: 서버 기본 동작을 확인하는 테스트
"""
import pytest
import asyncio
from src.server import PriceRankingMCPServer, create_server


class TestServerBasic:
    """서버 기본 기능 테스트"""
    
    @pytest.fixture
    def server(self):
        """테스트용 서버 인스턴스"""
        return create_server()
    
    def test_server_creation(self):
        """서버 생성 테스트"""
        server = create_server()
        
        assert server is not None
        assert isinstance(server, PriceRankingMCPServer)
        assert server.name == "price-ranking-server"
        assert not server.is_running
        assert len(server.tools) == 0
    
    @pytest.mark.asyncio
    async def test_server_start_stop(self, server):
        """서버 시작/중지 테스트"""
        # 초기 상태
        assert not server.is_running
        
        # 서버 시작
        await server.start()
        assert server.is_running
        
        # 서버 중지
        await server.stop()
        assert not server.is_running
    
    @pytest.mark.asyncio
    async def test_health_check(self, server):
        """헬스 체크 테스트"""
        # 서버 중지 상태에서 헬스 체크
        health = await server.health_check()
        
        assert health["status"] == "stopped"
        assert health["server_name"] == "price-ranking-server"
        assert health["version"] == "0.1.0"
        assert "timestamp" in health
        assert "registered_tools" in health
        
        # 서버 시작 후 헬스 체크
        await server.start()
        health = await server.health_check()
        
        assert health["status"] == "healthy"
        assert health["server_name"] == "price-ranking-server"
    
    def test_tool_registration(self, server):
        """도구 등록 테스트"""
        # 더미 도구 함수
        async def dummy_tool(**kwargs):
            return {"result": "dummy"}
        
        # 도구 등록
        server.register_tool("dummy_tool", dummy_tool)
        
        # 등록 확인
        assert "dummy_tool" in server.tools
        assert len(server.get_tools()) == 1
        assert server.get_tools()[0] == "dummy_tool"
    
    @pytest.mark.asyncio
    async def test_server_with_tools(self, server):
        """도구가 등록된 서버 테스트"""
        # 테스트 도구 등록
        async def test_tool(**kwargs):
            return {"message": "test tool executed", "args": kwargs}
        
        server.register_tool("test_tool", test_tool)
        
        # 서버 시작
        await server.start()
        
        # 헬스 체크에서 도구 확인
        health = await server.health_check()
        assert "test_tool" in health["registered_tools"]
        
        # 도구 목록 확인
        tools = server.get_tools()
        assert "test_tool" in tools


class TestServerConfig:
    """서버 설정 테스트"""
    
    def test_server_custom_name(self):
        """커스텀 이름으로 서버 생성"""
        custom_server = PriceRankingMCPServer("custom-server")
        
        assert custom_server.name == "custom-server"
        assert not custom_server.is_running
    
    def test_server_logger_setup(self):
        """로거 설정 확인"""
        server = create_server()
        
        assert server.logger is not None
        assert server.logger.name == "price-ranking-server"


class TestServerIntegration:
    """서버 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_server_lifecycle(self):
        """서버 전체 라이프사이클 테스트"""
        # 1. 서버 생성
        server = create_server()
        assert not server.is_running
        
        # 2. 도구 등록
        async def sample_tool(param1: str = "default"):
            return {"received": param1, "timestamp": "2024-01-01"}
        
        server.register_tool("sample_tool", sample_tool)
        
        # 3. 서버 시작
        await server.start()
        assert server.is_running
        
        # 4. 헬스 체크
        health = await server.health_check()
        assert health["status"] == "healthy"
        assert "sample_tool" in health["registered_tools"]
        
        # 5. 서버 중지
        await server.stop()
        assert not server.is_running
        
        # 6. 중지 후 헬스 체크
        health = await server.health_check()
        assert health["status"] == "stopped"