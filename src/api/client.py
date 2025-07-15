"""
한국투자증권 OpenAPI 클라이언트
"""

import asyncio
import aiohttp
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin
import logging

from src.api.models import StockPrice, MarketSummary, TokenInfo, StockRankingItem, APIResponse, HighLowStockItem, HighLowAnalysis, LimitStockItem, LimitAnalysis
from src.api.constants import (
    API_BASE_URL, ENDPOINTS, MARKETS, RANKING_TYPES, DEFAULT_HEADERS, 
    TIMEOUTS, RETRY_CONFIG, ERROR_CODES, ERROR_MESSAGES
)
from src.exceptions import APIError, AuthenticationError, RateLimitError, DataNotFoundError
from src.utils import setup_logger


class KoreaInvestmentAPIClient:
    """한국투자증권 OpenAPI 클라이언트"""
    
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        base_url: str = API_BASE_URL,
        timeout: int = TIMEOUTS["TOTAL"]
    ):
        self.app_key = app_key
        self.app_secret = app_secret
        self.base_url = base_url
        self.timeout = timeout
        
        # 세션 및 인증 정보
        self.session: Optional[aiohttp.ClientSession] = None
        self.access_token: Optional[str] = None
        self.token_expires_at: Optional[float] = None
        
        # 로거 설정
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # 요청 제한 관리
        self.last_request_time = 0
        self.request_count = 0
        self.request_times = []
    
    async def __aenter__(self):
        """컨텍스트 매니저 진입"""
        await self._create_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """컨텍스트 매니저 종료"""
        await self.close()
    
    async def _create_session(self):
        """HTTP 세션 생성"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            connector = aiohttp.TCPConnector(limit=100, limit_per_host=20)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=DEFAULT_HEADERS
            )
            
            self.logger.info("HTTP session created")
    
    async def close(self):
        """리소스 정리"""
        if self.session:
            await self.session.close()
            self.session = None
            self.logger.info("HTTP session closed")
    
    def _is_token_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        if not self.access_token or not self.token_expires_at:
            return True
        
        return time.time() >= self.token_expires_at
    
    async def _wait_for_rate_limit(self):
        """요청 제한 대기"""
        current_time = time.time()
        
        # 1초당 요청 제한 체크
        if current_time - self.last_request_time < 1.0 / RETRY_CONFIG["MAX_RETRIES"]:
            wait_time = 1.0 / RETRY_CONFIG["MAX_RETRIES"] - (current_time - self.last_request_time)
            await asyncio.sleep(wait_time)
        
        # 분당 요청 제한 체크
        self.request_times = [t for t in self.request_times if current_time - t < 60]
        if len(self.request_times) >= 50:  # 분당 50회 제한
            wait_time = 60 - (current_time - self.request_times[0])
            if wait_time > 0:
                await asyncio.sleep(wait_time)
        
        self.last_request_time = current_time
        self.request_times.append(current_time)
    
    async def authenticate(self) -> TokenInfo:
        """OAuth 인증"""
        await self._create_session()
        
        url = urljoin(self.base_url, ENDPOINTS["TOKEN"])
        
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        try:
            await self._wait_for_rate_limit()
            
            async with self.session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    token_info = TokenInfo(
                        access_token=data["access_token"],
                        token_type=data.get("token_type", "Bearer"),
                        expires_in=data.get("expires_in", 3600)
                    )
                    
                    self.access_token = token_info.access_token
                    self.token_expires_at = token_info.expires_at.timestamp()
                    
                    self.logger.info("Authentication successful")
                    return token_info
                    
                elif response.status == 401:
                    error_data = await response.json()
                    raise AuthenticationError(
                        f"Authentication failed: {error_data.get('error_description', 'Invalid credentials')}"
                    )
                else:
                    raise APIError(
                        f"Authentication failed with status {response.status}",
                        status_code=response.status
                    )
                    
        except aiohttp.ClientError as e:
            raise APIError(f"Network error during authentication: {str(e)}")
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError)):
                raise
            raise APIError(f"Unexpected error during authentication: {str(e)}")
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """API 요청 실행"""
        await self._create_session()
        
        # 토큰 확인 및 갱신
        if self._is_token_expired():
            await self.authenticate()
        
        # 요청 헤더 설정
        request_headers = DEFAULT_HEADERS.copy()
        if headers:
            request_headers.update(headers)
        
        if self.access_token:
            request_headers["Authorization"] = f"Bearer {self.access_token}"
        
        url = urljoin(self.base_url, endpoint)
        
        # 요청 제한 대기
        await self._wait_for_rate_limit()
        
        try:
            async with self.session.request(
                method,
                url,
                params=params,
                json=data,
                headers=request_headers
            ) as response:
                
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    # 토큰 만료 시 재인증
                    await self.authenticate()
                    request_headers["Authorization"] = f"Bearer {self.access_token}"
                    
                    async with self.session.request(
                        method,
                        url,
                        params=params,
                        json=data,
                        headers=request_headers
                    ) as retry_response:
                        if retry_response.status == 200:
                            return await retry_response.json()
                        else:
                            raise APIError(
                                f"API request failed after retry: {retry_response.status}",
                                status_code=retry_response.status
                            )
                elif response.status == 429:
                    retry_after = int(response.headers.get("Retry-After", 60))
                    raise RateLimitError(
                        "Rate limit exceeded",
                        retry_after=retry_after
                    )
                elif response.status == 404:
                    raise DataNotFoundError("Requested data not found")
                else:
                    error_data = await response.json() if response.content_type == 'application/json' else {}
                    raise APIError(
                        f"API request failed: {response.status}",
                        status_code=response.status,
                        api_response=error_data
                    )
                    
        except aiohttp.ClientError as e:
            raise APIError(f"Network error: {str(e)}")
        except Exception as e:
            if isinstance(e, (APIError, AuthenticationError, RateLimitError, DataNotFoundError)):
                raise
            raise APIError(f"Unexpected error: {str(e)}")
    
    async def get_stock_price(self, stock_code: str) -> StockPrice:
        """주식 가격 정보 조회"""
        if not stock_code or len(stock_code) != 6:
            raise ValueError("Stock code must be 6 digits")
        
        params = {
            "fid_cond_mrkt_div_code": "J",  # 시장 구분 (J: 주식)
            "fid_input_iscd": stock_code
        }
        
        try:
            response = await self._make_request("GET", ENDPOINTS["STOCK_PRICE"], params=params)
            
            if "output" in response:
                return StockPrice.from_api_response(response["output"], stock_code)
            else:
                raise APIError("Invalid response format")
                
        except Exception as e:
            if isinstance(e, (APIError, DataNotFoundError, RateLimitError)):
                raise
            raise APIError(f"Failed to get stock price for {stock_code}: {str(e)}")
    
    async def get_ranking_data(
        self,
        ranking_type: str,
        market: str = "ALL",
        count: int = 20
    ) -> List[StockRankingItem]:
        """순위 데이터 조회"""
        if ranking_type not in RANKING_TYPES:
            raise ValueError(f"Invalid ranking type: {ranking_type}")
        
        if market not in MARKETS:
            raise ValueError(f"Invalid market: {market}")
        
        params = {
            "fid_cond_mrkt_div_code": MARKETS[market],
            "fid_cond_scr_div_code": "20171",  # 화면 구분 코드
            "fid_div_cls_code": RANKING_TYPES[ranking_type],
            "fid_rsfl_rate1": "",
            "fid_rsfl_rate2": "",
            "fid_input_cnt_1": str(count)
        }
        
        try:
            response = await self._make_request("GET", ENDPOINTS["STOCK_RANKING"], params=params)
            
            if "output" in response:
                ranking_items = []
                for rank, item_data in enumerate(response["output"], 1):
                    ranking_item = StockRankingItem.from_api_response(item_data, rank)
                    ranking_items.append(ranking_item)
                
                return ranking_items
            else:
                raise APIError("Invalid response format")
                
        except Exception as e:
            if isinstance(e, APIError):
                raise
            raise APIError(f"Failed to get ranking data: {str(e)}")
    
    async def get_market_summary(self) -> MarketSummary:
        """시장 요약 정보 조회"""
        # 실제 구현에서는 시장 지수 정보를 조회하여 요약 생성
        # 현재는 모킹 데이터 반환
        return MarketSummary(
            total_stocks=2500,
            advancing=1200,
            declining=800,
            unchanged=500,
            average_change_rate=1.25,
            median_change_rate=0.85
        )
    
    async def get_52week_high_low_data(
        self,
        market: str = "ALL",
        breakthrough_only: bool = True
    ) -> Tuple[List[HighLowStockItem], List[HighLowStockItem], HighLowAnalysis]:
        """52주 신고가/신저가 데이터 조회"""
        try:
            # 현재는 모킹 데이터 반환 (실제 API 연동 시 수정)
            high_stocks = self._generate_mock_high_low_data("HIGH", market, breakthrough_only)
            low_stocks = self._generate_mock_high_low_data("LOW", market, breakthrough_only)
            
            # 분석 결과 생성
            analysis = HighLowAnalysis(
                new_highs_count=len(high_stocks),
                new_lows_count=len(low_stocks),
                high_low_ratio=len(high_stocks) / max(len(low_stocks), 1),
                market_breadth="POSITIVE" if len(high_stocks) > len(low_stocks) else "NEGATIVE",
                breakthrough_stocks=high_stocks,
                resistance_stocks=low_stocks,
                sector_analysis=self._analyze_sectors(high_stocks + low_stocks)
            )
            
            return high_stocks, low_stocks, analysis
            
        except Exception as e:
            raise APIError(f"Failed to get 52-week high/low data: {str(e)}")
    
    def _generate_mock_high_low_data(
        self, 
        data_type: str, 
        market: str, 
        breakthrough_only: bool
    ) -> List[HighLowStockItem]:
        """모킹 52주 고저가 데이터 생성"""
        from datetime import date, timedelta
        import random
        
        mock_data = []
        count = random.randint(5, 15) if breakthrough_only else random.randint(10, 30)
        
        for i in range(count):
            stock_code = f"{random.randint(1, 999):03d}{random.randint(10, 999):03d}"
            
            if data_type == "HIGH":
                current_price = random.randint(50000, 200000)
                week_52_high = current_price if breakthrough_only else random.randint(current_price, current_price + 20000)
                week_52_low = random.randint(30000, current_price - 10000)
                is_new_high = breakthrough_only or random.choice([True, False])
                is_new_low = False
            else:  # LOW
                current_price = random.randint(10000, 50000)
                week_52_high = random.randint(current_price + 10000, current_price + 50000)
                week_52_low = current_price if breakthrough_only else random.randint(current_price - 10000, current_price)
                is_new_high = False
                is_new_low = breakthrough_only or random.choice([True, False])
            
            mock_data.append(HighLowStockItem(
                stock_code=stock_code,
                stock_name=f"테스트종목{i+1}",
                current_price=current_price,
                week_52_high=week_52_high,
                week_52_low=week_52_low,
                week_52_high_date=date.today() - timedelta(days=random.randint(0, 365)),
                week_52_low_date=date.today() - timedelta(days=random.randint(0, 365)),
                is_new_high=is_new_high,
                is_new_low=is_new_low,
                volume=random.randint(100000, 10000000),
                volume_ratio=random.uniform(0.5, 5.0),
                momentum_score=random.uniform(1.0, 10.0),
                sector=random.choice(["기술", "금융", "제조", "유통", "바이오", "자동차"]),
                market_cap=current_price * random.randint(10000000, 100000000),
                foreign_ownership=random.uniform(0.0, 70.0)
            ))
        
        return mock_data
    
    def _analyze_sectors(self, stocks: List[HighLowStockItem]) -> Dict[str, int]:
        """업종별 분석"""
        sector_count = {}
        for stock in stocks:
            sector = stock.sector or "기타"
            sector_count[sector] = sector_count.get(sector, 0) + 1
        return sector_count
    
    async def get_limit_stocks_data(
        self,
        market: str = "ALL",
        include_history: bool = True
    ) -> Tuple[List[LimitStockItem], List[LimitStockItem], LimitAnalysis]:
        """상한가/하한가 데이터 조회"""
        try:
            # 현재는 모킹 데이터 반환 (실제 API 연동 시 수정)
            upper_stocks = self._generate_mock_limit_data("UPPER", market, include_history)
            lower_stocks = self._generate_mock_limit_data("LOWER", market, include_history)
            
            # 분석 결과 생성
            analysis = LimitAnalysis(
                upper_count=len(upper_stocks),
                lower_count=len(lower_stocks),
                upper_unlock_count=len([s for s in upper_stocks if s.unlock_probability > 50]),
                lower_unlock_count=len([s for s in lower_stocks if s.unlock_probability > 50]),
                market_sentiment=self._calculate_market_sentiment(upper_stocks, lower_stocks),
                total_volume=sum(s.volume_at_limit for s in upper_stocks + lower_stocks),
                sector_distribution=self._analyze_limit_sectors(upper_stocks + lower_stocks),
                theme_concentration=self._analyze_limit_themes(upper_stocks + lower_stocks)
            )
            
            return upper_stocks, lower_stocks, analysis
            
        except Exception as e:
            raise APIError(f"Failed to get limit stocks data: {str(e)}")
    
    def _generate_mock_limit_data(
        self, 
        limit_type: str, 
        market: str, 
        include_history: bool
    ) -> List[LimitStockItem]:
        """모킹 상한가/하한가 데이터 생성"""
        from datetime import time
        import random
        
        mock_data = []
        count = random.randint(3, 15)
        
        for i in range(count):
            stock_code = f"{random.randint(1, 999):03d}{random.randint(10, 999):03d}"
            previous_close = random.randint(10000, 100000)
            
            if limit_type == "UPPER":
                # 상한가 (30% 상승)
                limit_price = int(previous_close * 1.3)
                current_price = limit_price
                buy_orders = random.randint(5000000, 50000000)
                sell_orders = random.randint(0, 1000000)
                consecutive_limits = random.randint(1, 5)
                unlock_prob = random.uniform(5.0, 40.0)
                theme = random.choice([
                    ["2차전지", "전기차"], 
                    ["바이오", "신약"], 
                    ["반도체", "AI"], 
                    ["게임", "엔터"],
                    ["조선", "해운"]
                ])
            else:  # LOWER
                # 하한가 (30% 하락)
                limit_price = int(previous_close * 0.7)
                current_price = limit_price
                buy_orders = random.randint(0, 5000000)
                sell_orders = random.randint(10000000, 100000000)
                consecutive_limits = random.randint(1, 3)
                unlock_prob = random.uniform(10.0, 60.0)
                theme = ["구조조정", "실적악화"]
            
            recent_limits = []
            if include_history and consecutive_limits > 1:
                for j in range(min(consecutive_limits, 5)):
                    recent_limits.append({
                        "date": f"2024-01-{10-j:02d}",
                        "type": limit_type
                    })
            
            mock_data.append(LimitStockItem(
                stock_code=stock_code,
                stock_name=f"테스트종목{i+1}",
                current_price=current_price,
                limit_price=limit_price,
                previous_close=previous_close,
                limit_type=limit_type,
                hit_time=time(random.randint(9, 14), random.randint(0, 59), random.randint(0, 59)),
                volume_at_limit=random.randint(1000000, 20000000),
                buy_orders=buy_orders,
                sell_orders=sell_orders,
                consecutive_limits=consecutive_limits,
                unlock_probability=unlock_prob,
                theme=theme,
                recent_limits=recent_limits,
                market_cap=current_price * random.randint(10000000, 100000000)
            ))
        
        return mock_data
    
    def _calculate_market_sentiment(self, upper_stocks: List[LimitStockItem], lower_stocks: List[LimitStockItem]) -> str:
        """시장 심리 계산"""
        upper_count = len(upper_stocks)
        lower_count = len(lower_stocks)
        
        if upper_count == 0 and lower_count == 0:
            return "NEUTRAL"
        
        ratio = upper_count / (upper_count + lower_count)
        
        if ratio >= 0.8:
            return "VERY_BULLISH"
        elif ratio >= 0.6:
            return "BULLISH"
        elif ratio >= 0.4:
            return "NEUTRAL"
        elif ratio >= 0.2:
            return "BEARISH"
        else:
            return "VERY_BEARISH"
    
    def _analyze_limit_sectors(self, stocks: List[LimitStockItem]) -> Dict[str, int]:
        """업종별 상한가/하한가 분석"""
        # 실제 구현에서는 종목 코드를 통해 업종 정보 조회
        sectors = ["기술", "금융", "제조", "유통", "바이오", "자동차", "조선", "화학"]
        import random
        
        sector_count = {}
        for stock in stocks:
            sector = random.choice(sectors)
            sector_count[sector] = sector_count.get(sector, 0) + 1
        
        return sector_count
    
    def _analyze_limit_themes(self, stocks: List[LimitStockItem]) -> Dict[str, int]:
        """테마별 상한가/하한가 분석"""
        theme_count = {}
        for stock in stocks:
            for theme in stock.theme:
                theme_count[theme] = theme_count.get(theme, 0) + 1
        
        return theme_count
    
    async def health_check(self) -> Dict[str, Any]:
        """API 서버 상태 확인"""
        try:
            # 간단한 요청으로 서버 상태 확인
            await self._make_request("GET", ENDPOINTS["STOCK_PRICE"], params={
                "fid_cond_mrkt_div_code": "J",
                "fid_input_iscd": "005930"  # 삼성전자로 테스트
            })
            
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "api_server": "operational"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "api_server": "error"
            }