"""
상한가/하한가 도구
상한가/하한가 종목 조회 및 분석 도구
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from src.tools import BaseTool
from src.api.client import KoreaInvestmentAPIClient
from src.api.models import LimitStockItem, LimitAnalysis
from src.config import config
from src.exceptions import DataValidationError, ToolExecutionError, APIError
from src.utils import setup_logger


class LimitTool(BaseTool):
    """상한가/하한가 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_limit_stocks",
            description="상한가/하한가 종목 조회 및 분석"
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
        limit_type: Literal["UPPER", "LOWER", "BOTH"] = "BOTH",
        market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
        include_history: bool = True,
        **kwargs
    ) -> Dict[str, Any]:
        """상한가/하한가 조회 실행"""
        
        # 파라미터 검증
        if not self.validate_parameters(
            limit_type=limit_type,
            market=market,
            include_history=include_history
        ):
            raise DataValidationError(
                "Invalid parameters for limit stocks tool"
            )
        
        try:
            # 캐시 확인
            cache_key = f"{limit_type}_{market}_{include_history}"
            cached_result = self._get_from_cache(cache_key)
            if cached_result:
                self.logger.info(f"Cache hit for key: {cache_key}")
                return cached_result
            
            self.logger.info(f"Fetching limit stocks data: {limit_type}, {market}, include_history={include_history}")
            
            # API 클라이언트를 사용하여 데이터 조회
            upper_stocks, lower_stocks, analysis = await self.api_client.get_limit_stocks_data(
                market=market,
                include_history=include_history
            )
            
            # 타입별 필터링
            if limit_type == "UPPER":
                filtered_upper = upper_stocks
                filtered_lower = []
            elif limit_type == "LOWER":
                filtered_upper = []
                filtered_lower = lower_stocks
            else:  # BOTH
                filtered_upper = upper_stocks
                filtered_lower = lower_stocks
            
            # 테마별 분석
            theme_analysis = self._analyze_themes(filtered_upper + filtered_lower)
            
            # 인사이트 생성
            insights = self._generate_insights(filtered_upper, filtered_lower, analysis, limit_type)
            
            # 결과 구성
            result = {
                "timestamp": datetime.now().isoformat(),
                "limit_type": limit_type,
                "market": market,
                "include_history": include_history,
                "upper_limit": [stock.to_dict() for stock in filtered_upper],
                "lower_limit": [stock.to_dict() for stock in filtered_lower],
                "summary": analysis.to_dict(),
                "theme_analysis": theme_analysis,
                "insights": insights,
                "data_source": "Korea Investment API (Mock)",
                "cache_status": "MISS"
            }
            
            # 캐시에 저장
            self._set_cache(cache_key, result)
            
            self.logger.info(f"Successfully fetched {len(filtered_upper)} upper limits and {len(filtered_lower)} lower limits")
            return result
            
        except APIError as e:
            self.logger.error(f"API error: {str(e)}")
            raise ToolExecutionError(
                f"Failed to fetch limit stocks data: {str(e)}",
                tool_name=self.name,
                parameters={"limit_type": limit_type, "market": market}
            )
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            raise ToolExecutionError(
                f"Unexpected error in limit stocks tool: {str(e)}",
                tool_name=self.name,
                parameters={"limit_type": limit_type, "market": market}
            )
    
    def validate_parameters(self, **kwargs) -> bool:
        """파라미터 검증"""
        limit_type = kwargs.get("limit_type", "BOTH")
        market = kwargs.get("market", "ALL")
        include_history = kwargs.get("include_history", True)
        
        # limit_type 검증
        valid_types = ["UPPER", "LOWER", "BOTH"]
        if limit_type not in valid_types:
            return False
        
        # market 검증
        valid_markets = ["ALL", "KOSPI", "KOSDAQ"]
        if market not in valid_markets:
            return False
        
        # include_history 검증
        if not isinstance(include_history, bool):
            return False
        
        return True
    
    def _analyze_themes(self, stocks: List[LimitStockItem]) -> Dict[str, int]:
        """테마별 분석"""
        theme_count = {}
        for stock in stocks:
            for theme in stock.theme:
                theme_count[theme] = theme_count.get(theme, 0) + 1
        return theme_count
    
    def _generate_insights(
        self, 
        upper_stocks: List[LimitStockItem], 
        lower_stocks: List[LimitStockItem], 
        analysis: LimitAnalysis,
        limit_type: str = "BOTH"
    ) -> List[str]:
        """인사이트 생성"""
        insights = []
        
        # 상한가/하한가 개수 분석 - limit_type에 따라 다르게 처리
        if limit_type == "UPPER":
            if not upper_stocks:
                insights.append("상한가 종목이 없습니다")
                return insights
        elif limit_type == "LOWER":
            if not lower_stocks:
                insights.append("하한가 종목이 없습니다")
                return insights
        else:  # BOTH
            if not upper_stocks and not lower_stocks:
                insights.append("상한가/하한가 종목이 없습니다")
                return insights
            if not upper_stocks:
                insights.append("상한가 종목이 없습니다")
            if not lower_stocks:
                insights.append("하한가 종목이 없습니다")
        
        # 시장 심리 분석
        sentiment = analysis.market_sentiment
        if sentiment == "VERY_BULLISH":
            insights.append("시장이 매우 강한 상승 심리를 보이고 있습니다.")
        elif sentiment == "BULLISH":
            insights.append("시장이 상승 심리를 보이고 있습니다.")
        elif sentiment == "BEARISH":
            insights.append("시장이 하락 심리를 보이고 있습니다.")
        elif sentiment == "VERY_BEARISH":
            insights.append("시장이 매우 강한 하락 심리를 보이고 있습니다.")
        
        # 연속 상한가 분석
        if upper_stocks:
            consecutive_stocks = [s for s in upper_stocks if s.consecutive_limits >= 2]
            if consecutive_stocks:
                max_consecutive = max(s.consecutive_limits for s in consecutive_stocks)
                insights.append(f"연속 상한가 종목 {len(consecutive_stocks)}개 (최대 {max_consecutive}일 연속)")
        
        # 상한가 해제 확률 분석
        if upper_stocks:
            high_unlock_prob = [s for s in upper_stocks if s.unlock_probability > 50]
            if high_unlock_prob:
                insights.append(f"{len(high_unlock_prob)}개 종목이 상한가 해제 가능성이 높습니다.")
        
        # 강한 상한가/하한가 분석
        strong_limits = [s for s in upper_stocks + lower_stocks if s.is_strong_limit]
        if strong_limits:
            insights.append(f"{len(strong_limits)}개 종목이 강한 상한가/하한가를 보이고 있습니다.")
        
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
                "limit_type": {
                    "type": "string",
                    "enum": ["UPPER", "LOWER", "BOTH"],
                    "description": "조회 유형 (상한가/하한가/모두)",
                    "default": "BOTH"
                },
                "market": {
                    "type": "string",
                    "enum": ["ALL", "KOSPI", "KOSDAQ"],
                    "description": "시장 구분",
                    "default": "ALL"
                },
                "include_history": {
                    "type": "boolean",
                    "description": "연속 상한가/하한가 이력 포함",
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
            self.logger.info("LimitTool cleaned up")
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