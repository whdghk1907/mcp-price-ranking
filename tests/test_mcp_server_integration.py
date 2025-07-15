"""
MCP 서버 통합 테스트
TDD: MCP 서버와 도구들의 완전한 통합 테스트
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json
from src.server import main
from src.tools.integrated_price_tool import IntegratedPriceRankingTool
from src.tools.high_low_tools import HighLowTool
from src.tools.limit_tools import LimitTool


class TestMCPServerIntegration:
    """MCP 서버 통합 테스트"""
    
    def test_server_imports_successfully(self):
        """서버 모듈 임포트 테스트"""
        # main 함수가 존재하는지 확인
        assert callable(main)
    
    @pytest.mark.asyncio
    async def test_server_initializes_all_tools(self):
        """서버가 모든 도구를 초기화하는지 테스트"""
        with patch('src.server.create_server') as mock_create_server:
            mock_server = AsyncMock()
            mock_server.start = AsyncMock()
            mock_server.health_check = AsyncMock(return_value={"status": "healthy"})
            mock_server.list_tools = Mock(return_value=[])
            mock_server.stop = AsyncMock()
            mock_create_server.return_value = mock_server
            
            # 서버 초기화
            await main()
            
            # 서버가 생성되었는지 확인
            mock_create_server.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_server_registers_price_ranking_tool(self):
        """가격 순위 도구 등록 테스트"""
        from src.server import create_server
        
        server = create_server()
        await server.start()
        
        # 도구 목록 확인
        tools = server.list_tools()
        tool_names = [tool['name'] for tool in tools]
        assert 'get_price_change_ranking' in tool_names
        
        await server.stop()
    
    @pytest.mark.asyncio 
    async def test_server_registers_high_low_tool(self):
        """52주 고저가 도구 등록 테스트"""
        from src.server import create_server
        
        server = create_server()
        await server.start()
        
        # 도구 목록 확인
        tools = server.list_tools()
        tool_names = [tool['name'] for tool in tools]
        assert 'get_52week_high_low' in tool_names
        
        await server.stop()
    
    @pytest.mark.asyncio
    async def test_server_registers_limit_tool(self):
        """상한가/하한가 도구 등록 테스트"""
        from src.server import create_server
        
        server = create_server()
        await server.start()
        
        # 도구 목록 확인
        tools = server.list_tools()
        tool_names = [tool['name'] for tool in tools]
        assert 'get_limit_stocks' in tool_names
        
        await server.stop()
    
    @pytest.mark.asyncio
    async def test_tool_schemas_are_valid(self):
        """도구 스키마 유효성 테스트"""
        # 통합 가격 순위 도구
        price_tool = IntegratedPriceRankingTool()
        price_schema = price_tool.get_schema()
        
        assert price_schema["name"] == "get_price_change_ranking"
        assert "parameters" in price_schema
        assert "properties" in price_schema["parameters"]
        
        # 52주 고저가 도구
        high_low_tool = HighLowTool()
        high_low_schema = high_low_tool.get_schema()
        
        assert high_low_schema["name"] == "get_52week_high_low"
        assert "parameters" in high_low_schema
        assert "properties" in high_low_schema["parameters"]
        
        # 상한가/하한가 도구
        limit_tool = LimitTool()
        limit_schema = limit_tool.get_schema()
        
        assert limit_schema["name"] == "get_limit_stocks"
        assert "parameters" in limit_schema
        assert "properties" in limit_schema["parameters"]
    
    @pytest.mark.asyncio
    async def test_tool_execution_integration(self):
        """도구 실행 통합 테스트"""
        # Mock API 클라이언트 설정
        tool = IntegratedPriceRankingTool()
        
        # API 클라이언트 직접 모킹
        mock_api_client = AsyncMock()
        tool.api_client = mock_api_client
        
        # Mock 데이터 설정
        from src.api.models import StockRankingItem, MarketSummary
        mock_api_client.get_ranking_data.return_value = [
            StockRankingItem(
                rank=1,
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                change=1500,
                change_rate=1.95,
                volume=12345678,
                trading_value=78500 * 12345678,
                high=79000,
                low=77000,
                open=77500
            )
        ]
        mock_api_client.get_market_summary.return_value = MarketSummary(
            total_stocks=2500,
            advancing=1200,
            declining=800,
            unchanged=500,
            average_change_rate=1.25
        )
        
        # 도구 실행
        result = await tool.execute(
            ranking_type="TOP_GAINERS",
            market="KOSPI",
            count=1
        )
        
        # 결과 검증
        assert "ranking" in result
        assert len(result["ranking"]) == 1
        assert result["ranking"][0]["stock_code"] == "005930"
    
    def test_server_configuration_validation(self):
        """서버 설정 검증 테스트"""
        from src.config import config
        
        # 필수 설정 확인
        assert hasattr(config, 'api')
        assert hasattr(config.api, 'app_key')
        assert hasattr(config.api, 'app_secret')
        assert hasattr(config.api, 'base_url')
    
    @pytest.mark.asyncio
    async def test_concurrent_tool_execution(self):
        """동시 도구 실행 테스트"""
        import asyncio
        
        # Mock 데이터 설정
        from src.api.models import StockRankingItem, MarketSummary
        mock_data = [
            StockRankingItem(
                rank=1,
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                change=1500,
                change_rate=1.95,
                volume=12345678,
                trading_value=78500 * 12345678,
                high=79000,
                low=77000,
                open=77500
            )
        ]
        
        mock_market_summary = MarketSummary(
            total_stocks=2500,
            advancing=1200,
            declining=800,
            unchanged=500,
            average_change_rate=1.25
        )
        
        # 동시에 여러 도구 실행
        tool1 = IntegratedPriceRankingTool()
        tool2 = IntegratedPriceRankingTool()
        tool3 = IntegratedPriceRankingTool()
        
        # 각 도구의 API 클라이언트 모킹
        for tool in [tool1, tool2, tool3]:
            mock_api_client = AsyncMock()
            mock_api_client.get_ranking_data.return_value = mock_data
            mock_api_client.get_market_summary.return_value = mock_market_summary
            tool.api_client = mock_api_client
        
        tasks = [
            tool1.execute(ranking_type="TOP_GAINERS", market="KOSPI", count=1),
            tool2.execute(ranking_type="TOP_LOSERS", market="KOSDAQ", count=1),
            tool3.execute(ranking_type="MOST_VOLATILE", market="ALL", count=1)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # 모든 결과가 정상적으로 반환되었는지 확인
        assert len(results) == 3
        for result in results:
            assert "ranking" in result
            assert "timestamp" in result


class TestToolRegistration:
    """도구 등록 테스트"""
    
    def test_tool_registry_creation(self):
        """도구 레지스트리 생성 테스트"""
        from src.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        assert registry is not None
        assert hasattr(registry, 'register_tool')
        assert hasattr(registry, 'get_tool')
        assert hasattr(registry, 'list_tools')
    
    def test_tool_registration_process(self):
        """도구 등록 프로세스 테스트"""
        from src.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # 통합 가격 순위 도구 등록
        price_tool = IntegratedPriceRankingTool()
        registry.register_tool("price_ranking", price_tool)
        
        # 등록된 도구 조회
        registered_tool = registry.get_tool("price_ranking")
        assert registered_tool is not None
        assert registered_tool.name == "get_price_change_ranking"
    
    def test_tool_list_retrieval(self):
        """도구 목록 조회 테스트"""
        from src.tools.registry import ToolRegistry
        
        registry = ToolRegistry()
        
        # 여러 도구 등록
        registry.register_tool("price_ranking", IntegratedPriceRankingTool())
        registry.register_tool("high_low", HighLowTool())
        registry.register_tool("limit", LimitTool())
        
        # 도구 목록 조회
        tools = registry.list_tools()
        assert len(tools) == 3
        
        tool_names = [tool.name for tool in tools]
        assert "get_price_change_ranking" in tool_names
        assert "get_52week_high_low" in tool_names
        assert "get_limit_stocks" in tool_names
    
    def test_duplicate_tool_registration_handling(self):
        """중복 도구 등록 처리 테스트"""
        from src.tools.registry import ToolRegistry
        from src.exceptions import ToolExecutionError
        
        registry = ToolRegistry()
        
        # 동일한 키로 도구 등록
        tool1 = IntegratedPriceRankingTool()
        tool2 = IntegratedPriceRankingTool()
        
        registry.register_tool("price_ranking", tool1)
        
        # 중복 등록 시 에러 발생 확인
        with pytest.raises(ToolExecutionError):
            registry.register_tool("price_ranking", tool2)


class TestMCPProtocolCompliance:
    """MCP 프로토콜 준수 테스트"""
    
    def test_tool_schema_format_compliance(self):
        """도구 스키마 형식 준수 테스트"""
        tools = [
            IntegratedPriceRankingTool(),
            HighLowTool(),
            LimitTool()
        ]
        
        for tool in tools:
            schema = tool.get_schema()
            
            # MCP 필수 필드 확인
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            
            # 파라미터 스키마 형식 확인
            params = schema["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params
    
    def test_tool_execution_response_format(self):
        """도구 실행 응답 형식 테스트"""
        async def test_async():
            # Mock 데이터 설정
            from src.api.models import StockRankingItem, MarketSummary
            mock_data = [
                StockRankingItem(
                    rank=1,
                    stock_code="005930",
                    stock_name="삼성전자",
                    current_price=78500,
                    change=1500,
                    change_rate=1.95,
                    volume=12345678,
                    trading_value=78500 * 12345678,
                    high=79000,
                    low=77000,
                    open=77500
                )
            ]
            
            # 도구 실행 및 응답 형식 확인
            tool = IntegratedPriceRankingTool()
            
            # API 클라이언트 모킹
            mock_api_client = AsyncMock()
            mock_api_client.get_ranking_data.return_value = mock_data
            mock_api_client.get_market_summary.return_value = MarketSummary(
                total_stocks=2500,
                advancing=1200,
                declining=800,
                unchanged=500,
                average_change_rate=1.25
            )
            tool.api_client = mock_api_client
            
            result = await tool.execute(
                ranking_type="TOP_GAINERS",
                market="KOSPI",
                count=1
            )
            
            # 응답이 JSON 직렬화 가능한지 확인
            json_result = json.dumps(result, default=str)
            assert json_result is not None
            
            # 기본 구조 확인
            assert isinstance(result, dict)
            assert "timestamp" in result
        
        asyncio.run(test_async())