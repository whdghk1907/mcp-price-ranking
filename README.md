# 📈 MCP Price Ranking Server

한국 주식시장의 가격 변동률 기준 상위/하위 종목을 실시간으로 추적하고 분석하는 MCP 서버입니다.

## 🚀 주요 기능

- **실시간 가격 순위**: 상승률/하락률 상위 종목 추적
- **52주 신고가/신저가**: 새로운 고점/저점 달성 종목 분석
- **상한가/하한가 추적**: 극한 가격 변동 종목 모니터링
- **연속 상승/하락**: 연속적인 가격 움직임 패턴 분석
- **갭 상승/하락**: 시가 갭 발생 종목 추적
- **변동성 분석**: 가격 변동성 상위 종목 식별
- **실시간 알림**: 이상 가격 움직임 실시간 감지

## 🛠️ 기술 스택

- **언어**: Python 3.11+
- **MCP SDK**: mcp-python
- **API**: 한국투자증권 OpenAPI
- **비동기 처리**: asyncio, aiohttp
- **데이터 검증**: pydantic
- **기술적 분석**: TA-Lib, pandas
- **캐싱**: Redis + 메모리 캐시
- **테스트**: pytest, pytest-asyncio

## 📦 설치 및 설정

### 1. 의존성 설치

```bash
# 가상환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 설정

```bash
# 환경 변수 파일 복사
cp .env.example .env

# .env 파일에서 API 키 설정
KOREA_INVESTMENT_APP_KEY=your_actual_app_key
KOREA_INVESTMENT_APP_SECRET=your_actual_app_secret
```

### 3. 서버 실행

```bash
# 개발 모드
python -m src.server

# 또는 직접 실행
python src/server.py
```

## 🧪 테스트

```bash
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=src

# 특정 테스트 파일
pytest tests/test_project_structure.py -v
```

## 📋 프로젝트 구조

```
mcp-price-ranking/
├── src/                    # 소스 코드
│   ├── server.py           # MCP 서버 메인
│   ├── config.py           # 설정 관리
│   ├── exceptions.py       # 예외 정의
│   ├── tools/              # MCP 도구들
│   ├── api/                # API 클라이언트
│   ├── analysis/           # 분석 엔진
│   └── utils/              # 유틸리티
├── tests/                  # 테스트 코드
├── requirements.txt        # 의존성
├── .env.example           # 환경 변수 템플릿
└── README.md              # 프로젝트 문서
```

## 🔧 개발 상태

현재 TDD 방법론을 적용하여 단계별로 개발 중입니다.

### Phase 1: 기반 구조 구축 (진행 중)
- [x] 프로젝트 구조 설정
- [x] 기본 설정 파일 구성
- [ ] MCP 서버 기본 구현
- [ ] API 클라이언트 구현
- [ ] 첫 번째 도구 구현

### Phase 2: 핵심 기능 개발 (예정)
- [ ] 7개 주요 도구 구현
- [ ] 가격 분석 엔진
- [ ] 패턴 감지기
- [ ] 알림 시스템

## 📊 제공 도구

1. **get_price_change_ranking**: 가격 변동률 순위
2. **get_52week_high_low**: 52주 신고가/신저가
3. **get_limit_stocks**: 상한가/하한가 종목
4. **get_consecutive_moves**: 연속 상승/하락
5. **get_gap_stocks**: 갭 상승/하락
6. **get_volatility_ranking**: 변동성 순위
7. **get_price_alerts**: 실시간 알림

## 🤝 기여하기

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 라이선스

MIT License

## 📞 지원

이슈가 있으시면 GitHub Issues를 통해 문의해주세요.