"""
API 패키지
외부 API 클라이언트 및 관련 모듈들
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StockPrice:
    """주식 가격 정보"""
    stock_code: str
    stock_name: str
    current_price: int
    change: int
    change_rate: float
    volume: int
    high: int
    low: int
    open: int
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "change": self.change,
            "change_rate": self.change_rate,
            "volume": self.volume,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class MarketSummary:
    """시장 요약 정보"""
    total_stocks: int
    advancing: int
    declining: int
    unchanged: int
    average_change_rate: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "total_stocks": self.total_stocks,
            "advancing": self.advancing,
            "declining": self.declining,
            "unchanged": self.unchanged,
            "average_change_rate": self.average_change_rate,
            "timestamp": self.timestamp.isoformat()
        }