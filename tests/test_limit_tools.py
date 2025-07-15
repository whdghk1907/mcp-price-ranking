"""
상한가/하한가 도구 테스트
TDD: 상한가/하한가 도구 기능 테스트
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, time
from src.tools.limit_tools import LimitTool
from src.api.models import LimitStockItem, LimitAnalysis
from src.exceptions import DataValidationError, ToolExecutionError


class TestLimitTool:
    """상한가/하한가 도구 테스트"""
    
    @pytest.fixture
    def tool(self):
        """도구 인스턴스"""
        return LimitTool()
    
    def test_tool_creation(self, tool):
        """도구 생성 테스트"""
        assert tool.name == "get_limit_stocks"
        assert "상한가/하한가" in tool.description
        assert tool.api_client is not None
    
    def test_tool_schema(self, tool):
        """도구 스키마 테스트"""
        schema = tool.get_schema()
        
        assert schema["name"] == "get_limit_stocks"
        
        # 필수 파라미터 확인
        props = schema["parameters"]["properties"]
        assert "limit_type" in props
        assert "market" in props
        assert "include_history" in props
        
        # enum 값 확인
        assert "UPPER" in props["limit_type"]["enum"]
        assert "LOWER" in props["limit_type"]["enum"]
        assert "BOTH" in props["limit_type"]["enum"]
    
    def test_parameter_validation(self, tool):
        """파라미터 검증 테스트"""
        # 유효한 파라미터
        assert tool.validate_parameters(
            limit_type="UPPER",
            market="KOSPI",
            include_history=True
        ) is True
        
        # 잘못된 limit_type
        assert tool.validate_parameters(
            limit_type="INVALID",
            market="KOSPI"
        ) is False
        
        # 잘못된 market
        assert tool.validate_parameters(
            limit_type="UPPER",
            market="INVALID"
        ) is False
    
    @pytest.mark.asyncio
    async def test_upper_limit_execution_success(self, tool):
        """상한가 조회 성공 테스트"""
        # Mock 데이터 설정
        mock_upper_stocks = [
            LimitStockItem(
                stock_code="123456",
                stock_name="테스트종목",
                current_price=15600,
                limit_price=15600,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 32, 15),
                volume_at_limit=2345678,
                buy_orders=12345678,
                sell_orders=0,
                consecutive_limits=2,
                unlock_probability=15.3,
                theme=["2차전지", "전기차"]
            )
        ]
        
        mock_analysis = LimitAnalysis(
            upper_count=12,
            lower_count=3,
            upper_unlock_count=2,
            lower_unlock_count=1,
            market_sentiment="VERY_BULLISH",
            total_volume=50000000,
            sector_distribution={"기술": 8, "바이오": 3, "자동차": 1}
        )
        
        # API 메서드 모킹
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=(mock_upper_stocks, [], mock_analysis)
        )
        
        # 실행
        result = await tool.execute(
            limit_type="UPPER",
            market="KOSPI",
            include_history=True
        )
        
        # 결과 검증
        assert result["limit_type"] == "UPPER"
        assert result["market"] == "KOSPI"
        assert result["include_history"] is True
        assert len(result["upper_limit"]) == 1
        assert result["upper_limit"][0]["stock_code"] == "123456"
        assert result["upper_limit"][0]["limit_type"] == "UPPER"
        assert result["upper_limit"][0]["consecutive_limits"] == 2
        assert result["summary"]["upper_count"] == 12
        assert result["summary"]["market_sentiment"] == "VERY_BULLISH"
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_both_limit_execution(self, tool):
        """상한가/하한가 모두 조회 테스트"""
        mock_upper_stocks = [
            LimitStockItem(
                stock_code="123456",
                stock_name="상한가종목",
                current_price=15600,
                limit_price=15600,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 32, 15),
                consecutive_limits=1
            )
        ]
        
        mock_lower_stocks = [
            LimitStockItem(
                stock_code="789012",
                stock_name="하한가종목",
                current_price=8400,
                limit_price=8400,
                previous_close=12000,
                limit_type="LOWER",
                hit_time=time(10, 15, 30),
                consecutive_limits=1
            )
        ]
        
        mock_analysis = LimitAnalysis(
            upper_count=5,
            lower_count=3,
            upper_unlock_count=1,
            lower_unlock_count=0,
            market_sentiment="BULLISH"
        )
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=(mock_upper_stocks, mock_lower_stocks, mock_analysis)
        )
        
        result = await tool.execute(limit_type="BOTH", market="ALL")
        
        assert result["limit_type"] == "BOTH"
        assert len(result["upper_limit"]) == 1
        assert len(result["lower_limit"]) == 1
        assert result["upper_limit"][0]["limit_type"] == "UPPER"
        assert result["lower_limit"][0]["limit_type"] == "LOWER"
    
    @pytest.mark.asyncio
    async def test_consecutive_limits_analysis(self, tool):
        """연속 상한가 분석 테스트"""
        mock_stocks = [
            LimitStockItem(
                stock_code="123456",
                stock_name="연속상한가종목",
                current_price=15600,
                limit_price=15600,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 0, 0),
                consecutive_limits=5,  # 5일 연속
                recent_limits=[
                    {"date": "2024-01-10", "type": "UPPER"},
                    {"date": "2024-01-09", "type": "UPPER"},
                    {"date": "2024-01-08", "type": "UPPER"},
                    {"date": "2024-01-05", "type": "UPPER"},
                    {"date": "2024-01-04", "type": "UPPER"}
                ]
            )
        ]
        
        mock_analysis = LimitAnalysis(
            upper_count=1,
            lower_count=0,
            upper_unlock_count=0,
            lower_unlock_count=0,
            market_sentiment="VERY_BULLISH"
        )
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=(mock_stocks, [], mock_analysis)
        )
        
        result = await tool.execute(limit_type="UPPER", market="ALL", include_history=True)
        
        stock = result["upper_limit"][0]
        assert stock["consecutive_limits"] == 5
        assert len(stock["recent_limits"]) == 5
        assert stock["recent_limits"][0]["date"] == "2024-01-10"
        assert "insights" in result
        assert any("연속" in insight for insight in result["insights"])
    
    @pytest.mark.asyncio
    async def test_unlock_probability_calculation(self, tool):
        """상한가 해제 확률 계산 테스트"""
        mock_stocks = [
            LimitStockItem(
                stock_code="123456",
                stock_name="테스트종목",
                current_price=15600,
                limit_price=15600,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 0, 0),
                volume_at_limit=10000000,
                buy_orders=20000000,
                sell_orders=0,
                consecutive_limits=1,
                unlock_probability=25.5
            )
        ]
        
        mock_analysis = LimitAnalysis(
            upper_count=1,
            lower_count=0,
            upper_unlock_count=0,
            lower_unlock_count=0,
            market_sentiment="BULLISH"
        )
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=(mock_stocks, [], mock_analysis)
        )
        
        result = await tool.execute(limit_type="UPPER", market="ALL")
        
        stock = result["upper_limit"][0]
        assert stock["unlock_probability"] == 25.5
        assert stock["buy_orders"] > stock["sell_orders"]
        assert "insights" in result
    
    @pytest.mark.asyncio
    async def test_theme_analysis(self, tool):
        """테마 분석 테스트"""
        mock_stocks = [
            LimitStockItem(
                stock_code="123456",
                stock_name="2차전지종목",
                current_price=15600,
                limit_price=15600,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 0, 0),
                theme=["2차전지", "전기차"]
            ),
            LimitStockItem(
                stock_code="789012",
                stock_name="바이오종목",
                current_price=8400,
                limit_price=8400,
                previous_close=12000,
                limit_type="UPPER",
                hit_time=time(9, 5, 0),
                theme=["바이오", "신약"]
            )
        ]
        
        mock_analysis = LimitAnalysis(
            upper_count=2,
            lower_count=0,
            upper_unlock_count=0,
            lower_unlock_count=0,
            market_sentiment="BULLISH"
        )
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=(mock_stocks, [], mock_analysis)
        )
        
        result = await tool.execute(limit_type="UPPER", market="ALL")
        
        assert len(result["upper_limit"]) == 2
        assert result["upper_limit"][0]["theme"] == ["2차전지", "전기차"]
        assert result["upper_limit"][1]["theme"] == ["바이오", "신약"]
        assert "theme_analysis" in result
        assert result["theme_analysis"]["2차전지"] == 1
        assert result["theme_analysis"]["바이오"] == 1
    
    @pytest.mark.asyncio
    async def test_parameter_validation_error(self, tool):
        """파라미터 검증 오류 테스트"""
        with pytest.raises(DataValidationError):
            await tool.execute(
                limit_type="INVALID_TYPE",
                market="KOSPI"
            )
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, tool):
        """API 오류 처리 테스트"""
        from src.exceptions import APIError
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            side_effect=APIError("API request failed")
        )
        
        with pytest.raises(ToolExecutionError):
            await tool.execute(
                limit_type="UPPER",
                market="KOSPI"
            )
    
    @pytest.mark.asyncio
    async def test_empty_result_handling(self, tool):
        """빈 결과 처리 테스트"""
        mock_analysis = LimitAnalysis(
            upper_count=0,
            lower_count=0,
            upper_unlock_count=0,
            lower_unlock_count=0,
            market_sentiment="NEUTRAL"
        )
        
        tool.api_client.get_limit_stocks_data = AsyncMock(
            return_value=([], [], mock_analysis)
        )
        
        result = await tool.execute(limit_type="UPPER", market="KOSPI")
        
        assert len(result["upper_limit"]) == 0
        assert result["summary"]["upper_count"] == 0
        assert result["summary"]["market_sentiment"] == "NEUTRAL"
        assert "상한가 종목이 없습니다" in result["insights"]


class TestLimitStockItem:
    """LimitStockItem 모델 테스트"""
    
    def test_limit_stock_item_creation(self):
        """LimitStockItem 생성 테스트"""
        item = LimitStockItem(
            stock_code="123456",
            stock_name="테스트종목",
            current_price=15600,
            limit_price=15600,
            previous_close=12000,
            limit_type="UPPER",
            hit_time=time(9, 32, 15),
            consecutive_limits=2
        )
        
        assert item.stock_code == "123456"
        assert item.stock_name == "테스트종목"
        assert item.current_price == 15600
        assert item.limit_type == "UPPER"
        assert item.consecutive_limits == 2
    
    def test_limit_rate_calculation(self):
        """상한가율 계산 테스트"""
        item = LimitStockItem(
            stock_code="123456",
            stock_name="테스트종목",
            current_price=15600,
            limit_price=15600,
            previous_close=12000,
            limit_type="UPPER",
            hit_time=time(9, 0, 0)
        )
        
        # 상한가율 계산: (15600 - 12000) / 12000 * 100 = 30%
        assert abs(item.limit_rate - 30.0) < 0.01
    
    def test_volume_pressure_calculation(self):
        """거래량 압박 계산 테스트"""
        item = LimitStockItem(
            stock_code="123456",
            stock_name="테스트종목",
            current_price=15600,
            limit_price=15600,
            previous_close=12000,
            limit_type="UPPER",
            hit_time=time(9, 0, 0),
            buy_orders=20000000,
            sell_orders=500000
        )
        
        # 매수 압박: 20000000 / (20000000 + 500000) * 100 = 97.56%
        assert abs(item.volume_pressure - 97.56) < 0.01
    
    def test_to_dict_conversion(self):
        """딕셔너리 변환 테스트"""
        item = LimitStockItem(
            stock_code="123456",
            stock_name="테스트종목",
            current_price=15600,
            limit_price=15600,
            previous_close=12000,
            limit_type="UPPER",
            hit_time=time(9, 32, 15),
            consecutive_limits=2,
            theme=["2차전지", "전기차"]
        )
        
        result = item.to_dict()
        
        assert result["stock_code"] == "123456"
        assert result["stock_name"] == "테스트종목"
        assert result["current_price"] == 15600
        assert result["limit_type"] == "UPPER"
        assert result["consecutive_limits"] == 2
        assert result["theme"] == ["2차전지", "전기차"]
        assert "limit_rate" in result
        assert "hit_time" in result


class TestLimitAnalysis:
    """LimitAnalysis 모델 테스트"""
    
    def test_analysis_creation(self):
        """분석 결과 생성 테스트"""
        analysis = LimitAnalysis(
            upper_count=15,
            lower_count=5,
            upper_unlock_count=3,
            lower_unlock_count=1,
            market_sentiment="BULLISH"
        )
        
        assert analysis.upper_count == 15
        assert analysis.lower_count == 5
        assert analysis.upper_unlock_count == 3
        assert analysis.lower_unlock_count == 1
        assert analysis.market_sentiment == "BULLISH"
    
    def test_limit_ratio_calculation(self):
        """상한가 비율 계산 테스트"""
        analysis = LimitAnalysis(
            upper_count=20,
            lower_count=5,
            upper_unlock_count=2,
            lower_unlock_count=1,
            market_sentiment="BULLISH"
        )
        
        # 상한가 비율: 20 / (20 + 5) = 0.8
        assert abs(analysis.limit_ratio - 0.8) < 0.01
    
    def test_market_sentiment_strength(self):
        """시장 심리 강도 테스트"""
        analysis = LimitAnalysis(
            upper_count=50,
            lower_count=2,
            upper_unlock_count=5,
            lower_unlock_count=0,
            market_sentiment="VERY_BULLISH"
        )
        
        assert analysis.market_sentiment == "VERY_BULLISH"
        assert analysis.sentiment_strength == "VERY_STRONG"
    
    def test_to_dict_conversion(self):
        """딕셔너리 변환 테스트"""
        analysis = LimitAnalysis(
            upper_count=12,
            lower_count=3,
            upper_unlock_count=2,
            lower_unlock_count=1,
            market_sentiment="BULLISH"
        )
        
        result = analysis.to_dict()
        
        assert result["upper_count"] == 12
        assert result["lower_count"] == 3
        assert result["upper_unlock_count"] == 2
        assert result["lower_unlock_count"] == 1
        assert result["market_sentiment"] == "BULLISH"
        assert "limit_ratio" in result
        assert "sentiment_strength" in result