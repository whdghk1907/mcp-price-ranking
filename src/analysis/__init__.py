"""
Analysis 패키지
주식 데이터 분석 엔진 및 관련 모듈들
"""

from typing import Dict, Any, List
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AnalysisResult:
    """분석 결과"""
    stock_code: str
    analysis_type: str
    result: Dict[str, Any]
    confidence: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "stock_code": self.stock_code,
            "analysis_type": self.analysis_type,
            "result": self.result,
            "confidence": self.confidence,
            "timestamp": self.timestamp.isoformat()
        }


@dataclass
class Pattern:
    """차트 패턴 정보"""
    name: str
    type: str  # BULLISH, BEARISH, NEUTRAL
    confidence: float
    target_price: float = None
    stop_loss: float = None
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "name": self.name,
            "type": self.type,
            "confidence": self.confidence,
            "target_price": self.target_price,
            "stop_loss": self.stop_loss,
            "description": self.description
        }


class BaseAnalyzer:
    """기본 분석기 클래스"""
    
    def __init__(self, name: str):
        self.name = name
    
    async def analyze(self, data: Dict[str, Any]) -> AnalysisResult:
        """분석 실행 (기본 구현)"""
        return AnalysisResult(
            stock_code=data.get("stock_code", ""),
            analysis_type=self.name,
            result={},
            confidence=0.0,
            timestamp=datetime.now()
        )