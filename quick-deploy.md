# Quick Deploy

이 서비스는 프론트엔드와 백엔드를 따로 배포합니다.

## 추천 무료 우선 구성

- Frontend: Vercel Hobby
- Backend: Render Free Web Service
- Database: Neon Free Postgres
- Scheduler: GitHub Actions

## 1. Neon Postgres

1. Neon에서 Free 프로젝트를 생성합니다.
2. Connection string을 복사합니다.
3. Render 환경 변수 `DATABASE_URL`에 넣습니다.

예시:

```text
DATABASE_URL=postgresql://USER:PASSWORD@HOST/neondb?sslmode=require
```

## 2. Render FastAPI

1. Render에서 Web Service 또는 Blueprint를 생성합니다.
2. 이 저장소를 연결합니다.
3. `render.yaml`을 사용하거나 Docker Web Service로 배포합니다.
4. 환경 변수를 설정합니다.

```text
APP_ENV=production
DATABASE_URL=Neon connection string
CRAWL_ADMIN_TOKEN=random-secret
ALLOWED_ORIGINS=https://your-frontend.vercel.app
```

배포 후 확인:

```text
https://your-render-api.onrender.com/health
```

## 3. Vercel Frontend

1. Vercel에서 이 저장소를 Import합니다.
2. Framework Preset은 `Vite`를 선택합니다.
3. Build Command는 `npm run build`입니다.
4. Output Directory는 `dist`입니다.
5. 환경 변수를 설정합니다.

```text
VITE_API_BASE_URL=https://your-render-api.onrender.com
```

## 4. GitHub Actions Scheduler

Repository Secrets에 아래 값을 넣습니다.

```text
API_BASE_URL=https://your-render-api.onrender.com
CRAWL_ADMIN_TOKEN=same-secret-as-render
```

`.github/workflows/crawl.yml`이 하루 1회 크롤러를 호출합니다.

운영 DB를 처음 채울 때는 자동 스케줄과 별도로 백필을 한 번만 수동 실행합니다.

```powershell
Invoke-WebRequest `
  -Method POST `
  -Headers @{ "x-crawl-token" = "same-secret-as-render" } `
  "https://your-render-api.onrender.com/api/admin/crawl?backfill=true&max_pages=5"
```

## 배포 전 체크

- `npm run build` 성공
- `backend\.venv\Scripts\python.exe -X utf8 backend\smoke_test.py` 성공
- `backend\.venv\Scripts\python.exe -X utf8 backend\parser_test.py` 성공
- FastAPI `/health` 응답
- Render에 `DATABASE_URL` 설정
- Vercel에 `VITE_API_BASE_URL` 설정
- GitHub Secrets에 크롤 토큰 설정
- 공식 사이트 robots.txt와 이용 조건 확인
- `docs/source-compliance.md`의 출처별 점검 기록 확인
