# 📈 상승률 순위 MCP 서버 개발 계획서

## 1. 프로젝트 개요

### 1.1 목적
한국 주식시장의 가격 변동률 기준 상위/하위 종목을 실시간으로 추적하고 분석하는 MCP 서버 구축

### 1.2 범위
- 상승률/하락률 상위 종목 순위
- 52주 신고가/신저가 종목
- 상한가/하한가 종목 추적
- 가격 급등/급락 알림
- 연속 상승/하락 종목 분석
- 변동성 상위 종목
- 갭 상승/하락 종목

### 1.3 기술 스택
- **언어**: Python 3.11+
- **MCP SDK**: mcp-python
- **API Client**: 한국투자증권 OpenAPI
- **비동기 처리**: asyncio, aiohttp
- **데이터 검증**: pydantic
- **기술적 분석**: TA-Lib, pandas
- **캐싱**: Redis + 메모리 캐시

## 2. 서버 아키텍처

```
mcp-price-ranking/
├── src/
│   ├── server.py                 # MCP 서버 메인
│   ├── tools/                    # MCP 도구 정의
│   │   ├── __init__.py
│   │   ├── price_ranking_tools.py    # 가격 순위 도구
│   │   ├── high_low_tools.py         # 신고가/신저가 도구
│   │   ├── limit_tools.py            # 상한가/하한가 도구
│   │   └── volatility_tools.py       # 변동성 분석 도구
│   ├── api/
│   │   ├── __init__.py
│   │   ├── client.py             # API 클라이언트
│   │   ├── models.py             # 데이터 모델
│   │   └── constants.py          # 상수 정의
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── price_analyzer.py    # 가격 분석 엔진
│   │   ├── pattern_detector.py  # 패턴 감지
│   │   └── alert_manager.py     # 알림 관리
│   ├── utils/
│   │   ├── cache.py              # 캐시 관리
│   │   ├── calculator.py         # 계산 유틸리티
│   │   ├── formatter.py          # 데이터 포맷팅
│   │   └── validator.py          # 검증 로직
│   ├── config.py                 # 설정 관리
│   └── exceptions.py             # 예외 정의
├── tests/
│   ├── test_tools.py
│   ├── test_analyzer.py
│   └── test_patterns.py
├── requirements.txt
├── .env.example
└── README.md
```

## 3. 핵심 기능 명세

### 3.1 제공 도구 (Tools)

#### 1) `get_price_change_ranking`
```python
@tool
async def get_price_change_ranking(
    ranking_type: Literal["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"] = "TOP_GAINERS",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    count: int = 20,
    min_price: Optional[int] = None,
    min_volume: Optional[int] = None
) -> dict:
    """
    가격 변동률 기준 순위 조회
    
    Parameters:
        ranking_type: 순위 유형 (상승/하락/변동성)
        market: 시장 구분
        count: 조회할 종목 수
        min_price: 최소 주가 필터
        min_volume: 최소 거래량 필터
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "ranking_type": "TOP_GAINERS",
            "market": "ALL",
            "ranking": [
                {
                    "rank": 1,
                    "stock_code": "123456",
                    "stock_name": "종목명",
                    "current_price": 5670,
                    "previous_close": 4500,
                    "change": 1170,
                    "change_rate": 26.0,
                    "volume": 12345678,
                    "trading_value": 69876543210,
                    "high": 5800,
                    "low": 4550,
                    "open": 4600,
                    "high_rate": 28.89,  # 고가 대비 상승률
                    "volatility": 27.47,  # 일중 변동성
                    "market_cap_change": 234567890000,  # 시총 변화액
                    "consecutive_days": 3,  # 연속 상승일
                    "foreign_net_buy": 12345678900
                },
                ...
            ],
            "summary": {
                "total_stocks": 2345,
                "advancing": 1234,
                "declining": 890,
                "unchanged": 221,
                "average_change_rate": 1.23,
                "median_change_rate": 0.45
            }
        }
    """
```

#### 2) `get_52week_high_low`
```python
@tool
async def get_52week_high_low(
    type: Literal["HIGH", "LOW", "BOTH"] = "BOTH",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    count: int = 20,
    breakthrough_only: bool = True  # 오늘 돌파한 종목만
) -> dict:
    """
    52주 신고가/신저가 종목 조회
    
    Parameters:
        type: 조회 유형 (신고가/신저가/모두)
        market: 시장 구분
        count: 조회할 종목 수
        breakthrough_only: 오늘 돌파 종목만 표시
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "high_stocks": [
                {
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "current_price": 78500,
                    "52week_high": 78500,
                    "52week_high_date": "2024-01-10",
                    "52week_low": 58000,
                    "high_from_low_rate": 35.34,  # 저점 대비 상승률
                    "volume_ratio": 245.6,  # 평균 거래량 대비
                    "days_since_low": 156,
                    "sector": "반도체",
                    "market_cap": 468923450000000,
                    "foreign_ownership": 51.23,
                    "momentum_score": 8.5  # 모멘텀 점수 (1-10)
                },
                ...
            ],
            "low_stocks": [
                {
                    "stock_code": "123456",
                    "stock_name": "종목명",
                    "current_price": 1200,
                    "52week_high": 3500,
                    "52week_low": 1200,
                    "low_from_high_rate": -65.71,  # 고점 대비 하락률
                    "volume_ratio": 189.3,
                    "days_since_high": 234,
                    "support_level": 1150,  # 지지선
                    "risk_score": 8.2  # 위험도 점수 (1-10)
                },
                ...
            ],
            "statistics": {
                "new_highs_count": 45,
                "new_lows_count": 23,
                "high_low_ratio": 1.96,
                "market_breadth": "POSITIVE"
            }
        }
    """
```

#### 3) `get_limit_stocks`
```python
@tool
async def get_limit_stocks(
    limit_type: Literal["UPPER", "LOWER", "BOTH"] = "BOTH",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    include_history: bool = True
) -> dict:
    """
    상한가/하한가 종목 조회
    
    Parameters:
        limit_type: 상한가/하한가 구분
        market: 시장 구분
        include_history: 최근 이력 포함 여부
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "upper_limit": [
                {
                    "stock_code": "123456",
                    "stock_name": "종목명",
                    "current_price": 5670,
                    "limit_price": 5670,
                    "hit_time": "09:32:15",  # 상한가 도달 시각
                    "volume_at_limit": 2345678,
                    "buy_orders": 12345678,  # 매수 잔량
                    "sell_orders": 0,
                    "consecutive_limits": 2,  # 연속 상한가 일수
                    "recent_limits": [  # 최근 30일 상한가 이력
                        {"date": "2024-01-09", "type": "UPPER"},
                        {"date": "2024-01-08", "type": "UPPER"}
                    ],
                    "unlock_probability": 15.3,  # 상한가 해제 확률
                    "theme": ["2차전지", "전기차"]  # 관련 테마
                },
                ...
            ],
            "lower_limit": [...],
            "summary": {
                "upper_count": 12,
                "lower_count": 3,
                "upper_unlock_count": 2,  # 장중 해제
                "lower_unlock_count": 1,
                "market_sentiment": "VERY_BULLISH"
            }
        }
    """
```

#### 4) `get_consecutive_moves`
```python
@tool
async def get_consecutive_moves(
    move_type: Literal["UP", "DOWN"] = "UP",
    min_days: int = 3,
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    count: int = 20
) -> dict:
    """
    연속 상승/하락 종목 조회
    
    Parameters:
        move_type: 상승/하락 구분
        min_days: 최소 연속일수
        market: 시장 구분
        count: 조회할 종목 수
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "move_type": "UP",
            "stocks": [
                {
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "consecutive_days": 5,
                    "total_change_rate": 12.5,
                    "average_daily_rate": 2.4,
                    "current_price": 78500,
                    "start_price": 69777,
                    "highest_in_period": 78500,
                    "volume_trend": "INCREASING",  # 거래량 추세
                    "momentum_indicators": {
                        "rsi": 72.5,
                        "macd": "BULLISH",
                        "stochastic": 85.3
                    },
                    "reversal_probability": 68.5,  # 반전 가능성
                    "historical_performance": {
                        "avg_days_before_reversal": 6.2,
                        "avg_pullback_after": -4.5
                    }
                },
                ...
            ],
            "market_analysis": {
                "total_consecutive_up": 156,
                "total_consecutive_down": 89,
                "longest_streak": 12,
                "sector_concentration": {
                    "반도체": 23,
                    "2차전지": 18,
                    "바이오": 15
                }
            }
        }
    """
```

#### 5) `get_gap_stocks`
```python
@tool
async def get_gap_stocks(
    gap_type: Literal["UP", "DOWN", "BOTH"] = "BOTH",
    min_gap_rate: float = 3.0,
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    count: int = 20
) -> dict:
    """
    갭 상승/하락 종목 조회
    
    Parameters:
        gap_type: 갭 상승/하락 구분
        min_gap_rate: 최소 갭 비율 (%)
        market: 시장 구분
        count: 조회할 종목 수
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "gap_up_stocks": [
                {
                    "stock_code": "123456",
                    "stock_name": "종목명",
                    "open_price": 5200,
                    "previous_close": 4800,
                    "gap_size": 400,
                    "gap_rate": 8.33,
                    "current_price": 5350,
                    "gap_filled": false,
                    "low_of_day": 5150,
                    "fill_probability": 35.2,  # 갭 메우기 확률
                    "volume_at_open": 1234567,
                    "pre_market_news": true,
                    "catalyst": "실적 호조 발표",
                    "similar_gaps_history": [
                        {
                            "date": "2023-11-15",
                            "gap_rate": 7.2,
                            "filled_in_days": 3
                        }
                    ]
                },
                ...
            ],
            "gap_down_stocks": [...],
            "statistics": {
                "avg_gap_up_performance": 2.3,  # 갭상승 후 평균 수익률
                "avg_gap_down_performance": -1.8,
                "gap_fill_rate_up": 62.5,  # 갭상승 메우기 비율
                "gap_fill_rate_down": 71.2
            }
        }
    """
```

#### 6) `get_volatility_ranking`
```python
@tool
async def get_volatility_ranking(
    period: Literal["1D", "5D", "20D"] = "1D",
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
    count: int = 20,
    min_price: Optional[int] = 1000
) -> dict:
    """
    변동성 상위 종목 조회
    
    Parameters:
        period: 변동성 측정 기간
        market: 시장 구분
        count: 조회할 종목 수
        min_price: 최소 주가 필터
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "period": "1D",
            "ranking": [
                {
                    "rank": 1,
                    "stock_code": "123456",
                    "stock_name": "종목명",
                    "volatility": 8.75,  # 변동성 (%)
                    "high": 5800,
                    "low": 5200,
                    "current_price": 5450,
                    "average_true_range": 285,  # ATR
                    "beta": 1.85,
                    "price_swings": [  # 주요 가격 변동
                        {"time": "10:30", "price": 5800, "type": "HIGH"},
                        {"time": "11:45", "price": 5200, "type": "LOW"},
                        {"time": "14:20", "price": 5750, "type": "PEAK"}
                    ],
                    "volume_volatility": 156.3,  # 거래량 변동성
                    "suitable_for": ["DAY_TRADING", "SCALPING"],
                    "risk_level": "VERY_HIGH"
                },
                ...
            ],
            "market_volatility": {
                "vix_equivalent": 24.5,
                "average_volatility": 2.34,
                "volatility_trend": "INCREASING",
                "high_volatility_sectors": ["바이오", "엔터", "게임"]
            }
        }
    """
```

#### 7) `get_price_alerts`
```python
@tool
async def get_price_alerts(
    alert_types: List[str] = ["BREAKOUT", "BREAKDOWN", "UNUSUAL_MOVE"],
    time_window: int = 30,  # 최근 N분
    market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL"
) -> dict:
    """
    실시간 가격 알림 조회
    
    Parameters:
        alert_types: 알림 유형 리스트
        time_window: 조회 시간 범위 (분)
        market: 시장 구분
    
    Returns:
        {
            "timestamp": "2024-01-10T10:30:00+09:00",
            "alerts": [
                {
                    "alert_id": "20240110103025001",
                    "alert_type": "BREAKOUT",
                    "stock_code": "005930",
                    "stock_name": "삼성전자",
                    "trigger_time": "10:30:25",
                    "trigger_price": 78500,
                    "breakout_level": 78000,  # 돌파 레벨
                    "volume_surge": 325.6,  # 거래량 급증률
                    "strength_score": 8.5,  # 신호 강도
                    "follow_up": {
                        "current_price": 78600,
                        "high_since_alert": 78800,
                        "performance": 1.02
                    },
                    "technical_confirmation": [
                        "VOLUME_BREAKOUT",
                        "RSI_OVERSOLD_BOUNCE",
                        "MOVING_AVERAGE_CROSS"
                    ]
                },
                ...
            ],
            "alert_summary": {
                "total_alerts": 45,
                "by_type": {
                    "BREAKOUT": 15,
                    "BREAKDOWN": 8,
                    "UNUSUAL_MOVE": 22
                },
                "success_rate": {
                    "BREAKOUT": 73.3,
                    "BREAKDOWN": 68.5
                }
            }
        }
    """
```

## 4. 분석 엔진 구현

### 4.1 가격 분석 엔진

```python
# src/analysis/price_analyzer.py
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import talib

class PriceAnalyzer:
    """가격 분석 엔진"""
    
    def __init__(self):
        self.cache = {}
        self.indicators = {}
    
    async def analyze_price_action(
        self, 
        stock_code: str, 
        price_data: pd.DataFrame
    ) -> Dict:
        """종합적인 가격 분석"""
        
        analysis = {
            "stock_code": stock_code,
            "timestamp": datetime.now(),
            "price_metrics": self._calculate_price_metrics(price_data),
            "technical_indicators": self._calculate_indicators(price_data),
            "patterns": await self._detect_patterns(price_data),
            "support_resistance": self._find_support_resistance(price_data),
            "trend_analysis": self._analyze_trend(price_data),
            "volatility_analysis": self._analyze_volatility(price_data)
        }
        
        # 종합 점수 계산
        analysis["composite_score"] = self._calculate_composite_score(analysis)
        
        return analysis
    
    def _calculate_price_metrics(self, df: pd.DataFrame) -> Dict:
        """가격 관련 주요 지표 계산"""
        current = df.iloc[-1]
        
        return {
            "current_price": current['close'],
            "change": current['close'] - current['open'],
            "change_rate": ((current['close'] - current['open']) / current['open']) * 100,
            "high_low_spread": ((current['high'] - current['low']) / current['low']) * 100,
            "close_position": (current['close'] - current['low']) / (current['high'] - current['low']) if current['high'] != current['low'] else 0.5,
            "volume_ratio": current['volume'] / df['volume'].rolling(20).mean().iloc[-1] if len(df) > 20 else 1.0,
            "price_momentum": self._calculate_momentum(df),
            "relative_strength": self._calculate_relative_strength(df)
        }
    
    def _calculate_indicators(self, df: pd.DataFrame) -> Dict:
        """기술적 지표 계산"""
        close = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        indicators = {}
        
        # 이동평균
        if len(close) >= 5:
            indicators['sma_5'] = talib.SMA(close, timeperiod=5)[-1]
        if len(close) >= 20:
            indicators['sma_20'] = talib.SMA(close, timeperiod=20)[-1]
            indicators['bb_upper'], indicators['bb_middle'], indicators['bb_lower'] = talib.BBANDS(close, timeperiod=20)[-1]
            
        # 모멘텀 지표
        if len(close) >= 14:
            indicators['rsi'] = talib.RSI(close, timeperiod=14)[-1]
            indicators['cci'] = talib.CCI(high, low, close, timeperiod=14)[-1]
            
        # MACD
        if len(close) >= 26:
            macd, signal, hist = talib.MACD(close, fastperiod=12, slowperiod=26, signalperiod=9)
            indicators['macd'] = macd[-1]
            indicators['macd_signal'] = signal[-1]
            indicators['macd_histogram'] = hist[-1]
            
        # 거래량 지표
        if len(close) >= 20 and len(volume) >= 20:
            indicators['obv'] = talib.OBV(close, volume)[-1]
            indicators['ad'] = talib.AD(high, low, close, volume)[-1]
            
        return indicators
    
    async def _detect_patterns(self, df: pd.DataFrame) -> List[Dict]:
        """차트 패턴 감지"""
        patterns = []
        
        # 캔들스틱 패턴
        open_prices = df['open'].values
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        # Doji
        doji = talib.CDLDOJI(open_prices, high, low, close)
        if doji[-1] != 0:
            patterns.append({
                "type": "DOJI",
                "strength": abs(doji[-1]),
                "position": len(df) - 1
            })
            
        # Hammer
        hammer = talib.CDLHAMMER(open_prices, high, low, close)
        if hammer[-1] != 0:
            patterns.append({
                "type": "HAMMER",
                "strength": abs(hammer[-1]),
                "position": len(df) - 1
            })
            
        # 추가 패턴들...
        
        return patterns
    
    def _find_support_resistance(self, df: pd.DataFrame) -> Dict:
        """지지/저항선 찾기"""
        highs = df['high'].values
        lows = df['low'].values
        
        # 피벗 포인트 계산
        pivot = (highs[-1] + lows[-1] + df['close'].iloc[-1]) / 3
        
        # 지지/저항 레벨
        r1 = 2 * pivot - lows[-1]
        s1 = 2 * pivot - highs[-1]
        r2 = pivot + (highs[-1] - lows[-1])
        s2 = pivot - (highs[-1] - lows[-1])
        
        return {
            "pivot": pivot,
            "resistance_1": r1,
            "resistance_2": r2,
            "support_1": s1,
            "support_2": s2,
            "key_levels": self._find_key_levels(df)
        }
    
    def _find_key_levels(self, df: pd.DataFrame, window: int = 20) -> List[float]:
        """주요 가격대 찾기"""
        key_levels = []
        
        # 최근 고점/저점
        recent_high = df['high'].rolling(window).max()
        recent_low = df['low'].rolling(window).min()
        
        # 자주 터치된 가격대 찾기
        price_counts = {}
        for _, row in df.iterrows():
            for price in [row['high'], row['low'], row['close']]:
                rounded_price = round(price, -2)  # 100원 단위 반올림
                price_counts[rounded_price] = price_counts.get(rounded_price, 0) + 1
        
        # 상위 5개 가격대
        sorted_levels = sorted(price_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        key_levels = [level[0] for level in sorted_levels]
        
        return sorted(key_levels)
```

### 4.2 패턴 감지기

```python
# src/analysis/pattern_detector.py
from typing import Dict, List, Optional, Tuple
import numpy as np
from dataclasses import dataclass

@dataclass
class Pattern:
    """패턴 정보"""
    name: str
    type: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float
    target_price: Optional[float]
    stop_loss: Optional[float]
    description: str

class PatternDetector:
    """가격 패턴 감지기"""
    
    def __init__(self):
        self.min_pattern_bars = 5
        
    def detect_all_patterns(self, price_data: pd.DataFrame) -> List[Pattern]:
        """모든 패턴 감지"""
        patterns = []
        
        # 다양한 패턴 체크
        patterns.extend(self.detect_breakout_patterns(price_data))
        patterns.extend(self.detect_reversal_patterns(price_data))
        patterns.extend(self.detect_continuation_patterns(price_data))
        patterns.extend(self.detect_chart_patterns(price_data))
        
        # 신뢰도 순으로 정렬
        patterns.sort(key=lambda x: x.confidence, reverse=True)
        
        return patterns
    
    def detect_breakout_patterns(self, df: pd.DataFrame) -> List[Pattern]:
        """돌파 패턴 감지"""
        patterns = []
        
        # 박스권 돌파
        if len(df) >= 20:
            recent_high = df['high'].iloc[-20:].max()
            recent_low = df['low'].iloc[-20:].min()
            current_close = df['close'].iloc[-1]
            
            # 상단 돌파
            if current_close > recent_high * 0.98:
                confidence = min((current_close - recent_high) / recent_high * 100, 100)
                patterns.append(Pattern(
                    name="박스권 상단 돌파",
                    type="BULLISH",
                    confidence=confidence,
                    target_price=recent_high + (recent_high - recent_low),
                    stop_loss=recent_high * 0.97,
                    description=f"20일 박스권 상단 {recent_high:,.0f}원 돌파"
                ))
            
            # 하단 이탈
            elif current_close < recent_low * 1.02:
                confidence = min((recent_low - current_close) / recent_low * 100, 100)
                patterns.append(Pattern(
                    name="박스권 하단 이탈",
                    type="BEARISH",
                    confidence=confidence,
                    target_price=recent_low - (recent_high - recent_low),
                    stop_loss=recent_low * 1.03,
                    description=f"20일 박스권 하단 {recent_low:,.0f}원 이탈"
                ))
        
        # 삼각수렴 돌파
        triangle_pattern = self._detect_triangle_breakout(df)
        if triangle_pattern:
            patterns.append(triangle_pattern)
            
        return patterns
    
    def detect_reversal_patterns(self, df: pd.DataFrame) -> List[Pattern]:
        """반전 패턴 감지"""
        patterns = []
        
        # 이중 바닥/천정
        double_pattern = self._detect_double_pattern(df)
        if double_pattern:
            patterns.append(double_pattern)
            
        # V자 반전
        v_pattern = self._detect_v_reversal(df)
        if v_pattern:
            patterns.append(v_pattern)
            
        return patterns
    
    def _detect_triangle_breakout(self, df: pd.DataFrame) -> Optional[Pattern]:
        """삼각수렴 돌파 감지"""
        if len(df) < 30:
            return None
            
        # 고점과 저점의 수렴 확인
        highs = df['high'].iloc[-30:].values
        lows = df['low'].iloc[-30:].values
        
        # 추세선 계산
        high_slope = np.polyfit(range(len(highs)), highs, 1)[0]
        low_slope = np.polyfit(range(len(lows)), lows, 1)[0]
        
        # 수렴 패턴 확인
        if abs(high_slope) < abs(low_slope) and high_slope < 0 and low_slope > 0:
            current_close = df['close'].iloc[-1]
            convergence_point = (highs[-1] + lows[-1]) / 2
            
            if current_close > highs[-1] * 0.98:
                return Pattern(
                    name="상승 삼각형 돌파",
                    type="BULLISH",
                    confidence=75.0,
                    target_price=convergence_point + (highs[0] - lows[0]),
                    stop_loss=convergence_point * 0.97,
                    description="삼각수렴 상단 돌파, 상승 모멘텀 확인"
                )
                
        return None
```

### 4.3 알림 관리자

```python
# src/analysis/alert_manager.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import deque
import asyncio

class AlertManager:
    """실시간 알림 관리"""
    
    def __init__(self, max_alerts_per_stock: int = 5):
        self.alerts = deque(maxlen=1000)  # 최근 1000개 알림 유지
        self.alert_history = {}  # 종목별 알림 이력
        self.max_alerts_per_stock = max_alerts_per_stock
        self.alert_rules = self._initialize_rules()
        
    def _initialize_rules(self) -> Dict:
        """알림 규칙 초기화"""
        return {
            "PRICE_SURGE": {
                "threshold": 5.0,  # 5% 이상 급등
                "time_window": 300,  # 5분 내
                "priority": "HIGH"
            },
            "VOLUME_SPIKE": {
                "threshold": 300.0,  # 평균 대비 300%
                "time_window": 600,  # 10분 내
                "priority": "MEDIUM"
            },
            "BREAKOUT": {
                "threshold": 20,  # 20일 고점 돌파
                "confirmation_volume": 150.0,  # 평균 거래량 150%
                "priority": "HIGH"
            },
            "GAP_UP": {
                "threshold": 3.0,  # 3% 이상 갭상승
                "priority": "MEDIUM"
            },
            "LIMIT_APPROACH": {
                "threshold": 28.0,  # 28% 상승 (상한가 임박)
                "priority": "VERY_HIGH"
            }
        }
    
    async def check_alerts(
        self, 
        stock_data: Dict,
        historical_data: pd.DataFrame
    ) -> List[Dict]:
        """알림 조건 체크"""
        new_alerts = []
        stock_code = stock_data['stock_code']
        
        # 종목별 알림 제한 체크
        if not self._can_send_alert(stock_code):
            return []
        
        # 각 규칙별 체크
        for rule_name, rule_config in self.alert_rules.items():
            if self._check_rule(rule_name, stock_data, historical_data, rule_config):
                alert = self._create_alert(
                    stock_code=stock_code,
                    stock_name=stock_data['stock_name'],
                    alert_type=rule_name,
                    data=stock_data,
                    priority=rule_config['priority']
                )
                new_alerts.append(alert)
                
        # 알림 저장 및 전송
        for alert in new_alerts:
            await self._process_alert(alert)
            
        return new_alerts
    
    def _check_rule(
        self, 
        rule_name: str, 
        stock_data: Dict,
        historical_data: pd.DataFrame,
        rule_config: Dict
    ) -> bool:
        """개별 규칙 체크"""
        if rule_name == "PRICE_SURGE":
            return self._check_price_surge(stock_data, rule_config)
        elif rule_name == "VOLUME_SPIKE":
            return self._check_volume_spike(stock_data, historical_data, rule_config)
        elif rule_name == "BREAKOUT":
            return self._check_breakout(stock_data, historical_data, rule_config)
        elif rule_name == "GAP_UP":
            return self._check_gap_up(stock_data, rule_config)
        elif rule_name == "LIMIT_APPROACH":
            return self._check_limit_approach(stock_data, rule_config)
        
        return False
    
    def _check_price_surge(self, stock_data: Dict, config: Dict) -> bool:
        """급등 체크"""
        change_rate = stock_data.get('change_rate', 0)
        return change_rate >= config['threshold']
    
    def _check_volume_spike(
        self, 
        stock_data: Dict, 
        historical_data: pd.DataFrame,
        config: Dict
    ) -> bool:
        """거래량 급증 체크"""
        if len(historical_data) < 20:
            return False
            
        current_volume = stock_data.get('volume', 0)
        avg_volume = historical_data['volume'].iloc[-20:].mean()
        
        if avg_volume > 0:
            volume_ratio = (current_volume / avg_volume) * 100
            return volume_ratio >= config['threshold']
            
        return False
    
    def _create_alert(
        self,
        stock_code: str,
        stock_name: str,
        alert_type: str,
        data: Dict,
        priority: str
    ) -> Dict:
        """알림 생성"""
        return {
            "alert_id": f"{datetime.now().strftime('%Y%m%d%H%M%S')}{stock_code}",
            "timestamp": datetime.now(),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "alert_type": alert_type,
            "priority": priority,
            "data": data,
            "message": self._generate_alert_message(alert_type, stock_name, data)
        }
    
    def _generate_alert_message(
        self, 
        alert_type: str, 
        stock_name: str, 
        data: Dict
    ) -> str:
        """알림 메시지 생성"""
        messages = {
            "PRICE_SURGE": f"{stock_name} 급등! {data.get('change_rate', 0):.1f}% 상승",
            "VOLUME_SPIKE": f"{stock_name} 거래량 폭증! 평균 대비 {data.get('volume_ratio', 0):.0f}%",
            "BREAKOUT": f"{stock_name} 주요 저항선 돌파! 현재가 {data.get('current_price', 0):,}원",
            "GAP_UP": f"{stock_name} 갭상승 시작! {data.get('gap_rate', 0):.1f}% 갭",
            "LIMIT_APPROACH": f"{stock_name} 상한가 임박! 현재 {data.get('change_rate', 0):.1f}% 상승"
        }
        
        return messages.get(alert_type, f"{stock_name} {alert_type} 알림")
```

## 5. 캐싱 전략

```python
# src/utils/cache.py
from typing import Dict, Any, Optional, Set
from datetime import datetime, timedelta
import asyncio
from collections import OrderedDict

class PriceRankingCache:
    """가격 순위 전용 캐싱 시스템"""
    
    def __init__(self, max_size: int = 10000):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.hot_stocks: Set[str] = set()  # 자주 조회되는 종목
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        
    async def get_or_compute(
        self,
        key: str,
        compute_func,
        ttl: int = 30,  # 기본 30초 (실시간성 중요)
        is_hot: bool = False
    ) -> Any:
        """캐시 조회 또는 계산"""
        
        # Hot 데이터는 더 긴 TTL
        if is_hot or key in self.hot_stocks:
            ttl = ttl * 2
            
        # 캐시 확인
        if key in self.cache:
            entry = self.cache[key]
            if entry['expires'] > datetime.now():
                self.cache_stats['hits'] += 1
                # LRU 업데이트
                self.cache.move_to_end(key)
                return entry['data']
            else:
                # 만료된 항목 제거
                del self.cache[key]
                
        # 캐시 미스
        self.cache_stats['misses'] += 1
        
        # 데이터 계산
        data = await compute_func()
        
        # 캐시 저장
        self._set(key, data, ttl)
        
        # Hot 종목 추적
        if self.cache_stats['hits'] > 100:  # 100회 이상 조회 후
            hit_rate = self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses'])
            if hit_rate > 0.8:  # 80% 이상 히트율
                self.hot_stocks.add(key)
                
        return data
        
    def _set(self, key: str, data: Any, ttl: int):
        """캐시 저장"""
        # 크기 제한 확인
        while len(self.cache) >= self.max_size:
            # LRU 제거
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
            self.cache_stats['evictions'] += 1
            
        self.cache[key] = {
            'data': data,
            'expires': datetime.now() + timedelta(seconds=ttl),
            'access_count': 0
        }
        
    def invalidate_pattern(self, pattern: str):
        """패턴 기반 캐시 무효화"""
        keys_to_remove = [k for k in self.cache.keys() if pattern in k]
        for key in keys_to_remove:
            del self.cache[key]
            
    def get_hot_stocks(self) -> List[str]:
        """인기 종목 목록 반환"""
        return list(self.hot_stocks)
```

## 6. 성능 최적화

```python
# src/utils/calculator.py
import numpy as np
from numba import jit
from typing import Tuple, List
import pandas as pd

class OptimizedCalculator:
    """최적화된 계산 유틸리티"""
    
    @staticmethod
    @jit(nopython=True)
    def calculate_change_rates(
        current_prices: np.ndarray,
        previous_prices: np.ndarray
    ) -> np.ndarray:
        """벡터화된 변화율 계산"""
        return ((current_prices - previous_prices) / previous_prices) * 100
    
    @staticmethod
    @jit(nopython=True)
    def find_consecutive_moves(
        prices: np.ndarray,
        min_consecutive: int = 3
    ) -> Tuple[np.ndarray, np.ndarray]:
        """연속 상승/하락 찾기 (최적화)"""
        n = len(prices)
        up_counts = np.zeros(n, dtype=np.int32)
        down_counts = np.zeros(n, dtype=np.int32)
        
        for i in range(1, n):
            if prices[i] > prices[i-1]:
                up_counts[i] = up_counts[i-1] + 1
                down_counts[i] = 0
            elif prices[i] < prices[i-1]:
                down_counts[i] = down_counts[i-1] + 1
                up_counts[i] = 0
            else:
                up_counts[i] = up_counts[i-1]
                down_counts[i] = down_counts[i-1]
                
        return up_counts, down_counts
    
    @staticmethod
    def calculate_volatility_vectorized(
        high_prices: pd.Series,
        low_prices: pd.Series,
        close_prices: pd.Series,
        period: int = 20
    ) -> pd.Series:
        """벡터화된 변동성 계산"""
        # Parkinson 변동성
        hl_ratio = np.log(high_prices / low_prices)
        volatility = np.sqrt(252 / (4 * np.log(2))) * hl_ratio.rolling(period).std()
        
        return volatility * 100  # 퍼센트로 변환
    
    @staticmethod
    def batch_calculate_indicators(
        stocks_data: List[pd.DataFrame],
        indicator_func,
        **kwargs
    ) -> List[Any]:
        """배치 지표 계산"""
        results = []
        
        # 병렬 처리 가능한 경우
        for data in stocks_data:
            result = indicator_func(data, **kwargs)
            results.append(result)
            
        return results
```

## 7. 구현 일정

### Phase 1: 기초 구현 (4일)
- [ ] 프로젝트 구조 설정
- [ ] MCP 서버 기본 설정
- [ ] 한국투자증권 API 클라이언트 구현
- [ ] 기본 가격 순위 도구 구현

### Phase 2: 핵심 기능 (5일)
- [ ] 7개 주요 도구 구현
- [ ] 가격 분석 엔진 구현
- [ ] 패턴 감지기 구현
- [ ] 알림 시스템 구현

### Phase 3: 고도화 (4일)
- [ ] 기술적 지표 통합
- [ ] 실시간 알림 최적화
- [ ] 성능 최적화 (벡터화, 병렬처리)
- [ ] 캐싱 전략 구현

### Phase 4: 테스트 및 배포 (2일)
- [ ] 단위 테스트 작성
- [ ] 통합 테스트
- [ ] 문서화
- [ ] Docker 배포 준비

## 8. 테스트 계획

### 8.1 단위 테스트

```python
# tests/test_analyzer.py
import pytest
import pandas as pd
import numpy as np
from src.analysis.price_analyzer import PriceAnalyzer
from src.analysis.pattern_detector import PatternDetector

class TestPriceAnalyzer:
    @pytest.fixture
    def sample_data(self):
        """테스트용 샘플 데이터"""
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        data = pd.DataFrame({
            'open': np.random.uniform(50000, 51000, 30),
            'high': np.random.uniform(51000, 52000, 30),
            'low': np.random.uniform(49000, 50000, 30),
            'close': np.random.uniform(50000, 51000, 30),
            'volume': np.random.uniform(1000000, 2000000, 30)
        }, index=dates)
        return data
    
    @pytest.mark.asyncio
    async def test_analyze_price_action(self, sample_data):
        """가격 분석 테스트"""
        analyzer = PriceAnalyzer()
        result = await analyzer.analyze_price_action("005930", sample_data)
        
        assert 'price_metrics' in result
        assert 'technical_indicators' in result
        assert 'patterns' in result
        assert 'composite_score' in result
        
    def test_pattern_detection(self, sample_data):
        """패턴 감지 테스트"""
        detector = PatternDetector()
        
        # 상승 추세 데이터 생성
        sample_data['close'] = sample_data['close'] * np.linspace(1, 1.2, 30)
        
        patterns = detector.detect_all_patterns(sample_data)
        assert len(patterns) > 0
        assert all(hasattr(p, 'confidence') for p in patterns)

@pytest.mark.asyncio
async def test_alert_generation():
    """알림 생성 테스트"""
    from src.analysis.alert_manager import AlertManager
    
    manager = AlertManager()
    
    stock_data = {
        'stock_code': '005930',
        'stock_name': '삼성전자',
        'change_rate': 5.5,
        'volume': 30000000,
        'current_price': 78500
    }
    
    alerts = await manager.check_alerts(stock_data, pd.DataFrame())
    assert any(alert['alert_type'] == 'PRICE_SURGE' for alert in alerts)
```

### 8.2 통합 테스트

```python
# tests/test_integration.py
import pytest
from src.server import PriceRankingMCPServer

@pytest.mark.asyncio
async def test_full_ranking_flow():
    """전체 순위 조회 플로우 테스트"""
    server = PriceRankingMCPServer()
    
    # 상승률 순위 조회
    result = await server.get_price_change_ranking(
        ranking_type="TOP_GAINERS",
        market="ALL",
        count=10
    )
    
    assert 'ranking' in result
    assert len(result['ranking']) <= 10
    assert all('change_rate' in item for item in result['ranking'])
    
    # 순위가 올바르게 정렬되었는지 확인
    rates = [item['change_rate'] for item in result['ranking']]
    assert rates == sorted(rates, reverse=True)

@pytest.mark.asyncio
async def test_real_time_alerts():
    """실시간 알림 테스트"""
    server = PriceRankingMCPServer()
    
    # 알림 조회
    alerts = await server.get_price_alerts(
        alert_types=["BREAKOUT", "UNUSUAL_MOVE"],
        time_window=30
    )
    
    assert 'alerts' in alerts
    assert 'alert_summary' in alerts
```

## 9. 배포 및 운영

### 9.1 환경 설정

```bash
# .env 파일
KOREA_INVESTMENT_APP_KEY=your_app_key
KOREA_INVESTMENT_APP_SECRET=your_app_secret
CACHE_TTL_SECONDS=30
LOG_LEVEL=INFO
ALERT_WEBHOOK_URL=https://your-webhook-url
MAX_ALERTS_PER_MINUTE=100
UNUSUAL_MOVE_THRESHOLD=5.0
```

### 9.2 Docker 설정

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# TA-Lib 설치
RUN pip install numpy && \
    pip install TA-Lib

# Python 의존성 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 코드 복사
COPY . .

# 실행
CMD ["python", "-m", "src.server"]
```

### 9.3 Docker Compose 설정

```yaml
# docker-compose.yml
version: '3.8'

services:
  mcp-price-ranking:
    build: .
    container_name: mcp-price-ranking
    environment:
      - KOREA_INVESTMENT_APP_KEY=${KOREA_INVESTMENT_APP_KEY}
      - KOREA_INVESTMENT_APP_SECRET=${KOREA_INVESTMENT_APP_SECRET}
      - REDIS_URL=redis://redis:6379
    ports:
      - "8082:8080"
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
    depends_on:
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

## 10. 모니터링 및 유지보수

### 10.1 실시간 모니터링

```python
# src/utils/monitoring.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import asyncio

@dataclass
class RealtimeMetrics:
    """실시간 메트릭"""
    timestamp: datetime
    active_alerts: int
    ranking_requests_per_minute: int
    average_response_time: float
    cache_hit_rate: float
    hot_stocks: List[str]
    error_rate: float

class RealtimeMonitor:
    """실시간 모니터링"""
    
    def __init__(self):
        self.metrics_buffer = []
        self.alert_counter = 0
        self.request_counter = 0
        self.response_times = []
        
    async def collect_metrics(self) -> RealtimeMetrics:
        """메트릭 수집"""
        current_time = datetime.now()
        
        # 1분간 평균 계산
        recent_responses = [
            t for t in self.response_times 
            if (current_time - t['timestamp']).seconds < 60
        ]
        
        avg_response_time = (
            sum(r['duration'] for r in recent_responses) / len(recent_responses)
            if recent_responses else 0
        )
        
        metrics = RealtimeMetrics(
            timestamp=current_time,
            active_alerts=self.alert_counter,
            ranking_requests_per_minute=self.request_counter,
            average_response_time=avg_response_time,
            cache_hit_rate=self._calculate_cache_hit_rate(),
            hot_stocks=self._get_hot_stocks(),
            error_rate=self._calculate_error_rate()
        )
        
        self.metrics_buffer.append(metrics)
        
        # 메트릭 리셋
        if len(self.metrics_buffer) > 60:  # 1시간 데이터 유지
            self.metrics_buffer = self.metrics_buffer[-60:]
            
        return metrics
    
    async def check_health(self) -> Dict:
        """시스템 건강 상태 체크"""
        metrics = await self.collect_metrics()
        
        health_status = {
            "status": "healthy",
            "issues": []
        }
        
        # 응답 시간 체크
        if metrics.average_response_time > 2.0:
            health_status["issues"].append({
                "type": "SLOW_RESPONSE",
                "message": f"평균 응답 시간 초과: {metrics.average_response_time:.2f}초"
            })
            
        # 에러율 체크
        if metrics.error_rate > 0.05:
            health_status["issues"].append({
                "type": "HIGH_ERROR_RATE",
                "message": f"높은 에러율: {metrics.error_rate:.1%}"
            })
            
        # 캐시 효율성 체크
        if metrics.cache_hit_rate < 0.5:
            health_status["issues"].append({
                "type": "LOW_CACHE_HIT",
                "message": f"낮은 캐시 히트율: {metrics.cache_hit_rate:.1%}"
            })
            
        if health_status["issues"]:
            health_status["status"] = "unhealthy"
            
        return health_status
```

### 10.2 로그 집계 및 분석

```python
# src/utils/log_aggregator.py
from collections import defaultdict
from datetime import datetime, timedelta
import json

class LogAggregator:
    """로그 집계 및 분석"""
    
    def __init__(self):
        self.alert_stats = defaultdict(int)
        self.stock_access_count = defaultdict(int)
        self.error_patterns = defaultdict(list)
        
    def aggregate_daily_stats(self, log_file: str) -> Dict:
        """일별 통계 집계"""
        stats = {
            "date": datetime.now().date().isoformat(),
            "total_requests": 0,
            "unique_stocks": set(),
            "alert_distribution": {},
            "peak_hours": [],
            "error_summary": {}
        }
        
        hourly_requests = defaultdict(int)
        
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    log_data = json.loads(line)
                    
                    # 요청 수 집계
                    stats["total_requests"] += 1
                    
                    # 시간별 집계
                    hour = datetime.fromisoformat(log_data['timestamp']).hour
                    hourly_requests[hour] += 1
                    
                    # 종목별 집계
                    if 'stock_code' in log_data:
                        stats["unique_stocks"].add(log_data['stock_code'])
                        self.stock_access_count[log_data['stock_code']] += 1
                        
                    # 알림 집계
                    if 'alert_type' in log_data:
                        self.alert_stats[log_data['alert_type']] += 1
                        
                except Exception as e:
                    continue
                    
        # 통계 정리
        stats["unique_stocks"] = len(stats["unique_stocks"])
        stats["alert_distribution"] = dict(self.alert_stats)
        stats["peak_hours"] = sorted(
            hourly_requests.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        
        # 인기 종목 TOP 10
        stats["hot_stocks"] = sorted(
            self.stock_access_count.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return stats
```

### 10.3 알림 및 보고

- 실시간 알림 (Webhook/Slack)
- 일별 리포트 생성
- 주간 트렌드 분석
- 이상 패턴 감지 알림

## 11. 보안 고려사항

### 11.1 API 보안
- API 키 암호화 저장
- Rate limiting (분당 요청 제한)
- IP 화이트리스트

### 11.2 데이터 보안
- 민감 정보 마스킹
- 로그 데이터 암호화
- 정기적 보안 감사

### 11.3 알림 보안
- Webhook URL 검증
- 알림 내용 필터링
- DDoS 방지 메커니즘

이 계획서를 통해 실시간성과 정확성을 갖춘 상승률 순위 MCP 서버를 구축할 수 있습니다.