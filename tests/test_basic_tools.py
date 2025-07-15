"""
기본 도구 클래스 테스트
TDD: 실제 사용될 도구들의 기본 구조 테스트
"""
import pytest
from datetime import datetime
from src.tools.price_ranking_tools import PriceRankingTool
from src.tools.basic_tools import HealthCheckTool, InfoTool
from src.exceptions import ToolExecutionError, DataValidationError


class TestHealthCheckTool:
    """헬스체크 도구 테스트"""
    
    @pytest.fixture
    def health_tool(self):
        """헬스체크 도구 인스턴스"""
        return HealthCheckTool()
    
    def test_health_tool_creation(self, health_tool):
        """헬스체크 도구 생성 테스트"""
        assert health_tool.name == "health_check"
        assert "서버 상태" in health_tool.description
    
    @pytest.mark.asyncio
    async def test_health_check_execution(self, health_tool):
        """헬스체크 실행 테스트"""
        result = await health_tool.execute()
        
        assert result["status"] == "healthy"
        assert "timestamp" in result
        assert "uptime" in result
        assert "version" in result
        assert result["version"] == "0.1.0"
    
    def test_health_check_schema(self, health_tool):
        """헬스체크 스키마 테스트"""
        schema = health_tool.get_schema()
        
        assert schema["name"] == "health_check"
        assert schema["parameters"]["type"] == "object"
        # 헬스체크는 파라미터가 없음
        assert len(schema["parameters"]["properties"]) == 0


class TestInfoTool:
    """정보 도구 테스트"""
    
    @pytest.fixture
    def info_tool(self):
        """정보 도구 인스턴스"""
        return InfoTool()
    
    def test_info_tool_creation(self, info_tool):
        """정보 도구 생성 테스트"""
        assert info_tool.name == "get_server_info"
        assert "서버 정보" in info_tool.description
    
    @pytest.mark.asyncio
    async def test_info_execution(self, info_tool):
        """정보 도구 실행 테스트"""
        result = await info_tool.execute()
        
        assert "server_name" in result
        assert "available_tools" in result
        assert "supported_markets" in result
        assert "api_version" in result
        
        # 지원 마켓 확인
        markets = result["supported_markets"]
        assert "KOSPI" in markets
        assert "KOSDAQ" in markets
        assert "ALL" in markets
    
    @pytest.mark.asyncio
    async def test_info_with_detail(self, info_tool):
        """상세 정보 조회 테스트"""
        result = await info_tool.execute(detail=True)
        
        assert "server_name" in result
        assert "available_tools" in result
        assert "tool_schemas" in result  # 상세 정보에는 스키마 포함
        assert len(result["tool_schemas"]) >= 0
    
    def test_info_schema(self, info_tool):
        """정보 도구 스키마 테스트"""
        schema = info_tool.get_schema()
        
        assert schema["name"] == "get_server_info"
        assert "detail" in schema["parameters"]["properties"]
        assert schema["parameters"]["properties"]["detail"]["type"] == "boolean"


class TestPriceRankingTool:
    """가격 순위 도구 테스트"""
    
    @pytest.fixture
    def ranking_tool(self):
        """가격 순위 도구 인스턴스"""
        return PriceRankingTool()
    
    def test_ranking_tool_creation(self, ranking_tool):
        """가격 순위 도구 생성 테스트"""
        assert ranking_tool.name == "get_price_change_ranking"
        assert "가격 변동률" in ranking_tool.description
    
    def test_ranking_tool_schema(self, ranking_tool):
        """가격 순위 도구 스키마 테스트"""
        schema = ranking_tool.get_schema()
        
        assert schema["name"] == "get_price_change_ranking"
        
        # 필수 파라미터 확인
        props = schema["parameters"]["properties"]
        assert "ranking_type" in props
        assert "market" in props
        assert "count" in props
        
        # 타입 확인
        assert props["ranking_type"]["type"] == "string"
        assert props["market"]["type"] == "string"
        assert props["count"]["type"] == "integer"
        
        # enum 값 확인
        assert "TOP_GAINERS" in props["ranking_type"]["enum"]
        assert "TOP_LOSERS" in props["ranking_type"]["enum"]
        assert "MOST_VOLATILE" in props["ranking_type"]["enum"]
    
    def test_parameter_validation(self, ranking_tool):
        """파라미터 검증 테스트"""
        # 유효한 파라미터
        assert ranking_tool.validate_parameters(
            ranking_type="TOP_GAINERS",
            market="KOSPI",
            count=10
        ) is True
        
        # 잘못된 ranking_type
        assert ranking_tool.validate_parameters(
            ranking_type="INVALID_TYPE",
            market="KOSPI",
            count=10
        ) is False
        
        # 잘못된 market
        assert ranking_tool.validate_parameters(
            ranking_type="TOP_GAINERS",
            market="INVALID_MARKET",
            count=10
        ) is False
        
        # 잘못된 count (너무 큰 값)
        assert ranking_tool.validate_parameters(
            ranking_type="TOP_GAINERS",
            market="KOSPI",
            count=1000
        ) is False
    
    @pytest.mark.asyncio
    async def test_ranking_tool_execution_mock(self, ranking_tool):
        """가격 순위 도구 실행 테스트 (모킹)"""
        # 실제 API 없이 기본 구조 테스트
        try:
            result = await ranking_tool.execute(
                ranking_type="TOP_GAINERS",
                market="KOSPI",
                count=5
            )
            
            # 기본 구조 확인
            assert "timestamp" in result
            assert "ranking_type" in result
            assert "market" in result
            assert "ranking" in result
            assert result["ranking_type"] == "TOP_GAINERS"
            assert result["market"] == "KOSPI"
            
        except Exception as e:
            # API 클라이언트가 구현되지 않았으므로 예외 발생 예상
            assert "API client not implemented" in str(e) or "not implemented" in str(e)
    
    @pytest.mark.asyncio
    async def test_ranking_tool_validation_error(self, ranking_tool):
        """잘못된 파라미터로 도구 실행 시 에러 테스트"""
        with pytest.raises(DataValidationError):
            await ranking_tool.execute(
                ranking_type="INVALID_TYPE",
                market="KOSPI",
                count=10
            )


class TestToolIntegration:
    """도구 통합 테스트"""
    
    def test_all_tools_creation(self):
        """모든 기본 도구 생성 테스트"""
        tools = [
            HealthCheckTool(),
            InfoTool(),
            PriceRankingTool()
        ]
        
        # 모든 도구가 올바르게 생성되는지 확인
        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert hasattr(tool, 'execute')
            assert hasattr(tool, 'get_schema')
    
    def test_tool_names_unique(self):
        """도구 이름 중복 확인"""
        tools = [
            HealthCheckTool(),
            InfoTool(),
            PriceRankingTool()
        ]
        
        names = [tool.name for tool in tools]
        assert len(names) == len(set(names))  # 중복 없음
    
    def test_all_tool_schemas(self):
        """모든 도구 스키마 유효성 테스트"""
        tools = [
            HealthCheckTool(),
            InfoTool(),
            PriceRankingTool()
        ]
        
        for tool in tools:
            schema = tool.get_schema()
            
            # 필수 필드 확인
            assert "name" in schema
            assert "description" in schema
            assert "parameters" in schema
            
            # 파라미터 스키마 구조 확인
            params = schema["parameters"]
            assert "type" in params
            assert params["type"] == "object"
            assert "properties" in params