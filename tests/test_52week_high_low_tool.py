"""
52주 신고가/신저가 도구 테스트
TDD: 52주 고저가 도구 기능 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta
from src.tools.high_low_tools import HighLowTool
from src.api.models import HighLowStockItem, HighLowAnalysis
from src.exceptions import DataValidationError, ToolExecutionError


class TestHighLowTool:
    """52주 신고가/신저가 도구 테스트"""
    
    @pytest.fixture
    def tool(self):
        """도구 인스턴스"""
        return HighLowTool()
    
    def test_tool_creation(self, tool):
        """도구 생성 테스트"""
        assert tool.name == "get_52week_high_low"
        assert "52주 신고가/신저가" in tool.description
        assert tool.api_client is not None
    
    def test_tool_schema(self, tool):
        """도구 스키마 테스트"""
        schema = tool.get_schema()
        
        assert schema["name"] == "get_52week_high_low"
        
        # 필수 파라미터 확인
        props = schema["parameters"]["properties"]
        assert "type" in props
        assert "market" in props
        assert "count" in props
        assert "breakthrough_only" in props
        
        # enum 값 확인
        assert "HIGH" in props["type"]["enum"]
        assert "LOW" in props["type"]["enum"]
        assert "BOTH" in props["type"]["enum"]
    
    def test_parameter_validation(self, tool):
        """파라미터 검증 테스트"""
        # 유효한 파라미터
        assert tool.validate_parameters(
            type="HIGH",
            market="KOSPI",
            count=10,
            breakthrough_only=True
        ) is True
        
        # 잘못된 type
        assert tool.validate_parameters(
            type="INVALID",
            market="KOSPI",
            count=10
        ) is False
        
        # 잘못된 count
        assert tool.validate_parameters(
            type="HIGH",
            market="KOSPI",
            count=0
        ) is False
        
        assert tool.validate_parameters(
            type="HIGH",
            market="KOSPI",
            count=1000
        ) is False
    
    @pytest.mark.asyncio
    async def test_high_low_execution_success(self, tool):
        """52주 고저가 조회 성공 테스트"""
        # Mock 데이터 설정
        mock_high_stocks = [
            HighLowStockItem(
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                week_52_high=78500,
                week_52_low=58000,
                week_52_high_date=datetime.now().date(),
                week_52_low_date=datetime.now().date() - timedelta(days=100),
                is_new_high=True,
                is_new_low=False,
                volume=12345678,
                volume_ratio=245.6,
                momentum_score=8.5,
                sector="반도체"
            )
        ]
        
        mock_analysis = HighLowAnalysis(
            new_highs_count=15,
            new_lows_count=8,
            high_low_ratio=1.875,
            market_breadth="POSITIVE",
            breakthrough_stocks=mock_high_stocks,
            resistance_stocks=[]
        )
        
        # API 메서드 모킹
        tool.api_client.get_52week_high_low_data = AsyncMock(
            return_value=(mock_high_stocks, [], mock_analysis)
        )
        
        # 실행
        result = await tool.execute(
            type="HIGH",
            market="KOSPI",
            count=10,
            breakthrough_only=True
        )
        
        # 결과 검증
        assert result["type"] == "HIGH"
        assert result["market"] == "KOSPI"
        assert result["breakthrough_only"] is True
        assert len(result["high_stocks"]) == 1
        assert result["high_stocks"][0]["stock_code"] == "005930"
        assert result["high_stocks"][0]["is_new_high"] is True
        assert result["statistics"]["new_highs_count"] == 15
        assert result["statistics"]["high_low_ratio"] == 1.875
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_both_high_low_execution(self, tool):
        """고저가 모두 조회 테스트"""
        mock_high_stocks = [
            HighLowStockItem(
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                week_52_high=78500,
                week_52_low=58000,
                week_52_high_date=datetime.now().date(),
                week_52_low_date=datetime.now().date() - timedelta(days=100),
                is_new_high=True,
                is_new_low=False
            )
        ]
        
        mock_low_stocks = [
            HighLowStockItem(
                stock_code="123456",
                stock_name="테스트종목",
                current_price=1200,
                week_52_high=3500,
                week_52_low=1200,
                week_52_high_date=datetime.now().date() - timedelta(days=200),
                week_52_low_date=datetime.now().date(),
                is_new_high=False,
                is_new_low=True
            )
        ]
        
        mock_analysis = HighLowAnalysis(
            new_highs_count=10,
            new_lows_count=5,
            high_low_ratio=2.0,
            market_breadth="POSITIVE"
        )
        
        tool.api_client.get_52week_high_low_data = AsyncMock(
            return_value=(mock_high_stocks, mock_low_stocks, mock_analysis)
        )
        
        result = await tool.execute(type="BOTH", market="ALL", count=20)
        
        assert result["type"] == "BOTH"
        assert len(result["high_stocks"]) == 1
        assert len(result["low_stocks"]) == 1
        assert result["high_stocks"][0]["is_new_high"] is True
        assert result["low_stocks"][0]["is_new_low"] is True
    
    @pytest.mark.asyncio
    async def test_breakthrough_filtering(self, tool):
        """돌파 필터링 테스트"""
        # 돌파 종목과 비돌파 종목 혼합 데이터
        mock_stocks = [
            HighLowStockItem(
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                week_52_high=78500,
                week_52_low=58000,
                week_52_high_date=datetime.now().date(),
                week_52_low_date=datetime.now().date() - timedelta(days=100),
                is_new_high=True,  # 오늘 돌파
                is_new_low=False
            ),
            HighLowStockItem(
                stock_code="000660",
                stock_name="SK하이닉스",
                current_price=125000,
                week_52_high=130000,
                week_52_low=90000,
                week_52_high_date=datetime.now().date() - timedelta(days=30),
                week_52_low_date=datetime.now().date() - timedelta(days=150),
                is_new_high=False,  # 오늘 돌파 아님
                is_new_low=False
            )
        ]
        
        mock_analysis = HighLowAnalysis(
            new_highs_count=1,
            new_lows_count=0,
            high_low_ratio=float('inf'),
            market_breadth="POSITIVE"
        )
        
        tool.api_client.get_52week_high_low_data = AsyncMock(
            return_value=(mock_stocks, [], mock_analysis)
        )
        
        # breakthrough_only=True로 실행
        result = await tool.execute(
            type="HIGH",
            market="ALL",
            count=20,
            breakthrough_only=True
        )
        
        # 돌파 종목만 포함되어야 함
        assert len(result["high_stocks"]) == 1
        assert result["high_stocks"][0]["stock_code"] == "005930"
        assert result["high_stocks"][0]["is_new_high"] is True
    
    @pytest.mark.asyncio
    async def test_parameter_validation_error(self, tool):
        """파라미터 검증 오류 테스트"""
        with pytest.raises(DataValidationError):
            await tool.execute(
                type="INVALID_TYPE",
                market="KOSPI",
                count=10
            )
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, tool):
        """API 오류 처리 테스트"""
        from src.exceptions import APIError
        
        tool.api_client.get_52week_high_low_data = AsyncMock(
            side_effect=APIError("API request failed")
        )
        
        with pytest.raises(ToolExecutionError):
            await tool.execute(
                type="HIGH",
                market="KOSPI",
                count=10
            )
    
    @pytest.mark.asyncio
    async def test_empty_result_handling(self, tool):
        """빈 결과 처리 테스트"""
        mock_analysis = HighLowAnalysis(
            new_highs_count=0,
            new_lows_count=0,
            high_low_ratio=0.0,
            market_breadth="NEUTRAL"
        )
        
        tool.api_client.get_52week_high_low_data = AsyncMock(
            return_value=([], [], mock_analysis)
        )
        
        result = await tool.execute(type="HIGH", market="KOSPI", count=10)
        
        assert len(result["high_stocks"]) == 0
        assert result["statistics"]["new_highs_count"] == 0
        assert result["statistics"]["market_breadth"] == "NEUTRAL"


class TestHighLowStockItem:
    """HighLowStockItem 모델 테스트"""
    
    def test_high_low_stock_item_creation(self):
        """HighLowStockItem 생성 테스트"""
        item = HighLowStockItem(
            stock_code="005930",
            stock_name="삼성전자",
            current_price=78500,
            week_52_high=78500,
            week_52_low=58000,
            week_52_high_date=datetime.now().date(),
            week_52_low_date=datetime.now().date() - timedelta(days=100),
            is_new_high=True,
            is_new_low=False
        )
        
        assert item.stock_code == "005930"
        assert item.stock_name == "삼성전자"
        assert item.current_price == 78500
        assert item.is_new_high is True
        assert item.is_new_low is False
    
    def test_high_low_calculations(self):
        """고저가 계산 테스트"""
        item = HighLowStockItem(
            stock_code="005930",
            stock_name="삼성전자",
            current_price=70000,
            week_52_high=80000,
            week_52_low=60000,
            week_52_high_date=datetime.now().date(),
            week_52_low_date=datetime.now().date() - timedelta(days=100),
            is_new_high=False,
            is_new_low=False
        )
        
        # 고점 대비 하락률 계산
        assert abs(item.high_breakthrough_rate - (-12.5)) < 0.01
        
        # 저점 대비 상승률 계산
        assert abs(item.low_breakthrough_rate - 16.67) < 0.01
    
    def test_to_dict_conversion(self):
        """딕셔너리 변환 테스트"""
        item = HighLowStockItem(
            stock_code="005930",
            stock_name="삼성전자",
            current_price=78500,
            week_52_high=78500,
            week_52_low=58000,
            week_52_high_date=datetime.now().date(),
            week_52_low_date=datetime.now().date() - timedelta(days=100),
            is_new_high=True,
            is_new_low=False
        )
        
        result = item.to_dict()
        
        assert result["stock_code"] == "005930"
        assert result["stock_name"] == "삼성전자"
        assert result["current_price"] == 78500
        assert result["is_new_high"] is True
        assert result["is_new_low"] is False
        assert "high_breakthrough_rate" in result
        assert "low_breakthrough_rate" in result


class TestHighLowAnalysis:
    """HighLowAnalysis 모델 테스트"""
    
    def test_analysis_creation(self):
        """분석 결과 생성 테스트"""
        analysis = HighLowAnalysis(
            new_highs_count=20,
            new_lows_count=10,
            high_low_ratio=2.0,
            market_breadth="POSITIVE"
        )
        
        assert analysis.new_highs_count == 20
        assert analysis.new_lows_count == 10
        assert analysis.high_low_ratio == 2.0
        assert analysis.market_breadth == "POSITIVE"
    
    def test_market_breadth_calculation(self):
        """시장 폭 계산 테스트"""
        # 매우 긍정적
        analysis = HighLowAnalysis(
            new_highs_count=50,
            new_lows_count=5,
            high_low_ratio=10.0,
            market_breadth="VERY_POSITIVE"
        )
        assert analysis.market_breadth == "VERY_POSITIVE"
        
        # 중립
        analysis = HighLowAnalysis(
            new_highs_count=10,
            new_lows_count=10,
            high_low_ratio=1.0,
            market_breadth="NEUTRAL"
        )
        assert analysis.market_breadth == "NEUTRAL"
    
    def test_to_dict_conversion(self):
        """딕셔너리 변환 테스트"""
        analysis = HighLowAnalysis(
            new_highs_count=15,
            new_lows_count=8,
            high_low_ratio=1.875,
            market_breadth="POSITIVE"
        )
        
        result = analysis.to_dict()
        
        assert result["new_highs_count"] == 15
        assert result["new_lows_count"] == 8
        assert result["high_low_ratio"] == 1.875
        assert result["market_breadth"] == "POSITIVE"