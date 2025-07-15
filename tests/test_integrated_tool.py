"""
통합 도구 테스트
TDD: API 클라이언트와 도구가 통합된 완전한 기능 테스트
"""
import pytest
from unittest.mock import Mock, patch, AsyncMock
from src.tools.integrated_price_tool import IntegratedPriceRankingTool
from src.api.client import KoreaInvestmentAPIClient
from src.api.models import StockRankingItem
from src.exceptions import APIError, DataValidationError, ToolExecutionError


class TestIntegratedPriceRankingTool:
    """통합 가격 순위 도구 테스트"""
    
    @pytest.fixture
    def tool(self):
        """통합 도구 인스턴스"""
        return IntegratedPriceRankingTool()
    
    def test_tool_creation(self, tool):
        """도구 생성 테스트"""
        assert tool.name == "get_price_change_ranking"
        assert tool.api_client is not None
        assert isinstance(tool.api_client, KoreaInvestmentAPIClient)
    
    @pytest.mark.asyncio
    async def test_tool_with_mock_api_success(self, tool):
        """API 모킹으로 성공 케이스 테스트"""
        # Mock API 클라이언트 설정
        mock_ranking_data = [
            StockRankingItem(
                rank=1,
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,
                change=1500,
                change_rate=1.95,
                volume=12345678,
                trading_value=967827730000,
                high=79000,
                low=77000,
                open=77500,
                sector="전기전자"
            ),
            StockRankingItem(
                rank=2,
                stock_code="000660",
                stock_name="SK하이닉스",
                current_price=125000,
                change=2000,
                change_rate=1.63,
                volume=8765432,
                trading_value=1095679000000,
                high=126000,
                low=123000,
                open=124000,
                sector="반도체"
            )
        ]
        
        # API 클라이언트 메서드 모킹
        tool.api_client.get_ranking_data = AsyncMock(return_value=mock_ranking_data)
        tool.api_client.get_market_summary = AsyncMock(return_value=Mock(
            to_dict=Mock(return_value={
                "total_stocks": 2500,
                "advancing": 1200,
                "declining": 800,
                "unchanged": 500,
                "average_change_rate": 1.25
            })
        ))
        
        # 도구 실행
        result = await tool.execute(
            ranking_type="TOP_GAINERS",
            market="KOSPI",
            count=2
        )
        
        # 결과 검증
        assert result["ranking_type"] == "TOP_GAINERS"
        assert result["market"] == "KOSPI"
        assert len(result["ranking"]) == 2
        assert result["ranking"][0]["stock_code"] == "005930"
        assert result["ranking"][0]["stock_name"] == "삼성전자"
        assert result["ranking"][1]["stock_code"] == "000660"
        assert result["ranking"][1]["stock_name"] == "SK하이닉스"
        assert "summary" in result
        assert "timestamp" in result
    
    @pytest.mark.asyncio
    async def test_tool_with_api_error(self, tool):
        """API 에러 처리 테스트"""
        # API 클라이언트에서 에러 발생 모킹
        tool.api_client.get_ranking_data = AsyncMock(
            side_effect=APIError("API request failed", status_code=500)
        )
        
        # 도구 실행 시 에러 발생해야 함
        with pytest.raises(ToolExecutionError):
            await tool.execute(
                ranking_type="TOP_GAINERS",
                market="KOSPI",
                count=10
            )
    
    @pytest.mark.asyncio
    async def test_tool_parameter_validation(self, tool):
        """파라미터 검증 테스트"""
        # 잘못된 파라미터로 실행
        with pytest.raises(DataValidationError):
            await tool.execute(
                ranking_type="INVALID_TYPE",
                market="KOSPI",
                count=10
            )
    
    @pytest.mark.asyncio
    async def test_tool_with_filters(self, tool):
        """필터 적용 테스트"""
        # Mock 데이터 (일부는 필터 조건에 맞지 않음)
        mock_ranking_data = [
            StockRankingItem(
                rank=1,
                stock_code="005930",
                stock_name="삼성전자",
                current_price=78500,  # 필터 통과 (min_price=50000)
                change=1500,
                change_rate=1.95,
                volume=12345678,  # 필터 통과 (min_volume=1000000)
                trading_value=967827730000,
                high=79000,
                low=77000,
                open=77500
            ),
            StockRankingItem(
                rank=2,
                stock_code="123456",
                stock_name="테스트종목",
                current_price=30000,  # 필터 통과 안함 (min_price=50000)
                change=500,
                change_rate=1.69,
                volume=500000,  # 필터 통과 안함 (min_volume=1000000)
                trading_value=15000000000,
                high=30500,
                low=29500,
                open=30000
            )
        ]
        
        tool.api_client.get_ranking_data = AsyncMock(return_value=mock_ranking_data)
        tool.api_client.get_market_summary = AsyncMock(return_value=Mock(
            to_dict=Mock(return_value={"total_stocks": 2500})
        ))
        
        # 필터 적용하여 실행
        result = await tool.execute(
            ranking_type="TOP_GAINERS",
            market="ALL",
            count=10,
            min_price=50000,
            min_volume=1000000
        )
        
        # 필터링된 결과 확인
        assert len(result["ranking"]) == 1
        assert result["ranking"][0]["stock_code"] == "005930"
        assert result["filters"]["min_price"] == 50000
        assert result["filters"]["min_volume"] == 1000000
    
    @pytest.mark.asyncio
    async def test_tool_cleanup(self, tool):
        """도구 정리 테스트"""
        # API 클라이언트 close 메서드 모킹
        tool.api_client.close = AsyncMock()
        
        # 도구 정리
        await tool.cleanup()
        
        # API 클라이언트 정리 확인
        tool.api_client.close.assert_called_once()


class TestToolIntegrationWithRealAPI:
    """실제 API 키를 사용한 통합 테스트 (옵셔널)"""
    
    @pytest.mark.skipif(
        True,  # 실제 API 통합 테스트는 기본적으로 스킵
        reason="Integration tests require real API credentials"
    )
    @pytest.mark.asyncio
    async def test_real_api_integration(self):
        """실제 API와의 통합 테스트"""
        # 실제 API 키가 있는 경우에만 실행
        tool = IntegratedPriceRankingTool()
        
        try:
            result = await tool.execute(
                ranking_type="TOP_GAINERS",
                market="KOSPI",
                count=5
            )
            
            # 기본 구조 확인
            assert "ranking" in result
            assert "timestamp" in result
            assert "summary" in result
            
            # 실제 데이터 확인
            if result["ranking"]:
                first_item = result["ranking"][0]
                assert "stock_code" in first_item
                assert "stock_name" in first_item
                assert "current_price" in first_item
                assert "change_rate" in first_item
                
        except APIError as e:
            pytest.skip(f"API integration test failed: {str(e)}")
        finally:
            await tool.cleanup()


class TestToolPerformance:
    """도구 성능 테스트"""
    
    @pytest.mark.asyncio
    async def test_tool_response_time(self):
        """도구 응답 시간 테스트"""
        import time
        
        tool = IntegratedPriceRankingTool()
        
        # Mock API 설정
        tool.api_client.get_ranking_data = AsyncMock(return_value=[])
        tool.api_client.get_market_summary = AsyncMock(return_value=Mock(
            to_dict=Mock(return_value={"total_stocks": 0})
        ))
        
        start_time = time.time()
        
        await tool.execute(
            ranking_type="TOP_GAINERS",
            market="ALL",
            count=10
        )
        
        end_time = time.time()
        response_time = end_time - start_time
        
        # 응답 시간이 1초 이내여야 함
        assert response_time < 1.0
        
        await tool.cleanup()
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """동시 요청 테스트"""
        import asyncio
        
        tool = IntegratedPriceRankingTool()
        
        # Mock API 설정
        tool.api_client.get_ranking_data = AsyncMock(return_value=[])
        tool.api_client.get_market_summary = AsyncMock(return_value=Mock(
            to_dict=Mock(return_value={"total_stocks": 0})
        ))
        
        # 동시 요청 실행
        tasks = []
        for i in range(5):
            task = tool.execute(
                ranking_type="TOP_GAINERS",
                market="ALL",
                count=10
            )
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 모든 요청이 성공해야 함
        assert len(results) == 5
        for result in results:
            assert "ranking" in result
            assert "timestamp" in result
        
        await tool.cleanup()


# pytest 옵션 설정은 conftest.py에서 처리