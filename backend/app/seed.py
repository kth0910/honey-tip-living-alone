from sqlalchemy.orm import Session

from app.models import Document, Source


SOURCE_SEEDS = [
    {
        "name": "소비자24 비교공감",
        "url": "https://www.consumer.go.kr/user/ftc/consumer/cnsmrBBS/79/selectInfoRptList.do",
        "source_type": "comparison",
        "crawl_interval": "daily",
    },
    {
        "name": "소비자24 리콜정보",
        "url": "https://www.consumer.go.kr/user/ftc/consumer/recallInfo/60/selectRecallInfoInternalList.do",
        "source_type": "recall",
        "crawl_interval": "daily",
    },
    {
        "name": "한국소비자원",
        "url": "https://www.kca.go.kr/home/main.do",
        "source_type": "press",
        "crawl_interval": "daily",
    },
    {
        "name": "공정거래위원회",
        "url": "https://www.ftc.go.kr/www/selectReportUserList.do?key=10",
        "source_type": "press",
        "crawl_interval": "daily",
    },
]

DOCUMENT_SEEDS = [
    ("소비자24 비교공감", "전동승용완구 제품 비교정보", "전동승용완구 안전성, 사용성, 배터리, 가격 정보를 비교한 자료입니다.", "비교정보", "유아용품", "전동승용완구,유아용품,안전성,가격", "2026-04-28"),
    ("한국소비자원", "노트북 품질비교 결과", "휴대성, 구동속도, 디스플레이, 배터리 등 주요 성능을 제품별로 비교한 시험 결과입니다.", "비교정보", "생활가전", "노트북,품질비교,배터리,디스플레이", "2025-12-04"),
    ("소비자24 리콜정보", "요구르트 제품 회수 조치", "일부 식품 제품의 회수 조치 여부와 대상 제조일자를 확인해야 하는 리콜 정보입니다.", "리콜", "식품", "요구르트,식품,회수,리콜", "2026-04-27"),
    ("소비자24 리콜정보", "새치커버 제품 안전성 관련 회수 정보", "화장품 안전 기준과 관련된 회수 여부를 확인할 수 있는 리콜 항목입니다.", "리콜", "화장품", "새치커버,화장품,안전,회수", "2026-04-30"),
    ("한국소비자원", "전기매트 사용 시 안전주의", "과열, 보관, 사용 시간 등 전기매트 이용 시 확인해야 할 안전주의 정보입니다.", "안전주의", "생활가전", "전기매트,온열제품,안전주의,화재", "2026-01-20"),
    ("공정거래위원회", "구독서비스 소비자 피해 예방 안내", "정기결제, 해지, 환불 조건 등 구독서비스 이용 전 확인해야 할 소비자 유의사항입니다.", "보도자료", "정책", "구독서비스,정기결제,환불,정책", "2026-03-11"),
]


def seed_database(db: Session) -> None:
    sources_by_name: dict[str, Source] = {}
    for payload in SOURCE_SEEDS:
        source = db.query(Source).filter(Source.name == payload["name"]).one_or_none()
        if not source:
            source = Source(**payload)
            db.add(source)
            db.flush()
        sources_by_name[source.name] = source

    for source_name, title, summary, doc_type, category, tags, published_at in DOCUMENT_SEEDS:
        source = sources_by_name[source_name]
        url = f"{source.url}#seed-{published_at}-{title}"
        exists = db.query(Document).filter(Document.url == url).one_or_none()
        if exists:
            continue
        db.add(
            Document(
                source_id=source.id,
                title=title,
                summary=summary,
                url=url,
                doc_type=doc_type,
                category=category,
                tags=tags,
                published_at=published_at,
            )
        )

    db.commit()
