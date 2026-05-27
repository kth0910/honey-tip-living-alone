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
kca_smart = Source(
    name="한국소비자원 시험검사",
    url="https://www.kca.go.kr/smartconsumer/sub.do?menukey=7301&mode=list&cate=00000055",
    source_type="comparison",
)
ftc = Source(name="공정거래위원회", url="https://www.ftc.go.kr/www/selectReportUserList.do?key=10", source_type="press")

assert_parser(
    consumer24,
    """
    <table class="tbl col data">
      <caption>비교공감 게시판 - 이미지, 제목/요약, 제공기관, 게시일, 조회수</caption>
      <tbody>
        <tr>
          <td class="img">
            <a href="javascript:selectViewList('A1081327','view','1','');" title="[비교공감 제2026-7호] 전동승용완구"></a>
          </td>
          <td class="title">
            <div class="titleConts">
              <a href="javascript:selectViewList('A1081327','view','1','');">
                <span>[비교공감 제2026-7호] 전동승용완구</span>
                <span class="desc ellipsisMulti">제품별 주행시간과 안전성을 비교한 자료입니다.</span>
              </a>
            </div>
          </td>
          <td>한국소비자원</td>
          <td>2026.05.21</td>
          <td>816</td>
        </tr>
      </tbody>
    </table>
    """,
    "[비교공감 제2026-7호] 전동승용완구",
)
docs = parse_board(
    """
    <table class="tbl col data"><tbody><tr>
      <td></td>
      <td class="title"><a href="javascript:selectViewList('A1081327','view','1','');">
        <span>[비교공감 제2026-7호] 전동승용완구</span>
      </a></td>
      <td>한국소비자원</td><td>2026-05-21</td><td>816</td>
    </tr></tbody></table>
    """,
    consumer24.url,
    consumer24,
)
assert docs[0].url.endswith("/selectInfoRptDetail.do?infoId=A1081327")

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
assert not parse_board(
    """
    <div>
      <a href="/home/main.do?page=2">오늘 하루열지않기</a>
      <a href="/odr/pg/pi/pgpi001">나의사건처리</a>
      <a href="/home/sub.do?menukey=4001">판매유형별피해구제건수</a>
    </div>
    """,
    kca.url,
    kca,
)
assert_parser(
    kca_smart,
    """
    <table class="board m_board">
      <tbody>
        <tr>
          <td class="brd_none b_num">510</td>
          <td class="b_title2">시험검사</td>
          <td class="title">
            <a href="?menukey=7301&amp;mode=view&amp;no=1004459116&amp;cate=00000055" class="title">전동 승용완구 품질비교시험 결과보고서</a>
          </td>
          <td class="b_write">조수민</td>
          <td class="b_date">2026-05-21</td>
          <td>99</td>
        </tr>
      </tbody>
    </table>
    """,
    "전동 승용완구 품질비교시험 결과보고서",
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
kca_smart_page_6 = page_url_candidates(kca_smart, 6)
ftc_page_5 = page_url_candidates(ftc, 5)

assert consumer24.url in page_url_candidates(consumer24, 1)
assert any("page=3" in url and "row=10" in url for url in consumer24_page_3)
assert any("page=4" in url for url in kca_page_4)
assert any("page=6" in url and "cate=00000055" in url for url in kca_smart_page_6)
assert any("pageIndex=5" in url for url in ftc_page_5)

print("parser tests ok")
