# Cloud Architecture

## 목표

공식 소비자정보 사이트를 주기적으로 수집하고, 저장된 문서를 사용자가 검색할 수 있게 제공한다.

## 무료 우선 구성

```text
User
  |
  v
Vercel Hobby
  React frontend
  |
  v
Render Free Web Service
  FastAPI backend
  /api/documents
  /api/sources
  /api/admin/crawl
  |
  v
Neon Free
  Postgres database
  documents
  sources
  crawl_runs

GitHub Actions schedule
  |
  v
POST /api/admin/crawl
```

## 서비스별 역할

- **Vercel Hobby**: React 프론트엔드 호스팅
- **Render Free Web Service**: FastAPI API 서버 호스팅
- **Neon Free**: Postgres 데이터베이스
- **GitHub Actions**: 무료 스케줄러 역할로 크롤러 트리거

## Neon을 쓰는 이유

DB는 Neon Postgres를 기본 추천으로 둔다.

Neon은 Postgres 호환 연결 문자열을 제공하므로 현재 FastAPI 백엔드의 `DATABASE_URL`에 그대로 연결할 수 있다.

예시:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
```

## 운영 흐름

1. GitHub Actions가 하루 1회 `/api/admin/crawl`을 호출한다.
2. FastAPI 백엔드가 등록된 공식 사이트를 수집한다.
3. 크롤러가 문서 제목, 원문 URL, 기관, 유형, 태그, 게시일을 정규화한다.
4. 중복 URL은 저장하지 않는다.
5. 사용자는 프론트엔드에서 `/api/documents`를 통해 저장된 문서를 검색한다.

## 주의사항

- 공식 사이트별 robots.txt와 이용 조건을 확인해야 한다.
- 크롤링 주기는 낮게 시작한다.
- 원문 URL과 수집일을 반드시 표시한다.
- 검색 결과는 원문을 대체하지 않고, 원문으로 이동할 수 있어야 한다.
