# 운영자가 신경써야 할 점

최종 갱신: 2026-05-26

## 배포 구성

- GitHub 저장소: `https://github.com/kth0910/honey-tip-living-alone`
- 프론트엔드: Vercel
- 백엔드: Render Web Service
- 운영 DB: Neon Postgres
- 스케줄러: GitHub Actions

## 생성된 Neon 정보

- Neon project id: `spring-pond-01868315`
- branch: `main`
- branch id: `br-proud-truth-apht1kjn`
- database: `neondb`
- role: `neondb_owner`

Neon connection string은 비밀값이다. GitHub, 문서, README, 채팅 기록에 그대로 남기지 말고 Render 환경 변수 `DATABASE_URL`에만 넣는다.

## Render 환경 변수

Render 서비스 `honja-sallim-radar-api`에 필요한 값:

| 이름 | 값 | 비고 |
| --- | --- | --- |
| `APP_ENV` | `production` | 운영 모드 |
| `DATABASE_URL` | Neon connection string | 비밀값, Dashboard에서 직접 입력 |
| `CRAWL_ADMIN_TOKEN` | 긴 랜덤 문자열 | GitHub Actions secret과 같은 값 |
| `ALLOWED_ORIGINS` | Vercel 운영 URL | 예: `https://honey-tip-living-alone.vercel.app` |
| `ALLOWED_ORIGIN_REGEX` | `https://.*\.vercel\.app` | Vercel preview/production 허용 |

`CRAWL_ADMIN_TOKEN`은 Render에서 자동 생성하면 GitHub Actions가 같은 값을 알 수 없다. 운영에서는 직접 만든 랜덤 값을 Render env와 GitHub secret에 같은 값으로 넣는 편이 낫다.

## Vercel 환경 변수

프론트엔드는 기본 운영 API 주소로 `https://honja-sallim-radar-api.onrender.com`을 사용한다.

Render URL이 달라졌다면 Vercel에 아래 값을 등록한다.

| 이름 | 값 |
| --- | --- |
| `VITE_API_BASE_URL` | 실제 Render API URL |

Vite는 빌드 시점에 `VITE_` 환경 변수를 주입하므로, 값을 바꾸면 Vercel에서 재배포해야 한다.

## GitHub Actions Secrets

`.github/workflows/crawl.yml`은 하루 1회 Render 백엔드의 `/api/admin/crawl`을 호출한다.

Repository Settings > Secrets and variables > Actions에 아래 값을 넣는다.

| 이름 | 값 |
| --- | --- |
| `API_BASE_URL` | Render API URL |
| `CRAWL_ADMIN_TOKEN` | Render의 `CRAWL_ADMIN_TOKEN`과 같은 값 |

## 배포 후 확인

1. Render에서 `/health` 확인
   - `https://honja-sallim-radar-api.onrender.com/health`
2. Render 관리자 seed 실행
   - `POST /api/admin/seed`
   - 운영에서는 `x-crawl-token` 헤더 필요
3. 문서 API 확인
   - `GET /api/documents`
4. Vercel 프론트에서 검색 결과 확인
5. GitHub Actions `Crawl consumer archive`를 `workflow_dispatch`로 수동 실행해 성공 여부 확인

## 크롤링 운영 주의

- 운영 전 `docs/source-compliance.md`의 robots.txt와 이용 조건을 다시 확인한다.
- 하루 1회 이하로 시작하고 실패율, 응답 시간, 차단 여부를 본다.
- 공식 원문 전체를 복제하지 않고 제목, 요약, 태그, 발행일, 원문 URL, 수집 시각 위주로 저장한다.
- 사이트 구조가 바뀌면 문서 수집량이 갑자기 0이 될 수 있으므로 `crawl_runs`와 Render 로그를 주기적으로 확인한다.

## 비용과 장애 포인트

- Render Free 서비스는 cold start가 있을 수 있다.
- Neon Free compute도 idle 이후 첫 요청이 느릴 수 있다.
- Vercel 프론트는 백엔드 URL이 틀리면 검색 결과가 비어 보인다.
- CORS 오류가 나면 Render의 `ALLOWED_ORIGINS`, `ALLOWED_ORIGIN_REGEX`를 먼저 확인한다.
- GitHub Actions가 401이면 `CRAWL_ADMIN_TOKEN` 불일치가 가장 흔한 원인이다.

## 절대 커밋하면 안 되는 값

- Neon connection string
- Render `CRAWL_ADMIN_TOKEN`
- GitHub Actions secrets
- Vercel/Render/Neon API key
