"""
캐시 전략
캐시 키 생성, TTL 관리, 무효화 전략
"""

import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from src.utils import setup_logger


@dataclass
class CacheKey:
    """캐시 키 정보"""
    prefix: str
    key: str
    ttl: int
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    @property
    def full_key(self) -> str:
        """전체 캐시 키"""
        return f"{self.prefix}:{self.key}"
    
    def add_tag(self, tag: str) -> None:
        """태그 추가"""
        if tag not in self.tags:
            self.tags.append(tag)


class CacheStrategy:
    """캐시 전략 클래스"""
    
    def __init__(self):
        self.logger = setup_logger(f"{__name__}.{self.__class__.__name__}")
        
        # 기본 TTL 설정 (초)
        self.default_ttls = {
            "ranking": 60,      # 순위 데이터: 1분
            "high_low": 300,    # 52주 고저가: 5분  
            "limit": 30,        # 상한가/하한가: 30초
            "market_summary": 120,  # 시장 요약: 2분
            "stock_price": 10   # 개별 주가: 10초
        }
        
        # 시장 시간 설정
        self.market_open_hour = 9
        self.market_close_hour = 15
        self.market_close_minute = 30
    
    def generate_ranking_key(
        self, 
        ranking_type: str, 
        market: str, 
        count: int = 20,
        **filters
    ) -> CacheKey:
        """순위 데이터 캐시 키 생성"""
        # 필터 조건을 해시화
        filter_hash = self._hash_dict(filters) if filters else "no_filter"
        
        key = f"{ranking_type}:{market}:{count}:{filter_hash}"
        ttl = self._get_dynamic_ttl("ranking")
        
        cache_key = CacheKey(
            prefix="ranking",
            key=key,
            ttl=ttl,
            tags=["market_data", "ranking", market.lower()]
        )
        
        return cache_key
    
    def generate_high_low_key(
        self,
        type_param: str,
        market: str,
        count: int = 20,
        breakthrough_only: bool = True
    ) -> CacheKey:
        """52주 고저가 캐시 키 생성"""
        key = f"{type_param}:{market}:{count}:{breakthrough_only}"
        ttl = self._get_dynamic_ttl("high_low")
        
        cache_key = CacheKey(
            prefix="high_low",
            key=key,
            ttl=ttl,
            tags=["market_data", "high_low", market.lower()]
        )
        
        return cache_key
    
    def generate_limit_key(
        self,
        limit_type: str,
        market: str,
        include_history: bool = True
    ) -> CacheKey:
        """상한가/하한가 캐시 키 생성"""
        key = f"{limit_type}:{market}:{include_history}"
        ttl = self._get_dynamic_ttl("limit")
        
        cache_key = CacheKey(
            prefix="limit",
            key=key,
            ttl=ttl,
            tags=["market_data", "limit", market.lower()]
        )
        
        return cache_key
    
    def generate_stock_price_key(self, stock_code: str) -> CacheKey:
        """개별 주가 캐시 키 생성"""
        key = stock_code
        ttl = self._get_dynamic_ttl("stock_price")
        
        cache_key = CacheKey(
            prefix="stock_price",
            key=key,
            ttl=ttl,
            tags=["market_data", "stock_price"]
        )
        
        return cache_key
    
    def generate_market_summary_key(self) -> CacheKey:
        """시장 요약 캐시 키 생성"""
        key = "summary"
        ttl = self._get_dynamic_ttl("market_summary")
        
        cache_key = CacheKey(
            prefix="market_summary",
            key=key,
            ttl=ttl,
            tags=["market_data", "summary"]
        )
        
        return cache_key
    
    def get_ttl_for_market_hours(self) -> int:
        """시장 시간 내 TTL 반환"""
        return 30  # 30초
    
    def get_ttl_for_after_hours(self) -> int:
        """시장 시간 외 TTL 반환"""
        return 1800  # 30분
    
    def should_invalidate_by_time(
        self, 
        cache_time: datetime, 
        max_age_minutes: int
    ) -> bool:
        """시간 기반 캐시 무효화 판단"""
        age = datetime.now() - cache_time
        return age > timedelta(minutes=max_age_minutes)
    
    def should_invalidate_by_event(self, event: str) -> bool:
        """이벤트 기반 캐시 무효화 판단"""
        invalidation_events = {
            "market_open",
            "market_close", 
            "circuit_breaker",
            "system_maintenance"
        }
        return event in invalidation_events
    
    def get_invalidation_patterns(self, event: str) -> List[str]:
        """이벤트별 무효화 패턴 반환"""
        patterns = {
            "market_open": ["ranking:*", "high_low:*", "limit:*", "market_summary:*"],
            "market_close": ["ranking:*", "market_summary:*"],
            "circuit_breaker": ["ranking:*", "stock_price:*"],
            "system_maintenance": ["*"]
        }
        return patterns.get(event, [])
    
    def _get_dynamic_ttl(self, data_type: str) -> int:
        """동적 TTL 계산"""
        base_ttl = self.default_ttls.get(data_type, 300)
        
        # 현재 시간이 시장 시간인지 확인
        now = datetime.now()
        is_market_hours = self._is_market_hours(now)
        
        if is_market_hours:
            # 시장 시간 중에는 TTL을 짧게
            return min(base_ttl, self.get_ttl_for_market_hours())
        else:
            # 시장 시간 외에는 TTL을 길게
            return max(base_ttl, self.get_ttl_for_after_hours())
    
    def _is_market_hours(self, dt: datetime) -> bool:
        """시장 시간 여부 확인"""
        # 주말 제외
        if dt.weekday() >= 5:  # 토요일(5), 일요일(6)
            return False
        
        # 시장 시간 확인 (9:00 ~ 15:30)
        if dt.hour < self.market_open_hour:
            return False
        if dt.hour > self.market_close_hour:
            return False
        if dt.hour == self.market_close_hour and dt.minute > self.market_close_minute:
            return False
        
        return True
    
    def _hash_dict(self, data: Dict[str, Any]) -> str:
        """딕셔너리를 해시화"""
        # 키 정렬하여 일관성 보장
        sorted_items = sorted(data.items())
        hash_input = str(sorted_items).encode('utf-8')
        return hashlib.md5(hash_input).hexdigest()[:8]