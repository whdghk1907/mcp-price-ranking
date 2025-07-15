"""
API 데이터 모델
한국투자증권 API 응답 데이터 모델 정의
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class TokenInfo:
    """토큰 정보"""
    access_token: str
    token_type: str
    expires_in: int
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
    
    @property
    def expires_at(self) -> datetime:
        """토큰 만료 시간"""
        return datetime.fromtimestamp(
            self.created_at.timestamp() + self.expires_in
        )
    
    @property
    def is_expired(self) -> bool:
        """토큰 만료 여부"""
        return datetime.now() > self.expires_at
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "access_token": self.access_token,
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat()
        }


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
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def previous_close(self) -> int:
        """전일 종가"""
        return self.current_price - self.change
    
    @property
    def trading_value(self) -> int:
        """거래대금"""
        return self.current_price * self.volume
    
    @property
    def high_rate(self) -> float:
        """고가 대비 현재가 비율"""
        if self.high == 0:
            return 0.0
        return ((self.current_price - self.high) / self.high) * 100
    
    @property
    def low_rate(self) -> float:
        """저가 대비 현재가 비율"""
        if self.low == 0:
            return 0.0
        return ((self.current_price - self.low) / self.low) * 100
    
    @property
    def volatility(self) -> float:
        """일중 변동성"""
        if self.low == 0:
            return 0.0
        return ((self.high - self.low) / self.low) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "change": self.change,
            "change_rate": self.change_rate,
            "volume": self.volume,
            "trading_value": self.trading_value,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "high_rate": self.high_rate,
            "low_rate": self.low_rate,
            "volatility": self.volatility,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any], stock_code: str) -> "StockPrice":
        """API 응답에서 StockPrice 객체 생성"""
        return cls(
            stock_code=stock_code,
            stock_name=response_data.get('hts_kor_isnm', ''),
            current_price=int(response_data.get('stck_prpr', 0)),
            change=int(response_data.get('prdy_vrss', 0)),
            change_rate=float(response_data.get('prdy_ctrt', 0)),
            volume=int(response_data.get('acml_vol', 0)),
            high=int(response_data.get('stck_hgpr', 0)),
            low=int(response_data.get('stck_lwpr', 0)),
            open=int(response_data.get('stck_oprc', 0))
        )


@dataclass
class MarketSummary:
    """시장 요약 정보"""
    total_stocks: int
    advancing: int
    declining: int
    unchanged: int
    average_change_rate: float
    median_change_rate: float = 0.0
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def advance_decline_ratio(self) -> float:
        """상승/하락 비율"""
        if self.declining == 0:
            return float('inf')
        return self.advancing / self.declining
    
    @property
    def market_breadth(self) -> str:
        """시장 폭"""
        if self.advance_decline_ratio > 2.0:
            return "VERY_POSITIVE"
        elif self.advance_decline_ratio > 1.5:
            return "POSITIVE"
        elif self.advance_decline_ratio > 1.0:
            return "SLIGHTLY_POSITIVE"
        elif self.advance_decline_ratio > 0.5:
            return "SLIGHTLY_NEGATIVE"
        else:
            return "NEGATIVE"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "total_stocks": self.total_stocks,
            "advancing": self.advancing,
            "declining": self.declining,
            "unchanged": self.unchanged,
            "average_change_rate": self.average_change_rate,
            "median_change_rate": self.median_change_rate,
            "advance_decline_ratio": self.advance_decline_ratio,
            "market_breadth": self.market_breadth,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class StockRankingItem:
    """주식 순위 항목"""
    rank: int
    stock_code: str
    stock_name: str
    current_price: int
    change: int
    change_rate: float
    volume: int
    trading_value: int
    high: int
    low: int
    open: int
    market_cap: Optional[int] = None
    sector: Optional[str] = None
    
    @property
    def previous_close(self) -> int:
        """전일 종가"""
        return self.current_price - self.change
    
    @property
    def volatility(self) -> float:
        """일중 변동성"""
        if self.low == 0:
            return 0.0
        return ((self.high - self.low) / self.low) * 100
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "rank": self.rank,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "previous_close": self.previous_close,
            "change": self.change,
            "change_rate": self.change_rate,
            "volume": self.volume,
            "trading_value": self.trading_value,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "volatility": self.volatility,
            "market_cap": self.market_cap,
            "sector": self.sector
        }
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any], rank: int) -> "StockRankingItem":
        """API 응답에서 StockRankingItem 객체 생성"""
        current_price = int(response_data.get('stck_prpr', 0))
        volume = int(response_data.get('acml_vol', 0))
        
        return cls(
            rank=rank,
            stock_code=response_data.get('mksc_shrn_iscd', ''),
            stock_name=response_data.get('hts_kor_isnm', ''),
            current_price=current_price,
            change=int(response_data.get('prdy_vrss', 0)),
            change_rate=float(response_data.get('prdy_ctrt', 0)),
            volume=volume,
            trading_value=current_price * volume,
            high=int(response_data.get('stck_hgpr', 0)),
            low=int(response_data.get('stck_lwpr', 0)),
            open=int(response_data.get('stck_oprc', 0)),
            sector=response_data.get('bstp_kor_isnm', None)
        )


@dataclass
class APIResponse:
    """API 응답 기본 구조"""
    status_code: int
    data: Dict[str, Any]
    message: str = ""
    success: bool = True
    
    @property
    def is_success(self) -> bool:
        """성공 여부"""
        return self.success and 200 <= self.status_code < 300
    
    @property
    def is_error(self) -> bool:
        """에러 여부"""
        return not self.success or self.status_code >= 400
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "status_code": self.status_code,
            "data": self.data,
            "message": self.message,
            "success": self.success
        }


@dataclass
class Alert:
    """알림 정보"""
    alert_id: str
    stock_code: str
    stock_name: str
    alert_type: str
    message: str
    trigger_price: int
    current_price: int
    timestamp: datetime = None
    priority: str = "MEDIUM"
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    @property
    def age_seconds(self) -> int:
        """알림 발생 후 경과 시간 (초)"""
        return int((datetime.now() - self.timestamp).total_seconds())
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "alert_id": self.alert_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "alert_type": self.alert_type,
            "message": self.message,
            "trigger_price": self.trigger_price,
            "current_price": self.current_price,
            "priority": self.priority,
            "timestamp": self.timestamp.isoformat(),
            "age_seconds": self.age_seconds
        }


@dataclass
class HighLowStockItem:
    """52주 고저가 종목 정보"""
    stock_code: str
    stock_name: str
    current_price: int
    week_52_high: int
    week_52_low: int
    week_52_high_date: datetime.date
    week_52_low_date: datetime.date
    is_new_high: bool = False
    is_new_low: bool = False
    volume: int = 0
    volume_ratio: float = 0.0
    momentum_score: float = 0.0
    sector: str = ""
    market_cap: Optional[int] = None
    foreign_ownership: float = 0.0
    
    @property
    def high_breakthrough_rate(self) -> float:
        """고점 돌파율 (음수면 고점 대비 하락률)"""
        if self.week_52_high == 0:
            return 0.0
        return ((self.current_price - self.week_52_high) / self.week_52_high) * 100
    
    @property
    def low_breakthrough_rate(self) -> float:
        """저점 돌파율 (양수면 저점 대비 상승률)"""
        if self.week_52_low == 0:
            return 0.0
        return ((self.current_price - self.week_52_low) / self.week_52_low) * 100
    
    @property
    def high_low_range(self) -> float:
        """52주 고저가 범위"""
        if self.week_52_low == 0:
            return 0.0
        return ((self.week_52_high - self.week_52_low) / self.week_52_low) * 100
    
    @property
    def position_in_range(self) -> float:
        """52주 범위 내 현재 위치 (0-100%)"""
        if self.week_52_high == self.week_52_low:
            return 50.0
        return ((self.current_price - self.week_52_low) / (self.week_52_high - self.week_52_low)) * 100
    
    @property
    def days_since_high(self) -> int:
        """고점 이후 경과 일수"""
        from datetime import date
        return (date.today() - self.week_52_high_date).days
    
    @property
    def days_since_low(self) -> int:
        """저점 이후 경과 일수"""
        from datetime import date
        return (date.today() - self.week_52_low_date).days
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "week_52_high": self.week_52_high,
            "week_52_low": self.week_52_low,
            "week_52_high_date": self.week_52_high_date.isoformat(),
            "week_52_low_date": self.week_52_low_date.isoformat(),
            "is_new_high": self.is_new_high,
            "is_new_low": self.is_new_low,
            "high_breakthrough_rate": self.high_breakthrough_rate,
            "low_breakthrough_rate": self.low_breakthrough_rate,
            "high_low_range": self.high_low_range,
            "position_in_range": self.position_in_range,
            "days_since_high": self.days_since_high,
            "days_since_low": self.days_since_low,
            "volume": self.volume,
            "volume_ratio": self.volume_ratio,
            "momentum_score": self.momentum_score,
            "sector": self.sector,
            "market_cap": self.market_cap,
            "foreign_ownership": self.foreign_ownership
        }
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> "HighLowStockItem":
        """API 응답에서 HighLowStockItem 생성"""
        from datetime import date
        
        return cls(
            stock_code=response_data.get('stock_code', ''),
            stock_name=response_data.get('stock_name', ''),
            current_price=int(response_data.get('current_price', 0)),
            week_52_high=int(response_data.get('week_52_high', 0)),
            week_52_low=int(response_data.get('week_52_low', 0)),
            week_52_high_date=date.fromisoformat(response_data.get('week_52_high_date', date.today().isoformat())),
            week_52_low_date=date.fromisoformat(response_data.get('week_52_low_date', date.today().isoformat())),
            is_new_high=response_data.get('is_new_high', False),
            is_new_low=response_data.get('is_new_low', False),
            volume=int(response_data.get('volume', 0)),
            volume_ratio=float(response_data.get('volume_ratio', 0.0)),
            momentum_score=float(response_data.get('momentum_score', 0.0)),
            sector=response_data.get('sector', ''),
            market_cap=response_data.get('market_cap'),
            foreign_ownership=float(response_data.get('foreign_ownership', 0.0))
        )


@dataclass
class HighLowAnalysis:
    """52주 고저가 분석 결과"""
    new_highs_count: int
    new_lows_count: int
    high_low_ratio: float
    market_breadth: str
    breakthrough_stocks: List[HighLowStockItem] = None
    resistance_stocks: List[HighLowStockItem] = None
    sector_analysis: Dict[str, int] = None
    
    def __post_init__(self):
        if self.breakthrough_stocks is None:
            self.breakthrough_stocks = []
        if self.resistance_stocks is None:
            self.resistance_stocks = []
        if self.sector_analysis is None:
            self.sector_analysis = {}
    
    @property
    def market_strength(self) -> str:
        """시장 강도 평가"""
        if self.high_low_ratio >= 3.0:
            return "VERY_STRONG"
        elif self.high_low_ratio >= 2.0:
            return "STRONG"
        elif self.high_low_ratio >= 1.5:
            return "MODERATE"
        elif self.high_low_ratio >= 1.0:
            return "WEAK"
        else:
            return "VERY_WEAK"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "new_highs_count": self.new_highs_count,
            "new_lows_count": self.new_lows_count,
            "high_low_ratio": self.high_low_ratio,
            "market_breadth": self.market_breadth,
            "market_strength": self.market_strength,
            "breakthrough_stocks_count": len(self.breakthrough_stocks),
            "resistance_stocks_count": len(self.resistance_stocks),
            "sector_analysis": self.sector_analysis
        }


@dataclass
class LimitStockItem:
    """상한가/하한가 종목 정보"""
    stock_code: str
    stock_name: str
    current_price: int
    limit_price: int
    previous_close: int
    limit_type: str  # "UPPER" or "LOWER"
    hit_time: datetime.time
    volume_at_limit: int = 0
    buy_orders: int = 0
    sell_orders: int = 0
    consecutive_limits: int = 0
    unlock_probability: float = 0.0
    theme: List[str] = None
    recent_limits: List[Dict[str, Any]] = None
    market_cap: Optional[int] = None
    
    def __post_init__(self):
        if self.theme is None:
            self.theme = []
        if self.recent_limits is None:
            self.recent_limits = []
    
    @property
    def limit_rate(self) -> float:
        """상한가/하한가 비율"""
        if self.previous_close == 0:
            return 0.0
        return ((self.current_price - self.previous_close) / self.previous_close) * 100
    
    @property
    def volume_pressure(self) -> float:
        """거래량 압박 지수 (매수 압박 비율)"""
        total_orders = self.buy_orders + self.sell_orders
        if total_orders == 0:
            return 0.0
        return (self.buy_orders / total_orders) * 100
    
    @property
    def is_strong_limit(self) -> bool:
        """강한 상한가/하한가 여부"""
        return (
            self.consecutive_limits >= 2 or
            self.volume_pressure > 90.0 or
            self.volume_at_limit > 10000000
        )
    
    @property
    def trading_value(self) -> int:
        """거래대금"""
        return self.current_price * self.volume_at_limit
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "current_price": self.current_price,
            "limit_price": self.limit_price,
            "previous_close": self.previous_close,
            "limit_type": self.limit_type,
            "hit_time": self.hit_time.isoformat(),
            "volume_at_limit": self.volume_at_limit,
            "buy_orders": self.buy_orders,
            "sell_orders": self.sell_orders,
            "consecutive_limits": self.consecutive_limits,
            "unlock_probability": self.unlock_probability,
            "theme": self.theme,
            "recent_limits": self.recent_limits,
            "market_cap": self.market_cap,
            "limit_rate": self.limit_rate,
            "volume_pressure": self.volume_pressure,
            "is_strong_limit": self.is_strong_limit,
            "trading_value": self.trading_value
        }
    
    @classmethod
    def from_api_response(cls, response_data: Dict[str, Any]) -> "LimitStockItem":
        """API 응답에서 LimitStockItem 생성"""
        from datetime import time
        
        # 시간 파싱
        hit_time_str = response_data.get('hit_time', '09:00:00')
        hit_time = time.fromisoformat(hit_time_str) if hit_time_str else time(9, 0, 0)
        
        return cls(
            stock_code=response_data.get('stock_code', ''),
            stock_name=response_data.get('stock_name', ''),
            current_price=int(response_data.get('current_price', 0)),
            limit_price=int(response_data.get('limit_price', 0)),
            previous_close=int(response_data.get('previous_close', 0)),
            limit_type=response_data.get('limit_type', 'UPPER'),
            hit_time=hit_time,
            volume_at_limit=int(response_data.get('volume_at_limit', 0)),
            buy_orders=int(response_data.get('buy_orders', 0)),
            sell_orders=int(response_data.get('sell_orders', 0)),
            consecutive_limits=int(response_data.get('consecutive_limits', 0)),
            unlock_probability=float(response_data.get('unlock_probability', 0.0)),
            theme=response_data.get('theme', []),
            recent_limits=response_data.get('recent_limits', []),
            market_cap=response_data.get('market_cap')
        )


@dataclass
class LimitAnalysis:
    """상한가/하한가 분석 결과"""
    upper_count: int
    lower_count: int
    upper_unlock_count: int
    lower_unlock_count: int
    market_sentiment: str
    total_volume: int = 0
    sector_distribution: Dict[str, int] = None
    theme_concentration: Dict[str, int] = None
    
    def __post_init__(self):
        if self.sector_distribution is None:
            self.sector_distribution = {}
        if self.theme_concentration is None:
            self.theme_concentration = {}
    
    @property
    def limit_ratio(self) -> float:
        """상한가 비율"""
        total = self.upper_count + self.lower_count
        if total == 0:
            return 0.0
        return self.upper_count / total
    
    @property
    def sentiment_strength(self) -> str:
        """시장 심리 강도"""
        if self.market_sentiment == "VERY_BULLISH":
            return "VERY_STRONG"
        elif self.market_sentiment == "BULLISH":
            return "STRONG"
        elif self.market_sentiment == "NEUTRAL":
            return "MODERATE"
        elif self.market_sentiment == "BEARISH":
            return "WEAK"
        else:  # VERY_BEARISH
            return "VERY_WEAK"
    
    @property
    def unlock_rate(self) -> float:
        """상한가 해제율"""
        if self.upper_count == 0:
            return 0.0
        return (self.upper_unlock_count / self.upper_count) * 100
    
    @property
    def market_momentum(self) -> str:
        """시장 모멘텀"""
        ratio = self.limit_ratio
        if ratio >= 0.8:
            return "VERY_POSITIVE"
        elif ratio >= 0.6:
            return "POSITIVE"
        elif ratio >= 0.4:
            return "NEUTRAL"
        elif ratio >= 0.2:
            return "NEGATIVE"
        else:
            return "VERY_NEGATIVE"
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "upper_count": self.upper_count,
            "lower_count": self.lower_count,
            "upper_unlock_count": self.upper_unlock_count,
            "lower_unlock_count": self.lower_unlock_count,
            "market_sentiment": self.market_sentiment,
            "total_volume": self.total_volume,
            "sector_distribution": self.sector_distribution,
            "theme_concentration": self.theme_concentration,
            "limit_ratio": self.limit_ratio,
            "sentiment_strength": self.sentiment_strength,
            "unlock_rate": self.unlock_rate,
            "market_momentum": self.market_momentum
        }