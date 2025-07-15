# 📈 상승률 순위 MCP 서버 상세 개발계획

## 1. 개발 개요

### 1.1 프로젝트 분석 요약
기존 계획서를 분석한 결과, 한국 주식시장의 가격 변동률 기준 상위/하위 종목을 실시간으로 추적하고 분석하는 MCP 서버 구축이 목표입니다. 7개의 핵심 도구와 고도화된 분석 엔진을 포함한 포괄적인 시스템입니다.

### 1.2 핵심 특징
- **실시간성**: 30초 이내 데이터 업데이트
- **포괄성**: 7개 주요 분석 도구 제공
- **확장성**: MCP 프로토콜 기반 플러그인 아키텍처
- **성능**: 벡터화 연산 및 캐싱 최적화
- **신뢰성**: 포괄적 알림 시스템 및 모니터링

## 2. 단계별 개발 계획

### Phase 1: 기반 구조 구축 (4일)

#### Day 1: 프로젝트 초기화 및 환경 설정
**목표**: 개발 환경 구성 및 프로젝트 뼈대 구축

**작업 항목**:
1. **프로젝트 구조 생성**
   ```
   mcp-price-ranking/
   ├── src/
   │   ├── __init__.py
   │   ├── server.py
   │   ├── tools/
   │   ├── api/
   │   ├── analysis/
   │   ├── utils/
   │   ├── config.py
   │   └── exceptions.py
   ├── tests/
   ├── requirements.txt
   ├── .env.example
   └── README.md
   ```

2. **의존성 설정**
   ```python
   # requirements.txt 주요 패키지
   mcp-python>=0.5.0
   aiohttp>=3.9.0
   pandas>=2.1.0
   numpy>=1.24.0
   TA-Lib>=0.4.0
   pydantic>=2.4.0
   redis>=5.0.0
   numba>=0.58.0
   python-dotenv>=1.0.0
   pytest>=7.4.0
   pytest-asyncio>=0.21.0
   ```

3. **기본 설정 파일 구성**
   - `.env.example` 템플릿 작성
   - `config.py` 설정 관리 클래스 구현
   - `exceptions.py` 커스텀 예외 정의

**완료 기준**:
- [ ] 프로젝트 구조 완성
- [ ] 가상환경 및 의존성 설치 완료
- [ ] 기본 설정 파일 작성 완료
- [ ] Git 리포지토리 초기화

#### Day 2: MCP 서버 기본 구현
**목표**: MCP 서버 뼈대 구성 및 기본 통신 확립

**작업 항목**:
1. **MCP 서버 기본 클래스 구현**
   ```python
   # src/server.py
   from mcp.server import MCPServer
   from mcp.tools import Tool
   
   class PriceRankingMCPServer(MCPServer):
       def __init__(self):
           super().__init__("price-ranking-server")
           self.register_tools()
           
       def register_tools(self):
           # 도구 등록 로직
           pass
   ```

2. **기본 도구 인터페이스 정의**
   ```python
   # src/tools/__init__.py
   from abc import ABC, abstractmethod
   
   class BaseTool(ABC):
       @abstractmethod
       async def execute(self, **kwargs):
           pass
   ```

3. **헬스체크 엔드포인트 구현**
   - 서버 상태 확인 API
   - 기본 응답 확인

**완료 기준**:
- [ ] MCP 서버 기본 클래스 구현
- [ ] 서버 시작/종료 로직 완성
- [ ] 기본 헬스체크 작동 확인

#### Day 3: API 클라이언트 구현
**목표**: 한국투자증권 OpenAPI 연동 기반 구축

**작업 항목**:
1. **API 클라이언트 기본 클래스**
   ```python
   # src/api/client.py
   import aiohttp
   from typing import Dict, Any
   
   class KoreaInvestmentAPIClient:
       def __init__(self, app_key: str, app_secret: str):
           self.app_key = app_key
           self.app_secret = app_secret
           self.session = None
           self.access_token = None
           
       async def authenticate(self):
           # OAuth 인증 로직
           pass
           
       async def get_stock_price(self, stock_code: str):
           # 주식 가격 조회
           pass
           
       async def get_market_data(self):
           # 시장 데이터 조회
           pass
   ```

2. **데이터 모델 정의**
   ```python
   # src/api/models.py
   from pydantic import BaseModel
   from typing import Optional, List
   from datetime import datetime
   
   class StockPrice(BaseModel):
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
   
   class MarketSummary(BaseModel):
       total_stocks: int
       advancing: int
       declining: int
       unchanged: int
       average_change_rate: float
   ```

3. **API 상수 정의**
   ```python
   # src/api/constants.py
   API_BASE_URL = "https://openapi.koreainvestment.com:9443"
   
   ENDPOINTS = {
       "TOKEN": "/oauth2/tokenP",
       "STOCK_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-price",
       "STOCK_RANKING": "/uapi/domestic-stock/v1/ranking/fluctuation",
   }
   
   MARKETS = {
       "KOSPI": "J",
       "KOSDAQ": "Q",
       "ALL": ""
   }
   ```

**완료 기준**:
- [ ] API 클라이언트 기본 구조 완성
- [ ] 인증 로직 구현 및 테스트
- [ ] 기본 데이터 조회 API 작동 확인
- [ ] 데이터 모델 검증 완료

#### Day 4: 첫 번째 도구 구현
**목표**: `get_price_change_ranking` 도구 완전 구현

**작업 항목**:
1. **가격 순위 도구 구현**
   ```python
   # src/tools/price_ranking_tools.py
   from mcp.tools import tool
   from typing import Literal, Optional
   
   @tool
   async def get_price_change_ranking(
       ranking_type: Literal["TOP_GAINERS", "TOP_LOSERS", "MOST_VOLATILE"] = "TOP_GAINERS",
       market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
       count: int = 20,
       min_price: Optional[int] = None,
       min_volume: Optional[int] = None
   ) -> dict:
       """가격 변동률 기준 순위 조회"""
       # 구현 로직
       pass
   ```

2. **데이터 검증 및 필터링**
   ```python
   # src/utils/validator.py
   class DataValidator:
       @staticmethod
       def validate_stock_data(data: dict) -> bool:
           required_fields = ['stock_code', 'current_price', 'change_rate']
           return all(field in data for field in required_fields)
           
       @staticmethod
       def apply_filters(data: list, min_price: int, min_volume: int) -> list:
           # 필터링 로직
           pass
   ```

3. **기본 캐싱 구현**
   ```python
   # src/utils/cache.py (기본 버전)
   from typing import Dict, Any
   from datetime import datetime, timedelta
   
   class SimpleCache:
       def __init__(self):
           self._cache = {}
           
       async def get(self, key: str):
           # 캐시 조회
           pass
           
       async def set(self, key: str, value: Any, ttl: int = 30):
           # 캐시 저장
           pass
   ```

**완료 기준**:
- [ ] 첫 번째 도구 완전 작동
- [ ] 실제 API 데이터로 테스트 완료
- [ ] 기본 캐싱 적용 및 검증
- [ ] 에러 핸들링 구현

### Phase 2: 핵심 기능 개발 (5일)

#### Day 5: 52주 신고가/신저가 도구 구현
**목표**: `get_52week_high_low` 도구 구현

**작업 항목**:
1. **52주 데이터 처리 로직**
   ```python
   # src/tools/high_low_tools.py
   async def get_52week_high_low(
       type: Literal["HIGH", "LOW", "BOTH"] = "BOTH",
       market: Literal["ALL", "KOSPI", "KOSDAQ"] = "ALL",
       count: int = 20,
       breakthrough_only: bool = True
   ) -> dict:
       """52주 신고가/신저가 종목 조회"""
       # 구현 로직
       pass
   ```

2. **돌파 감지 알고리즘**
   ```python
   def detect_52week_breakthrough(current_price: float, high_52w: float, low_52w: float) -> dict:
       breakthrough_info = {
           "is_new_high": current_price >= high_52w * 0.999,
           "is_new_low": current_price <= low_52w * 1.001,
           "distance_from_high": ((current_price - high_52w) / high_52w) * 100,
           "distance_from_low": ((current_price - low_52w) / low_52w) * 100
       }
       return breakthrough_info
   ```

**완료 기준**:
- [ ] 52주 신고가/신저가 정확 계산
- [ ] 돌파 감지 로직 검증
- [ ] 모멘텀 점수 계산 구현

#### Day 6: 상한가/하한가 도구 구현
**목표**: `get_limit_stocks` 도구 구현

**작업 항목**:
1. **상한가/하한가 계산 로직**
   ```python
   # src/tools/limit_tools.py
   def calculate_limit_price(previous_close: int, market_type: str) -> tuple:
       """상한가/하한가 계산"""
       if market_type == "KOSPI":
           limit_rate = 0.30  # 30%
       else:  # KOSDAQ
           limit_rate = 0.30
           
       upper_limit = int(previous_close * (1 + limit_rate))
       lower_limit = int(previous_close * (1 - limit_rate))
       
       return upper_limit, lower_limit
   ```

2. **연속 상한가 추적**
   ```python
   def track_consecutive_limits(stock_code: str, price_history: list) -> dict:
       consecutive_count = 0
       for price_data in reversed(price_history):
           if is_limit_price(price_data):
               consecutive_count += 1
           else:
               break
       return {"consecutive_days": consecutive_count}
   ```

**완료 기준**:
- [ ] 상한가/하한가 정확 계산
- [ ] 연속 상한가 추적 로직
- [ ] 해제 확률 예측 모델

#### Day 7: 연속 상승/하락 및 갭 주식 도구 구현
**목표**: `get_consecutive_moves`, `get_gap_stocks` 도구 구현

**작업 항목**:
1. **연속 움직임 감지**
   ```python
   # src/tools/consecutive_tools.py
   from src.utils.calculator import OptimizedCalculator
   
   async def analyze_consecutive_moves(price_data: list, min_days: int) -> list:
       """연속 상승/하락 분석"""
       calculator = OptimizedCalculator()
       prices = np.array([p['close'] for p in price_data])
       up_counts, down_counts = calculator.find_consecutive_moves(prices, min_days)
       
       # 결과 처리
       return process_consecutive_results(up_counts, down_counts, price_data)
   ```

2. **갭 계산 및 분석**
   ```python
   def calculate_gap_info(open_price: float, previous_close: float) -> dict:
       gap_size = open_price - previous_close
       gap_rate = (gap_size / previous_close) * 100
       
       return {
           "gap_size": gap_size,
           "gap_rate": gap_rate,
           "gap_type": "UP" if gap_rate > 0 else "DOWN",
           "is_significant": abs(gap_rate) >= 3.0
       }
   ```

**완료 기준**:
- [ ] 연속 움직임 정확 감지
- [ ] 갭 계산 및 메우기 확률 예측
- [ ] 성능 최적화 적용

#### Day 8-9: 변동성 분석 및 실시간 알림 시스템
**목표**: `get_volatility_ranking`, `get_price_alerts` 도구 구현

**작업 항목**:
1. **변동성 계산 엔진**
   ```python
   # src/analysis/volatility_engine.py
   import talib
   
   class VolatilityEngine:
       def calculate_historical_volatility(self, prices: pd.Series, period: int = 20) -> float:
           returns = prices.pct_change().dropna()
           volatility = returns.rolling(period).std() * np.sqrt(252) * 100
           return volatility.iloc[-1]
           
       def calculate_parkinson_volatility(self, high: pd.Series, low: pd.Series) -> float:
           hl_ratio = np.log(high / low)
           volatility = np.sqrt(252 / (4 * np.log(2))) * hl_ratio.std() * 100
           return volatility
   ```

2. **실시간 알림 시스템**
   ```python
   # src/analysis/alert_manager.py (확장)
   class RealtimeAlertSystem:
       def __init__(self):
           self.alert_queue = asyncio.Queue()
           self.active_alerts = {}
           
       async def process_market_data(self, market_data: list):
           """시장 데이터 실시간 처리"""
           for stock_data in market_data:
               alerts = await self.check_alert_conditions(stock_data)
               for alert in alerts:
                   await self.alert_queue.put(alert)
   ```

**완료 기준**:
- [ ] 다양한 변동성 지표 계산
- [ ] 실시간 알림 큐 시스템
- [ ] 알림 우선순위 및 필터링

### Phase 3: 고도화 및 최적화 (4일)

#### Day 10: 가격 분석 엔진 완성
**목표**: 포괄적인 기술적 분석 엔진 구현

**작업 항목**:
1. **기술적 지표 통합**
   ```python
   # src/analysis/technical_indicators.py
   class TechnicalIndicatorEngine:
       def __init__(self):
           self.indicators = {}
           
       def calculate_all_indicators(self, price_data: pd.DataFrame) -> dict:
           indicators = {}
           
           # 이동평균
           indicators.update(self._calculate_moving_averages(price_data))
           
           # 모멘텀 지표
           indicators.update(self._calculate_momentum_indicators(price_data))
           
           # 변동성 지표
           indicators.update(self._calculate_volatility_indicators(price_data))
           
           # 거래량 지표
           indicators.update(self._calculate_volume_indicators(price_data))
           
           return indicators
   ```

2. **패턴 인식 고도화**
   ```python
   # src/analysis/advanced_patterns.py
   class AdvancedPatternDetector:
       def detect_complex_patterns(self, data: pd.DataFrame) -> list:
           patterns = []
           
           # 삼각수렴 패턴
           patterns.extend(self.detect_triangle_convergence(data))
           
           # 헤드앤숄더 패턴
           patterns.extend(self.detect_head_and_shoulders(data))
           
           # 이중천정/이중바닥
           patterns.extend(self.detect_double_patterns(data))
           
           return patterns
   ```

**완료 기준**:
- [ ] 20+ 기술적 지표 구현
- [ ] 복합 패턴 인식 시스템
- [ ] 신호 강도 점수화

#### Day 11: 성능 최적화
**목표**: 대용량 데이터 처리 최적화

**작업 항목**:
1. **벡터화 연산 적용**
   ```python
   # src/utils/optimized_calculator.py (확장)
   from numba import jit, prange
   
   @jit(nopython=True, parallel=True)
   def vectorized_change_rate_calculation(current_prices, previous_prices):
       n = len(current_prices)
       change_rates = np.empty(n)
       
       for i in prange(n):
           if previous_prices[i] != 0:
               change_rates[i] = ((current_prices[i] - previous_prices[i]) / previous_prices[i]) * 100
           else:
               change_rates[i] = 0.0
               
       return change_rates
   ```

2. **메모리 최적화**
   ```python
   # src/utils/memory_optimizer.py
   class MemoryOptimizer:
       def __init__(self):
           self.memory_pool = {}
           
       def optimize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
           # 데이터 타입 최적화
           for col in df.select_dtypes(include=['int64']):
               df[col] = pd.to_numeric(df[col], downcast='integer')
               
           for col in df.select_dtypes(include=['float64']):
               df[col] = pd.to_numeric(df[col], downcast='float')
               
           return df
   ```

**완료 기준**:
- [ ] 50% 이상 연산 속도 향상
- [ ] 메모리 사용량 30% 절감
- [ ] 동시 처리 성능 향상

#### Day 12: 고급 캐싱 시스템
**목표**: 다층 캐싱 및 예측적 캐싱 구현

**작업 항목**:
1. **Redis 기반 분산 캐싱**
   ```python
   # src/utils/distributed_cache.py
   import redis.asyncio as redis
   
   class DistributedCache:
       def __init__(self, redis_url: str):
           self.redis = redis.from_url(redis_url)
           self.local_cache = {}
           
       async def get_with_fallback(self, key: str):
           # 로컬 캐시 우선 확인
           if key in self.local_cache:
               return self.local_cache[key]
               
           # Redis 캐시 확인
           value = await self.redis.get(key)
           if value:
               self.local_cache[key] = value
               return value
               
           return None
   ```

2. **예측적 캐싱**
   ```python
   class PredictiveCache:
       def __init__(self):
           self.access_patterns = {}
           
       def predict_next_requests(self, current_request: str) -> list:
           # 접근 패턴 기반 예측
           patterns = self.access_patterns.get(current_request, [])
           return sorted(patterns, key=lambda x: x['frequency'], reverse=True)[:5]
   ```

**완료 기준**:
- [ ] 다층 캐싱 시스템 구현
- [ ] 캐시 히트율 80% 이상 달성
- [ ] 예측적 캐싱 적용

#### Day 13: 모니터링 및 관찰성
**목표**: 포괄적인 모니터링 시스템 구축

**작업 항목**:
1. **메트릭 수집 시스템**
   ```python
   # src/monitoring/metrics_collector.py
   from dataclasses import dataclass
   from typing import Dict, List
   import time
   
   @dataclass
   class PerformanceMetrics:
       timestamp: float
       request_count: int
       average_response_time: float
       cache_hit_rate: float
       error_rate: float
       memory_usage: float
       cpu_usage: float
   
   class MetricsCollector:
       def __init__(self):
           self.metrics_history = []
           self.current_metrics = {}
           
       async def collect_system_metrics(self) -> PerformanceMetrics:
           # 시스템 메트릭 수집
           pass
   ```

2. **알림 및 대시보드**
   ```python
   # src/monitoring/dashboard.py
   class RealtimeDashboard:
       def __init__(self):
           self.widgets = []
           
       def generate_dashboard_data(self) -> dict:
           return {
               "system_health": self.get_system_health(),
               "active_alerts": self.get_active_alerts(),
               "performance_charts": self.get_performance_charts(),
               "hot_stocks": self.get_trending_stocks()
           }
   ```

**완료 기준**:
- [ ] 실시간 메트릭 수집
- [ ] 성능 대시보드 구현
- [ ] 자동 알림 시스템

### Phase 4: 테스트 및 배포 준비 (2일)

#### Day 14: 포괄적 테스트
**목표**: 전체 시스템 테스트 및 검증

**작업 항목**:
1. **단위 테스트 완성**
   ```python
   # tests/test_comprehensive.py
   import pytest
   from unittest.mock import Mock, patch
   
   class TestFullSystem:
       @pytest.mark.asyncio
       async def test_end_to_end_ranking(self):
           # 전체 플로우 테스트
           pass
           
       @pytest.mark.asyncio
       async def test_high_load_performance(self):
           # 부하 테스트
           pass
           
       @pytest.mark.asyncio
       async def test_error_recovery(self):
           # 오류 복구 테스트
           pass
   ```

2. **성능 벤치마크**
   ```python
   # tests/performance_benchmark.py
   import asyncio
   import time
   
   async def benchmark_ranking_performance():
       start_time = time.time()
       
       # 1000개 동시 요청 테스트
       tasks = []
       for _ in range(1000):
           task = asyncio.create_task(call_ranking_api())
           tasks.append(task)
           
       results = await asyncio.gather(*tasks)
       
       end_time = time.time()
       avg_response_time = (end_time - start_time) / len(results)
       
       assert avg_response_time < 2.0  # 2초 이내
   ```

**완료 기준**:
- [ ] 95% 이상 테스트 커버리지
- [ ] 모든 성능 벤치마크 통과
- [ ] 장애 복구 시나리오 검증

#### Day 15: 배포 준비 및 문서화
**목표**: 프로덕션 배포 준비 완료

**작업 항목**:
1. **Docker 컨테이너화**
   ```dockerfile
   # Dockerfile (최적화)
   FROM python:3.11-slim as builder
   
   # 빌드 의존성 설치
   RUN apt-get update && apt-get install -y gcc g++ && \
       pip install --no-cache-dir numpy && \
       pip install --no-cache-dir TA-Lib
   
   FROM python:3.11-slim
   
   # 빌드된 패키지 복사
   COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
   
   WORKDIR /app
   COPY . .
   
   # 헬스체크 추가
   HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
       CMD curl -f http://localhost:8080/health || exit 1
   
   CMD ["python", "-m", "src.server"]
   ```

2. **배포 자동화**
   ```yaml
   # .github/workflows/deploy.yml
   name: Deploy MCP Server
   
   on:
     push:
       branches: [main]
   
   jobs:
     test:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v3
         - name: Run tests
           run: |
             pip install -r requirements.txt
             pytest tests/ -v --cov=src
   
     deploy:
       needs: test
       runs-on: ubuntu-latest
       steps:
         - name: Deploy to production
           run: |
             docker build -t mcp-price-ranking .
             docker push mcp-price-ranking:latest
   ```

**완료 기준**:
- [ ] Docker 이미지 최적화 완료
- [ ] CI/CD 파이프라인 구축
- [ ] 프로덕션 환경 배포 가이드

## 3. 위험 관리 및 대응 계획

### 3.1 기술적 위험
1. **API 요청 제한**
   - **위험**: 한국투자증권 API 호출 제한 초과
   - **대응**: 요청 큐잉 및 백오프 전략 구현

2. **실시간 데이터 지연**
   - **위험**: 네트워크 지연으로 인한 데이터 실시간성 저하
   - **대응**: 다중 데이터 소스 및 캐싱 전략

3. **메모리 부족**
   - **위험**: 대량 데이터 처리 시 메모리 오버플로우
   - **대응**: 스트리밍 처리 및 메모리 풀링

### 3.2 운영 위험
1. **서비스 다운타임**
   - **위험**: 시스템 장애로 인한 서비스 중단
   - **대응**: 헬스체크 및 자동 복구 메커니즘

2. **데이터 품질**
   - **위험**: 잘못된 데이터로 인한 부정확한 분석
   - **대응**: 다층 데이터 검증 시스템

## 4. 성공 지표 및 KPI

### 4.1 성능 지표
- **응답 시간**: 평균 500ms 이하
- **처리량**: 초당 1000 요청 처리
- **가용성**: 99.9% 업타임
- **정확도**: 99.5% 이상 데이터 정확도

### 4.2 사용성 지표
- **캐시 히트율**: 80% 이상
- **알림 정확도**: 90% 이상
- **사용자 만족도**: 4.5/5.0 이상

## 5. 추후 확장 계획

### 5.1 단기 확장 (1-3개월)
- 추가 기술적 지표 (50+)
- 머신러닝 기반 예측 모델
- 모바일 알림 지원

### 5.2 장기 확장 (6-12개월)
- 글로벌 주식 시장 지원
- 암호화폐 시장 데이터
- AI 기반 투자 인사이트

이 상세 개발계획을 통해 체계적이고 단계적인 구현이 가능하며, 각 단계별 명확한 목표와 완료 기준을 제시하여 프로젝트 진행 상황을 효과적으로 관리할 수 있습니다.