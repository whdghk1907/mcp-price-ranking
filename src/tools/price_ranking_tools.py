"""
가격 순위 도구
주식 가격 변동률 기준 순위 조회 도구
"""

from datetime import datetime
from typing import Dict, Any, List, Optional, Literal
from src.tools import BaseTool
from src.exceptions import DataValidationError, ToolExecutionError


class PriceRankingTool(BaseTool):
    """가격 변동률 순위 도구"""
    
    def __init__(self):
        super().__init__(
            name="get_price_change_ranking",
            description="가격 변동률 기준 종목 순위 조회 (상승률/하락률/변동성)"
        )
    
    async def execute(
        self,
        ranking_type: Literal["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"] = "TOP_GAINERS",
        market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
        count: int = 20,
        min_price: Optional[int] = None,
        min_volume: Optional[int] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """가격 순위 조회 실행"""
        
        # 파라미터 검증
        if not self.validate_parameters(
            ranking_type=ranking_type,
            market=market,
            count=count,
            min_price=min_price,
            min_volume=min_volume
        ):
            raise DataValidationError(
                "Invalid parameters for price ranking tool"
            )
        
        try:
            # 현재는 기본 구조만 반환 (API 클라이언트 구현 후 실제 데이터 조회)
            result = {
                "timestamp": datetime.now().isoformat(),
                "ranking_type": ranking_type,
                "market": market,
                "count": count,
                "filters": {
                    "min_price": min_price,
                    "min_volume": min_volume
                },
                "ranking": self._get_mock_ranking_data(ranking_type, count),
                "summary": self._get_mock_summary_data()
            }
            
            return result
            
        except Exception as e:
            raise ToolExecutionError(
                f"Failed to get price ranking: {str(e)}",
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
    
    def _get_mock_ranking_data(self, ranking_type: str, count: int) -> List[Dict[str, Any]]:
        """모킹 순위 데이터 생성"""
        mock_data = []
        
        base_change_rate = 10.0 if ranking_type == "TOP_GAINERS" else -10.0
        if ranking_type == "MOST_VOLATILE":
            base_change_rate = 15.0
        
        for i in range(count):
            rank = i + 1
            stock_code = f"00{rank:04d}"
            change_rate = base_change_rate - (i * 0.5) if ranking_type == "TOP_GAINERS" else base_change_rate + (i * 0.5)
            
            if ranking_type == "MOST_VOLATILE":
                change_rate = base_change_rate - (i * 0.3)
            
            current_price = 50000 + (i * 100)
            previous_close = int(current_price / (1 + change_rate / 100))
            
            mock_data.append({
                "rank": rank,
                "stock_code": stock_code,
                "stock_name": f"테스트종목{rank}",
                "current_price": current_price,
                "previous_close": previous_close,
                "change": current_price - previous_close,
                "change_rate": round(change_rate, 2),
                "volume": 1000000 + (i * 10000),
                "trading_value": (current_price * (1000000 + (i * 10000))),
                "high": current_price + 500,
                "low": current_price - 500,
                "open": current_price - 200,
                "market_cap": current_price * 1000000,
                "sector": "테스트업종"
            })
        
        return mock_data
    
    def _get_mock_summary_data(self) -> Dict[str, Any]:
        """모킹 요약 데이터 생성"""
        return {
            "total_stocks": 2500,
            "advancing": 1200,
            "declining": 800,
            "unchanged": 500,
            "average_change_rate": 1.25,
            "median_change_rate": 0.85
        }
    
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