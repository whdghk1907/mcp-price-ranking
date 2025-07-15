"""
52주 신고가/신저가 도구
52주 고저가 돌파 종목 분석 도구
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal, Tuple
from src.tools import BaseTool
from src.api.client import KoreaInvestmentAPIClient
from src.api.models import HighLowStockItem, HighLowAnalysis
from src.config import config
from src.exceptions import DataValidationError, ToolExecutionError, APIError
from src.utils import setup_logger


class HighLowTool(BaseTool):
    """52주 신고가/신저가 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_52week_high_low",
            description="52주 신고가/신저가 종목 조회 및 돌파 분석"
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
        
        # 캐시
        self._cache = {}
        self._cache_ttl = 60  # 1분 TTL
    
    async def execute(
        self,
        type: Literal["HIGH", "LOW", "BOTH"] = "BOTH",
        market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
        count: int = 20,
        breakthrough_only: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """52주 고저가 조회 실행"""
        
        # 파라미터 검증
        if not self.validate_parameters(
            type=type,
            market=market,
            count=count,
            breakthrough_only=breakthrough_only
        ):
            raise DataValidationError(
                "Invalid parameters for 52-week high/low tool"
            )
        
        try:
            # 캐시 확인
            cache_key = f"{type}_{market}_{count}_{breakthrough_only}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Cache hit for key: {cache_key}")
                return cached_result
            
            self.logger.info(f"Fetching 52-week high/low data: {type}, {market}, breakthrough_only={breakthrough_only}")
            
            # API 클라이언트를 사용하여 데이터 조회
            high_stocks, low_stocks, analysis = await self.api_client.get_52week_high_low_data(
                market=market,
                breakthrough_only=breakthrough_only
            )
            
            # 타입별 필터링
            if type == "HIGH":
                filtered_high = self._filter_and_limit_stocks(high_stocks, count, breakthrough_only)
                filtered_low = []
            elif type == "LOW":
                filtered_high = []
                filtered_low = self._filter_and_limit_stocks(low_stocks, count, breakthrough_only)
            else:  # BOTH
                filtered_high = self._filter_and_limit_stocks(high_stocks, count//2, breakthrough_only)
                filtered_low = self._filter_and_limit_stocks(low_stocks, count//2, breakthrough_only)
            
            # 추가 분석 수행
            enhanced_analysis = self._enhance_analysis(analysis, filtered_high, filtered_low)
            
            # 결과 구성
            result = {
                "timestamp": datetime.now().isoformat(),
                "type": type,
                "market": market,
                "count": len(filtered_high) + len(filtered_low),
                "breakthrough_only": breakthrough_only,
                "high_stocks": [stock.to_dict() for stock in filtered_high],
                "low_stocks": [stock.to_dict() for stock in filtered_low],
                "statistics": enhanced_analysis.to_dict(),
                "insights": self._generate_insights(filtered_high, filtered_low, enhanced_analysis),
                "data_source": "Korea Investment API (Mock)",
                "cache_status": "MISS"
            }
            
            # 캐시에 저장
            self._set_cache(cache_key, result)
            
            self.logger.info(f"Successfully fetched {len(filtered_high)} highs and {len(filtered_low)} lows")
            return result
            
        except APIError as e:
            self.logger.error(f"API error: {str(e)}")
            raise ToolExecutionError(
                f"Failed to fetch 52-week high/low data: {str(e)}",
                tool_name=self.name,
                parameters={"type": type, "market": market, "count": count}
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise ToolExecutionError(
                f"Unexpected error in 52-week high/low tool: {str(e)}",
                tool_name=self.name,
                parameters={"type": type, "market": market, "count": count}
            )
    
    def validate_parameters(self, **kwargs) -> bool:
        """파라미터 검증"""
        type_param = kwargs.get("type", "BOTH")
        market = kwargs.get("market", "ALL")
        count = kwargs.get("count", 20)
        breakthrough_only = kwargs.get("breakthrough_only", True)
        
        # type 검증
        valid_types = ["HIGH", "LOW", "BOTH"]
        if type_param not in valid_types:
            return False
        
        # market 검증
        valid_markets = ["ALL", "KOSPI", "KOSDAQ"]
        if market not in valid_markets:
            return False
        
        # count 검증
        if not isinstance(count, int) or count < 1 or count > 200:
            return False
        
        # breakthrough_only 검증
        if not isinstance(breakthrough_only, bool):
            return False
        
        return True
    
    def _filter_and_limit_stocks(
        self, 
        stocks: List[HighLowStockItem], 
        count: int, 
        breakthrough_only: bool
    ) -> List[HighLowStockItem]:
        """종목 필터링 및 제한"""
        filtered_stocks = stocks
        
        # 돌파 전용 필터링
        if breakthrough_only:
            filtered_stocks = [
                stock for stock in filtered_stocks 
                if stock.is_new_high or stock.is_new_low
            ]
        
        # 모멘텀 스코어 기준 정렬
        filtered_stocks.sort(key=lambda x: x.momentum_score or 0, reverse=True)
        
        # 개수 제한
        return filtered_stocks[:count]
    
    def _enhance_analysis(
        self, 
        analysis: HighLowAnalysis, 
        high_stocks: List[HighLowStockItem], 
        low_stocks: List[HighLowStockItem]
    ) -> HighLowAnalysis:
        """분석 결과 강화"""
        # 업종별 분석 업데이트
        all_stocks = high_stocks + low_stocks
        sector_analysis = {}
        
        for stock in all_stocks:
            sector = stock.sector or "기타"
            if sector not in sector_analysis:
                sector_analysis[sector] = {"high": 0, "low": 0}
            
            if stock in high_stocks:
                sector_analysis[sector]["high"] += 1
            if stock in low_stocks:
                sector_analysis[sector]["low"] += 1
        
        analysis.sector_analysis = sector_analysis
        
        # 시장 강도 재계산
        if analysis.new_lows_count > 0:
            analysis.high_low_ratio = analysis.new_highs_count / analysis.new_lows_count
        else:
            analysis.high_low_ratio = float('inf') if analysis.new_highs_count > 0 else 0.0
        
        return analysis
    
    def _generate_insights(
        self, 
        high_stocks: List[HighLowStockItem], 
        low_stocks: List[HighLowStockItem], 
        analysis: HighLowAnalysis
    ) -> List[str]:
        """인사이트 생성"""
        insights = []
        
        # 시장 강도 분석
        market_strength = analysis.market_strength
        if market_strength in ["VERY_STRONG", "STRONG"]:
            insights.append(f"시장이 {market_strength.lower()} 강세를 보이고 있습니다.")
        elif market_strength in ["VERY_WEAK", "WEAK"]:
            insights.append(f"시장이 {market_strength.lower()} 약세를 보이고 있습니다.")
        
        # 돌파 종목 분석
        if high_stocks:
            avg_momentum = sum(stock.momentum_score or 0 for stock in high_stocks) / len(high_stocks)
            insights.append(f"신고가 돌파 종목들의 평균 모멘텀 스코어: {avg_momentum:.1f}")
            
            # 고평가 구간 종목 확인
            high_position_stocks = [s for s in high_stocks if s.position_in_range > 95]
            if high_position_stocks:
                insights.append(f"{len(high_position_stocks)}개 종목이 52주 최고점 근처에 있습니다.")
        
        if low_stocks:
            # 저평가 구간 종목 확인
            low_position_stocks = [s for s in low_stocks if s.position_in_range < 5]
            if low_position_stocks:
                insights.append(f"{len(low_position_stocks)}개 종목이 52주 최저점 근처에 있습니다.")
        
        # 업종별 분석
        if analysis.sector_analysis:
            dominant_sector = max(analysis.sector_analysis.items(), key=lambda x: sum(x[1].values()) if isinstance(x[1], dict) else x[1])
            insights.append(f"'{dominant_sector[0]}' 업종이 가장 많은 활동을 보입니다.")
        
        return insights
    
    def _get_from_cache(self, key: str) -> Optional[Dict[str, Any]]:
        """캐시에서 조회"""
        if key not in self._cache:
            return None
            
        cache_entry = self._cache[key]
        cache_time = cache_entry.get("timestamp", 0)
        
        if datetime.now().timestamp() - cache_time > self._cache_ttl:
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
        
        # 캐시 크기 제한
        if len(self._cache) > 50:
            oldest_key = min(self._cache.keys(), key=lambda k: self._cache[k]["timestamp"])
            del self._cache[oldest_key]
    
    def _get_parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "type": {
                    "type": "string",
                    "enum": ["HIGH", "LOW", "BOTH"],
                    "description": "조회 유형 (신고가/신저가/모두)",
                    "default": "BOTH"
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
                    "maximum": 200,
                    "default": 20
                },
                "breakthrough_only": {
                    "type": "boolean",
                    "description": "오늘 돌파한 종목만 표시",
                    "default": True
                }
            },
            "required": []
        }
    
    async def cleanup(self):
        """리소스 정리"""
        try:
            await self.api_client.close()
            self._cache.clear()
            self.logger.info("HighLowTool cleaned up")
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