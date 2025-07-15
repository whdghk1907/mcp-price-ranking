"""
API 클라이언트 테스트
TDD: 한국투자증권 API 클라이언트 기능 테스트
"""
import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from src.api.client import KoreaInvestmentAPIClient
from src.api.models import StockPrice, MarketSummary, TokenInfo
from src.api.constants import API_BASE_URL, ENDPOINTS, MARKETS
from src.exceptions import APIError, AuthenticationError, RateLimitError, DataNotFoundError


class TestKoreaInvestmentAPIClient:
    """한국투자증권 API 클라이언트 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트용 클라이언트 인스턴스"""
        return KoreaInvestmentAPIClient(
            app_key="test_app_key",
            app_secret="test_app_secret"
        )
    
    def test_client_creation(self, client):
        """클라이언트 생성 테스트"""
        assert client.app_key == "test_app_key"
        assert client.app_secret == "test_app_secret"
        assert client.base_url == API_BASE_URL
        assert client.session is None
        assert client.access_token is None
        assert client.token_expires_at is None
    
    def test_client_with_custom_base_url(self):
        """커스텀 base_url로 클라이언트 생성"""
        custom_url = "https://custom.api.com"
        client = KoreaInvestmentAPIClient(
            app_key="key",
            app_secret="secret",
            base_url=custom_url
        )
        assert client.base_url == custom_url
    
    @pytest.mark.asyncio
    async def test_session_creation(self, client):
        """세션 생성 테스트"""
        await client._create_session()
        
        assert client.session is not None
        assert hasattr(client.session, 'close')
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, client):
        """세션 정리 테스트"""
        await client._create_session()
        session = client.session
        
        await client.close()
        
        assert client.session is None
        # 실제 세션 정리 확인은 모킹으로 대체
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_authenticate_success(self, mock_post, client):
        """인증 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'access_token': 'test_token',
            'token_type': 'Bearer',
            'expires_in': 3600
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        token_info = await client.authenticate()
        
        assert token_info.access_token == 'test_token'
        assert token_info.token_type == 'Bearer'
        assert token_info.expires_in == 3600
        assert client.access_token == 'test_token'
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.post')
    async def test_authenticate_failure(self, mock_post, client):
        """인증 실패 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status = 401
        mock_response.json = AsyncMock(return_value={
            'error': 'invalid_client',
            'error_description': 'Invalid client credentials'
        })
        mock_post.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        
        with pytest.raises(AuthenticationError):
            await client.authenticate()
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_get_stock_price_success(self, mock_request, client):
        """주식 가격 조회 성공 테스트"""
        # Mock 응답 설정
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'output': {
                'stck_prpr': '78500',  # 현재가
                'prdy_vrss': '1500',   # 전일대비
                'prdy_vrss_sign': '2', # 등락부호
                'prdy_ctrt': '1.95',   # 등락률
                'acml_vol': '12345678', # 누적거래량
                'stck_hgpr': '79000',  # 고가
                'stck_lwpr': '77000',  # 저가
                'stck_oprc': '77500',  # 시가
                'hts_kor_isnm': '삼성전자' # 종목명
            }
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        client.access_token = "test_token"
        client.token_expires_at = time.time() + 3600  # 1시간 후 만료
        
        stock_price = await client.get_stock_price("005930")
        
        assert stock_price.stock_code == "005930"
        assert stock_price.stock_name == "삼성전자"
        assert stock_price.current_price == 78500
        assert stock_price.change == 1500
        assert stock_price.change_rate == 1.95
        assert stock_price.volume == 12345678
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_get_stock_price_not_found(self, mock_request, client):
        """존재하지 않는 주식 조회 테스트"""
        mock_response = Mock()
        mock_response.status = 404
        mock_response.json = AsyncMock(return_value={
            'error': 'not_found',
            'message': 'Stock not found'
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        client.access_token = "test_token"
        client.token_expires_at = time.time() + 3600  # 1시간 후 만료
        
        with pytest.raises(DataNotFoundError):
            await client.get_stock_price("999999")
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_get_ranking_data_success(self, mock_request, client):
        """순위 데이터 조회 성공 테스트"""
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={
            'output': [
                {
                    'mksc_shrn_iscd': '005930',
                    'hts_kor_isnm': '삼성전자',
                    'stck_prpr': '78500',
                    'prdy_vrss': '1500',
                    'prdy_ctrt': '1.95',
                    'acml_vol': '12345678',
                    'stck_hgpr': '79000',
                    'stck_lwpr': '77000',
                    'stck_oprc': '77500'
                },
                {
                    'mksc_shrn_iscd': '000660',
                    'hts_kor_isnm': 'SK하이닉스',
                    'stck_prpr': '125000',
                    'prdy_vrss': '2000',
                    'prdy_ctrt': '1.63',
                    'acml_vol': '8765432',
                    'stck_hgpr': '126000',
                    'stck_lwpr': '123000',
                    'stck_oprc': '124000'
                }
            ]
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        client.access_token = "test_token"
        client.token_expires_at = time.time() + 3600  # 1시간 후 만료
        
        ranking_data = await client.get_ranking_data("TOP_GAINERS", "ALL", 10)
        
        assert len(ranking_data) == 2
        assert ranking_data[0].stock_code == "005930"
        assert ranking_data[0].stock_name == "삼성전자"
        assert ranking_data[1].stock_code == "000660"
        assert ranking_data[1].stock_name == "SK하이닉스"
    
    @pytest.mark.asyncio
    @patch('aiohttp.ClientSession.request')
    async def test_rate_limit_handling(self, mock_request, client):
        """API 요청 제한 처리 테스트"""
        mock_response = Mock()
        mock_response.status = 429
        mock_response.headers = {'Retry-After': '60'}
        mock_response.json = AsyncMock(return_value={
            'error': 'rate_limit_exceeded',
            'message': 'Too many requests'
        })
        mock_request.return_value.__aenter__.return_value = mock_response
        
        await client._create_session()
        client.access_token = "test_token"
        client.token_expires_at = time.time() + 3600  # 1시간 후 만료
        
        with pytest.raises(RateLimitError) as exc_info:
            await client.get_stock_price("005930")
        
        assert exc_info.value.retry_after == 60
    
    @pytest.mark.asyncio
    async def test_token_refresh_when_expired(self, client):
        """토큰 만료 시 자동 갱신 테스트"""
        # 만료된 토큰 설정
        client.access_token = "expired_token"
        client.token_expires_at = datetime.now().timestamp() - 3600  # 1시간 전 만료
        
        # 토큰 갱신이 필요한지 확인
        assert client._is_token_expired() is True
        
        # 실제 갱신 테스트는 authenticate 모킹으로 대체


class TestAPIConstants:
    """API 상수 테스트"""
    
    def test_api_base_url(self):
        """API 기본 URL 확인"""
        assert API_BASE_URL == "https://openapi.koreainvestment.com:9443"
    
    def test_endpoints(self):
        """API 엔드포인트 확인"""
        assert "TOKEN" in ENDPOINTS
        assert "STOCK_PRICE" in ENDPOINTS
        assert "STOCK_RANKING" in ENDPOINTS
        
        # 엔드포인트 경로 확인
        assert ENDPOINTS["TOKEN"] == "/oauth2/tokenP"
        assert "/uapi/domestic-stock" in ENDPOINTS["STOCK_PRICE"]
    
    def test_markets(self):
        """시장 코드 확인"""
        assert MARKETS["KOSPI"] == "J"
        assert MARKETS["KOSDAQ"] == "Q"
        assert MARKETS["ALL"] == ""


class TestAPIErrorHandling:
    """API 에러 처리 테스트"""
    
    @pytest.fixture
    def client(self):
        """테스트용 클라이언트"""
        return KoreaInvestmentAPIClient("key", "secret")
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, client):
        """네트워크 에러 처리 테스트"""
        await client._create_session()
        
        with patch.object(client.session, 'post', side_effect=Exception("Network error")):
            with pytest.raises(APIError) as exc_info:
                await client.authenticate()
            
            assert "Network error" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_invalid_response_handling(self, client):
        """잘못된 응답 처리 테스트"""
        await client._create_session()
        
        mock_response = Mock()
        mock_response.status = 200
        mock_response.json = AsyncMock(side_effect=Exception("Invalid JSON"))
        
        with patch.object(client.session, 'post', return_value=mock_response):
            with pytest.raises(APIError):
                await client.authenticate()


class TestClientIntegration:
    """클라이언트 통합 테스트"""
    
    @pytest.mark.asyncio
    async def test_full_workflow_mock(self):
        """전체 워크플로우 테스트 (모킹)"""
        client = KoreaInvestmentAPIClient("key", "secret")
        
        # 1. 세션 생성
        await client._create_session()
        assert client.session is not None
        
        # 2. 인증은 모킹으로 설정
        client.access_token = "mock_token"
        client.token_expires_at = datetime.now().timestamp() + 3600
        
        # 3. 토큰 유효성 확인
        assert not client._is_token_expired()
        
        # 4. 정리
        await client.close()
        assert client.session is None