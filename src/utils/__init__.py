"""
Utils 패키지
유틸리티 함수 및 헬퍼 클래스들
"""

from typing import Any, Dict, List, Optional
from datetime import datetime
import logging


def setup_logger(name: str, level: str = "INFO") -> logging.Logger:
    """로거 설정 유틸리티"""
    logger = logging.getLogger(name)
    
    # 로그 레벨 설정
    log_level = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(log_level)
    
    # 핸들러가 없으면 추가
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    
    return logger


def validate_stock_code(stock_code: str) -> bool:
    """주식 코드 검증"""
    if not stock_code:
        return False
    
    # 한국 주식 코드는 6자리 숫자
    if len(stock_code) != 6:
        return False
    
    if not stock_code.isdigit():
        return False
    
    return True


def format_price(price: int) -> str:
    """가격 포맷팅 (천단위 콤마)"""
    return f"{price:,}"


def format_change_rate(rate: float) -> str:
    """변화율 포맷팅"""
    sign = "+" if rate > 0 else ""
    return f"{sign}{rate:.2f}%"


def calculate_change_rate(current: float, previous: float) -> float:
    """변화율 계산"""
    if previous == 0:
        return 0.0
    
    return ((current - previous) / previous) * 100


class Timer:
    """실행 시간 측정 유틸리티"""
    
    def __init__(self):
        self.start_time = None
        self.end_time = None
    
    def start(self):
        """측정 시작"""
        self.start_time = datetime.now()
    
    def stop(self) -> float:
        """측정 종료 및 실행 시간 반환 (초)"""
        self.end_time = datetime.now()
        if self.start_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds()
        return 0.0
    
    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        return self.stop()