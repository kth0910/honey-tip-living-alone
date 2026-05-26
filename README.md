# 혼자살림 레이더

공식 소비자정보를 수집하고 저장한 뒤, 사용자가 제품명이나 이슈로 검색할 수 있게 제공하는 웹 서비스입니다.

컨셉은 학교 공지 크롤링 서비스와 같습니다. 소비자24, 공정거래위원회, 한국소비자원에 흩어진 비교정보, 리콜, 보도자료, 안전주의 자료를 백엔드가 수집하고 DB에 저장합니다. 프론트엔드는 저장된 문서를 FastAPI 검색 API로 조회합니다.

## 구성

- Frontend: React + Vite
- Backend: FastAPI
- Local DB: SQLite
- Production DB: Neon Postgres
- Scheduler: GitHub Actions cron
- Backend hosting: Render Free Web Service
- Frontend hosting: Vercel Hobby

## 로컬 실행

### 1. 백엔드 실행

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

다른 터미널에서 샘플 데이터를 넣습니다.

```powershell
Invoke-WebRequest -Method POST http://127.0.0.1:8000/api/admin/seed
```

확인:

```powershell
Invoke-WebRequest http://127.0.0.1:8000/health
Invoke-WebRequest http://127.0.0.1:8000/api/documents
```

백엔드 smoke test:

```powershell
$env:PYTHONPATH='backend'
backend\.venv\Scripts\python.exe -X utf8 backend\smoke_test.py
backend\.venv\Scripts\python.exe -X utf8 backend\parser_test.py
```

`uv run`을 쓰려면 루트에 Python 프로젝트 설정을 별도로 추가해야 합니다. 현재 저장소의 백엔드 검증 기준 명령은 위의 `backend\.venv\Scripts\python.exe` 방식입니다.

### 2. 프론트엔드 실행

프로젝트 루트에서 실행합니다.

```powershell
npm install
npm run dev
```

기본 주소는 `http://127.0.0.1:5173`입니다.

프론트엔드는 기본적으로 `http://127.0.0.1:8000`의 FastAPI 백엔드를 호출합니다. 배포 환경에서는 `.env`에 API 주소를 넣습니다.

```text
VITE_API_BASE_URL=https://your-api.example.com
```

## 주요 기능

- 저장된 소비자정보 문서 검색
- 비교정보, 리콜, 보도자료, 안전주의 유형 필터
- 공식 수집원 목록 조회
- FastAPI 관리자 API로 크롤러 실행
- URL 중복 저장 방지
- 로컬 SQLite 실행과 Neon Postgres 배포 지원

## API

```text
GET  /health
GET  /api/sources
GET  /api/documents?query=노트북&type=비교정보
POST /api/admin/seed
POST /api/admin/crawl
```

`/api/admin/crawl`은 `x-crawl-token` 헤더가 필요합니다.
`/api/admin/seed`는 로컬 환경(`APP_ENV=local`)에서는 개발 편의를 위해 토큰 없이 동작하지만, 운영 환경에서는 `x-crawl-token` 헤더가 필요합니다.

## 크롤러 실행

관리자 API:

```powershell
Invoke-WebRequest `
  -Method POST `
  -Headers @{ "x-crawl-token" = "change-me" } `
  http://127.0.0.1:8000/api/admin/crawl
```

CLI:

```powershell
cd backend
python -m app.worker crawl --seed
```

## 클라우드 아키텍처

자세한 구조는 [docs/cloud-architecture.md](docs/cloud-architecture.md)를 확인하세요.
공식 출처별 크롤링 정책과 robots.txt 확인 대상은 [docs/source-compliance.md](docs/source-compliance.md)를 확인하세요.

요약:

- Vercel: React 프론트엔드
- Render: FastAPI 백엔드
- Neon: Postgres DB
- GitHub Actions: 주기적 크롤링 트리거

## 파일 구조

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── crawler.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── seed.py
│   │   └── worker.py
│   ├── Dockerfile
│   └── requirements.txt
├── src/
│   ├── App.jsx
│   ├── api.js
│   ├── main.jsx
│   ├── design-tokens.css
│   └── styles.css
├── docs/
│   └── cloud-architecture.md
├── render.yaml
├── package.json
└── quick-deploy.md
```

## 운영 주의사항

- 각 공식 사이트의 robots.txt와 이용 조건을 확인하세요.
- 요청 주기를 낮게 시작하세요.
- 원문 URL, 출처, 수집일을 반드시 표시하세요.
- 검색 결과는 공식 원문을 대체하지 않습니다.
- 운영 환경에서 seed API를 호출할 때는 반드시 관리자 토큰을 사용하세요.
