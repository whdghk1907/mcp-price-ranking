"""
통합 가격 순위 도구
API 클라이언트와 완전히 통합된 가격 순위 도구
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from src.tools import BaseTool
from src.api.client import KoreaInvestmentAPIClient
from src.api.models import StockRankingItem, MarketSummary
from src.config import config
from src.exceptions import DataValidationError, ToolExecutionError, APIError
from src.utils import setup_logger
from src.cache.redis_cache import RedisCacheManager


class IntegratedPriceRankingTool(BaseTool):
    """API 클라이언트와 통합된 가격 순위 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_price_change_ranking",
            description="실시간 가격 변동률 기준 종목 순위 조회 (한국투자증권 API 연동)"
        )
        
        # API 클라이언트 초기화
        self.api_client = KoreaInvestmentAPIClient(
            app_key=config.api.app_key,
            app_secret=config.api.app_secret,
            base_url=config.api.base_url,
            timeout=config.api.timeout
        )
        
        # 로거 설정
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # Redis 캐시 매니저 초기화
        self.cache_manager = RedisCacheManager()
    
    async def execute(
        self,
        ranking_type: Literal["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"] = "TOP_GAINERS",
        market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
        count: int = 20,
        min_price: Optional[int] = None,
        min_volume: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """통합 가격 순위 조회 실행"""
        
        # 파라미터 검증
        if not self.validate_parameters(
            ranking_type=ranking_type,
            market=market,
            count=count,
            min_price=min_price,
            min_volume=min_volume
        ):
            raise DataValidationError(
                "Invalid parameters for integrated price ranking tool"
            )
        
        try:
            # Redis 캐시 확인
            cached_result = await self.cache_manager.get_ranking_cache(
                ranking_type=ranking_type,
                market=market,
                count=count,
                min_price=min_price,
                min_volume=min_volume
            )
            
            if cached_result:
                self.logger.info(f"Cache hit for: {ranking_type}_{market}_{count}")
                # 캐시된 결과에 cache_status 추가
                if isinstance(cached_result, dict):
                    cached_result["cache_status"] = "HIT"
                return cached_result
            
            self.logger.info(f"Fetching ranking data: {ranking_type}, {market}, {count}")
            
            # API 클라이언트를 사용하여 실제 데이터 조회
            ranking_data = await self.api_client.get_ranking_data(
                ranking_type=ranking_type,
                market=market,
                count=count * 2  # 필터링을 고려하여 더 많이 조회
            )
            
            # 필터 적용
            filtered_ranking = self._apply_filters(
                ranking_data, 
                min_price=min_price, 
                min_volume=min_volume
            )
            
            # 결과 개수 제한
            filtered_ranking = filtered_ranking[:count]
            
            # 시장 요약 정보 조회
            market_summary = await self.api_client.get_market_summary()
            
            # 결과 구성
            result = {
                "timestamp": datetime.now().isoformat(),
                "ranking_type": ranking_type,
                "market": market,
                "count": len(filtered_ranking),
                "requested_count": count,
                "filters": {
                    "min_price": min_price,
                    "min_volume": min_volume
                },
                "ranking": [item.to_dict() for item in filtered_ranking],
                "summary": market_summary.to_dict() if market_summary else {},
                "data_source": "Korea Investment API",
                "cache_status": "MISS"
            }
            
            # Redis 캐시에 저장
            await self.cache_manager.set_ranking_cache(
                ranking_type=ranking_type,
                market=market,
                count=count,
                data=result,
                min_price=min_price,
                min_volume=min_volume
            )
            
            self.logger.info(f"Successfully fetched {len(filtered_ranking)} items")
            return result
            
        except APIError as e:
            self.logger.error(f"API error: {str(e)}")
            raise ToolExecutionError(
                f"Failed to fetch ranking data: {str(e)}",
                tool_name=self.name,
                parameters={
                    "ranking_type": ranking_type,
                    "market": market,
                    "count": count
                }
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise ToolExecutionError(
                f"Unexpected error in ranking tool: {str(e)}",
                tool_name=self.name,
                parameters={
                    "ranking_type": ranking_type,
                    "market": market,
                    "count": count
                }
            )
    
    def validate_parameters(self, **kwargs) -> bool:
        """파라미터 검증"""
        ranking_type = kwargs.get("ranking_type", "TOP_GAINERS")
        market = kwargs.get("market", "ALL")
        count = kwargs.get("count", 20)
        
        # ranking_type 검증
        valid_ranking_types = ["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"]
        if ranking_type not in valid_ranking_types:
            return False
        
        # market 검증
        valid_markets = ["ALL", "KOSPI", "KOSDAQ"]
        if market not in valid_markets:
            return False
        
        # count 검증
        if not isinstance(count, int) or count < 1 or count > 100:
            return False
        
        # min_price 검증
        min_price = kwargs.get("min_price")
        if min_price is not None and (not isinstance(min_price, int) or min_price < 0):
            return False
        
        # min_volume 검증
        min_volume = kwargs.get("min_volume")
        if min_volume is not None and (not isinstance(min_volume, int) or min_volume < 0):
            return False
        
        return True
    
    def _apply_filters(
        self, 
        ranking_data: List[StockRankingItem],
        min_price: Optional[int] = None,
        min_volume: Optional[int] = None
    ) -> List[StockRankingItem]:
        """필터 적용"""
        filtered_data = ranking_data
        
        # 최소 가격 필터
        if min_price is not None:
            filtered_data = [
                item for item in filtered_data 
                if item.current_price >= min_price
            ]
        
        # 최소 거래량 필터
        if min_volume is not None:
            filtered_data = [
                item for item in filtered_data 
                if item.volume >= min_volume
            ]
        
        return filtered_data
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 조회"""
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        cache_time = cache_entry.get("timestamp", 0)
        
        if datetime.now().timestamp() - cache_time > self._cache_ttl:
            # 캐시 만료
            del self._cache[key]
            return None
        
        result = cache_entry.get("data")
        if result:
            result["cache_status"] = "HIT"
        
        return result
    
    def _set_cache(self, key: str, data: Dict[str, Any]):
        """캐시에 저장"""
        self._cache[key] = {
            "data": data,
            "timestamp": datetime.now().timestamp()
        }
        
        # 캐시 크기 제한 (간단한 LRU)
        if len(self._cache) > 100:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "ranking_type": {
                    "type": "string",
                    "enum": ["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"],
                    "description": "순위 유형 (상승률/하락률/변동성)",
                    "default": "TOP_GAINERS"
                },
                "market": {
                    "type": "string",
                    "enum": ["ALL", "KOSPI", "KOSDAQ"],
                    "description": "시장 구분",
                    "default": "ALL"
                },
                "count": {
                    "type": "integer",
                    "description": "조회할 종목 수",
                    "minimum": 1,
                    "maximum": 100,
                    "default": 20
                },
                "min_price": {
                    "type": "integer",
                    "description": "최소 주가 필터 (원)",
                    "minimum": 0
                },
                "min_volume": {
                    "type": "integer",
                    "description": "최소 거래량 필터 (주)",
                    "minimum": 0
                }
            },
            "required": []
        }
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            await self.api_client.close()
            self._cache.clear()
            self.logger.info("IntegratedPriceRankingTool cleaned up")
        except Exception as e:
            self.logger.error(f"Error during cleanup: {str(e)}")
    
    async def health_check(self) -> Dict[str, Any]:
        """도구 상태 확인"""
        try:
            # API 클라이언트 상태 확인
            api_health = await self.api_client.health_check()
            
            return {
                "tool_name": self.name,
                "status": "healthy" if api_health["status"] == "healthy" else "unhealthy",
                "api_client": api_health,
                "cache_size": len(self._cache),
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "tool_name": self.name,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }