"""
API 상수 정의
한국투자증권 OpenAPI 관련 상수들
"""

# API 기본 설정
API_BASE_URL = "https://openapi.koreainvestment.com:9443"
API_VERSION = "v1"

# API 엔드포인트
ENDPOINTS = {
    # 인증 관련
    "TOKEN": "/oauth2/tokenP",
    "REVOKE": "/oauth2/revokeP",
    
    # 주식 기본 정보
    "STOCK_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-price",
    "STOCK_INFO": "/uapi/domestic-stock/v1/quotations/inquire-daily-price",
    
    # 순위 정보
    "STOCK_RANKING": "/uapi/domestic-stock/v1/ranking/fluctuation",
    "VOLUME_RANKING": "/uapi/domestic-stock/v1/ranking/volume",
    "VALUE_RANKING": "/uapi/domestic-stock/v1/ranking/value",
    
    # 시장 정보
    "MARKET_INDEX": "/uapi/domestic-stock/v1/quotations/inquire-index-price",
    "MARKET_SUMMARY": "/uapi/domestic-stock/v1/quotations/inquire-daily-indexchartprice",
    
    # 조건 검색
    "CONDITION_SEARCH": "/uapi/domestic-stock/v1/quotations/inquire-daily-itemchartprice",
    
    # 52주 고/저가
    "HIGH_LOW_PRICE": "/uapi/domestic-stock/v1/quotations/inquire-daily-price"
}

# 시장 구분 코드
MARKETS = {
    "ALL": "",
    "KOSPI": "J",
    "KOSDAQ": "Q",
    "KONEX": "K"
}

# 시장 한글명
MARKET_NAMES = {
    "ALL": "전체",
    "KOSPI": "코스피",
    "KOSDAQ": "코스닥",
    "KONEX": "코넥스"
}

# 순위 유형 코드
RANKING_TYPES = {
    "TOP_GAINERS": "1",      # 상승률 상위
    "TOP_LOSERS": "2",       # 하락률 상위
    "MOST_ACTIVE": "3",      # 거래량 상위
    "MOST_VALUABLE": "4",    # 거래대금 상위
    "MOST_VOLATILE": "5",    # 변동성 상위
    "HIGH_PRICE": "6",       # 고가 상위
    "LOW_PRICE": "7",        # 저가 상위
    "MARKET_CAP": "8"        # 시총 상위
}

# 정렬 방향
SORT_DIRECTIONS = {
    "ASC": "1",   # 오름차순
    "DESC": "2"   # 내림차순
}

# 가격 조건
PRICE_CONDITIONS = {
    "ALL": "0",           # 전체
    "ABOVE_1000": "1",    # 1천원 이상
    "ABOVE_5000": "2",    # 5천원 이상
    "ABOVE_10000": "3",   # 1만원 이상
    "ABOVE_50000": "4",   # 5만원 이상
    "ABOVE_100000": "5"   # 10만원 이상
}

# 거래량 조건
VOLUME_CONDITIONS = {
    "ALL": "0",              # 전체
    "ABOVE_10000": "1",      # 1만주 이상
    "ABOVE_50000": "2",      # 5만주 이상
    "ABOVE_100000": "3",     # 10만주 이상
    "ABOVE_500000": "4",     # 50만주 이상
    "ABOVE_1000000": "5"     # 100만주 이상
}

# 업종 코드 (주요 업종)
SECTORS = {
    "TECHNOLOGY": "Q001",
    "FINANCE": "Q002",
    "CHEMICAL": "Q003",
    "STEEL": "Q004",
    "CONSTRUCTION": "Q005",
    "SHIPBUILDING": "Q006",
    "AUTOMOBILE": "Q007",
    "FOOD": "Q008",
    "TEXTILE": "Q009",
    "PAPER": "Q010",
    "PHARMACEUTICAL": "Q011",
    "RETAIL": "Q012",
    "TRANSPORT": "Q013",
    "COMMUNICATION": "Q014",
    "ENTERTAINMENT": "Q015",
    "UTILITY": "Q016",
    "MANUFACTURING": "Q017",
    "SERVICE": "Q018"
}

# 등락 구분
CHANGE_TYPES = {
    "RISE": "2",      # 상승
    "FALL": "5",      # 하락
    "UNCHANGED": "3"  # 보합
}

# 요청 헤더 설정
DEFAULT_HEADERS = {
    "Content-Type": "application/json; charset=utf-8",
    "Accept": "application/json",
    "User-Agent": "MCP-Price-Ranking/1.0"
}

# API 제한 설정
RATE_LIMITS = {
    "REQUESTS_PER_SECOND": 20,
    "REQUESTS_PER_MINUTE": 1000,
    "REQUESTS_PER_HOUR": 10000,
    "BURST_LIMIT": 5
}

# 타임아웃 설정 (초)
TIMEOUTS = {
    "CONNECT": 10,
    "READ": 30,
    "TOTAL": 60
}

# 재시도 설정
RETRY_CONFIG = {
    "MAX_RETRIES": 3,
    "BACKOFF_FACTOR": 2,
    "RETRY_STATUS_CODES": [429, 500, 502, 503, 504]
}

# 캐시 설정
CACHE_CONFIG = {
    "TOKEN_TTL": 3600,      # 토큰 캐시 1시간
    "PRICE_TTL": 30,        # 가격 정보 30초
    "RANKING_TTL": 60,      # 순위 정보 1분
    "MARKET_TTL": 300       # 시장 정보 5분
}

# 데이터 유효성 검사 설정
VALIDATION_CONFIG = {
    "MAX_STOCK_CODE_LENGTH": 6,
    "MIN_STOCK_CODE_LENGTH": 6,
    "MAX_RANKING_COUNT": 100,
    "MIN_RANKING_COUNT": 1,
    "MAX_PRICE": 1000000,
    "MIN_PRICE": 1
}

# 알림 설정
ALERT_CONFIG = {
    "PRICE_CHANGE_THRESHOLD": 5.0,    # 5% 이상 변동 시 알림
    "VOLUME_SPIKE_THRESHOLD": 300.0,  # 평균 거래량 대비 300% 이상
    "VOLATILITY_THRESHOLD": 10.0,     # 변동성 10% 이상
    "MAX_ALERTS_PER_MINUTE": 100
}

# 한국 주식시장 거래 시간
MARKET_HOURS = {
    "REGULAR_OPEN": "09:00",
    "REGULAR_CLOSE": "15:30",
    "AFTER_HOURS_OPEN": "15:40",
    "AFTER_HOURS_CLOSE": "16:00",
    "TIMEZONE": "Asia/Seoul"
}

# 공휴일 및 휴장일 (예시)
MARKET_HOLIDAYS = [
    "2024-01-01",  # 신정
    "2024-02-09",  # 설날 연휴
    "2024-02-10",  # 설날
    "2024-02-11",  # 설날 연휴
    "2024-02-12",  # 설날 대체공휴일
    "2024-03-01",  # 3.1절
    "2024-04-10",  # 국회의원선거
    "2024-05-05",  # 어린이날
    "2024-05-06",  # 어린이날 대체공휴일
    "2024-05-15",  # 부처님오신날
    "2024-06-06",  # 현충일
    "2024-08-15",  # 광복절
    "2024-09-16",  # 추석 연휴
    "2024-09-17",  # 추석
    "2024-09-18",  # 추석 연휴
    "2024-10-03",  # 개천절
    "2024-10-09",  # 한글날
    "2024-12-25"   # 성탄절
]

# 에러 코드 매핑
ERROR_CODES = {
    "INVALID_TOKEN": "40001",
    "EXPIRED_TOKEN": "40002",
    "INVALID_PARAMETER": "40003",
    "STOCK_NOT_FOUND": "40004",
    "MARKET_CLOSED": "40005",
    "RATE_LIMIT_EXCEEDED": "42901",
    "INTERNAL_ERROR": "50001",
    "SERVICE_UNAVAILABLE": "50003"
}

# 에러 메시지
ERROR_MESSAGES = {
    "INVALID_TOKEN": "유효하지 않은 토큰입니다.",
    "EXPIRED_TOKEN": "토큰이 만료되었습니다.",
    "INVALID_PARAMETER": "잘못된 파라미터입니다.",
    "STOCK_NOT_FOUND": "해당 종목을 찾을 수 없습니다.",
    "MARKET_CLOSED": "시장이 닫혀있습니다.",
    "RATE_LIMIT_EXCEEDED": "요청 제한을 초과했습니다.",
    "INTERNAL_ERROR": "내부 서버 오류입니다.",
    "SERVICE_UNAVAILABLE": "서비스를 사용할 수 없습니다."
}