from app.crawler import page_url_candidates, parse_board
from app.models import Source


def assert_parser(source: Source, html: str, expected_title: str) -> None:
    docs = parse_board(html, source.url, source)
    assert docs, source.name
    assert docs[0].title == expected_title
    assert docs[0].published_at == "2026-05-21"
    assert docs[0].url.startswith("https://")


consumer24 = Source(
    name="소비자24 비교공감",
    url="https://www.consumer.go.kr/user/ftc/consumer/cnsmrBBS/79/selectInfoRptList.do",
    source_type="comparison",
)
kca = Source(name="한국소비자원", url="https://www.kca.go.kr/home/main.do", source_type="press")
ftc = Source(name="공정거래위원회", url="https://www.ftc.go.kr/www/selectReportUserList.do?key=10", source_type="press")

assert_parser(
    consumer24,
    """
    <table><tbody><tr>
      <td><a href="/user/ftc/consumer/cnsmrBBS/79/selectInfoRptView.do?infoId=1">무선청소기 품질 비교정보</a></td>
      <td>2026.05.21</td>
    </tr></tbody></table>
    """,
    "무선청소기 품질 비교정보",
)
assert_parser(
    kca,
    """
    <ul class="board-list"><li>
      <a href="/home/sub.do?menukey=4002&mode=view&no=1">전기매트 안전주의 안내</a>
      <span>2026-05-21</span>
    </li></ul>
    """,
    "전기매트 안전주의 안내",
)
assert_parser(
    ftc,
    """
    <table><tbody><tr>
      <td><a href="/www/selectReportUserView.do?key=10&rpttype=1">구독서비스 소비자 피해 예방 안내</a></td>
      <td>2026년 5월 21일</td>
    </tr></tbody></table>
    """,
    "구독서비스 소비자 피해 예방 안내",
)

consumer24_page_3 = page_url_candidates(consumer24, 3)
kca_page_4 = page_url_candidates(kca, 4)
ftc_page_5 = page_url_candidates(ftc, 5)

assert consumer24.url in page_url_candidates(consumer24, 1)
assert any("pageIndex=3" in url for url in consumer24_page_3)
assert any("page=4" in url for url in kca_page_4)
assert any("pageIndex=5" in url for url in ftc_page_5)

print("parser tests ok")
