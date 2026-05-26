import {
  AlertCircle,
  ArrowDownAZ,
  ArrowUpAZ,
  CalendarClock,
  Database,
  ExternalLink,
  FileSearch,
  Filter,
  RefreshCw,
  Search,
} from "lucide-react";
import React from "react";
import { fetchDocuments, fetchSources, triggerSeed } from "./api.js";

const docTypes = ["전체", "비교정보", "리콜", "보도자료", "안전주의"];
const dateRanges = [
  { label: "전체 기간", value: "all" },
  { label: "최근 30일", value: "30" },
  { label: "최근 1년", value: "365" },
];
const sortOptions = [
  { label: "수집일 최신순", value: "collected_desc", icon: ArrowDownAZ },
  { label: "발행일 최신순", value: "published_desc", icon: CalendarClock },
  { label: "제목순", value: "title_asc", icon: ArrowUpAZ },
];
const isLocalMode = import.meta.env.DEV || import.meta.env.MODE === "local";

function parseDate(value) {
  if (!value) return null;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? null : date;
}

function isWithinRange(item, range) {
  if (range === "all") return true;
  const reference = parseDate(item.publishedAt) ?? parseDate(item.collectedAt);
  if (!reference) return false;
  const days = Number(range);
  const cutoff = new Date();
  cutoff.setDate(cutoff.getDate() - days);
  return reference >= cutoff;
}

function sortDocuments(items, sortBy) {
  const next = [...items];
  if (sortBy === "title_asc") {
    return next.sort((a, b) => a.title.localeCompare(b.title, "ko"));
  }
  if (sortBy === "published_desc") {
    return next.sort((a, b) => {
      const left = parseDate(a.publishedAt)?.getTime() ?? 0;
      const right = parseDate(b.publishedAt)?.getTime() ?? 0;
      return right - left;
    });
  }
  return next.sort((a, b) => {
    const left = parseDate(a.collectedAt)?.getTime() ?? 0;
    const right = parseDate(b.collectedAt)?.getTime() ?? 0;
    return right - left;
  });
}

function SkeletonList() {
  return (
    <div className="result-list" aria-label="검색 결과 불러오는 중">
      {[0, 1, 2].map((item) => (
        <article className="result-card skeleton-card" key={item}>
          <span />
          <strong />
          <p />
          <p />
        </article>
      ))}
    </div>
  );
}

function App() {
  const [query, setQuery] = React.useState("");
  const [activeType, setActiveType] = React.useState("전체");
  const [activeSource, setActiveSource] = React.useState("");
  const [dateRange, setDateRange] = React.useState("all");
  const [sortBy, setSortBy] = React.useState("collected_desc");
  const [documents, setDocuments] = React.useState([]);
  const [sources, setSources] = React.useState([]);
  const [selectedId, setSelectedId] = React.useState(null);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState("");
  const [refreshKey, setRefreshKey] = React.useState(0);

  React.useEffect(() => {
    let ignore = false;

    async function loadSources() {
      try {
        const data = await fetchSources();
        if (!ignore) setSources(data);
      } catch {
        if (!ignore) setSources([]);
      }
    }

    loadSources();
    return () => {
      ignore = true;
    };
  }, []);

  React.useEffect(() => {
    let ignore = false;

    async function loadDocuments() {
      setIsLoading(true);
      setError("");
      try {
        const data = await fetchDocuments({
          query,
          type: activeType,
          sourceId: activeSource,
          limit: 100,
        });
        if (!ignore) setDocuments(data);
      } catch {
        if (!ignore) {
          setDocuments([]);
          setError("백엔드 API에 연결할 수 없습니다. 서버 상태를 확인한 뒤 다시 시도하세요.");
        }
      } finally {
        if (!ignore) setIsLoading(false);
      }
    }

    const timer = window.setTimeout(loadDocuments, 180);
    return () => {
      ignore = true;
      window.clearTimeout(timer);
    };
  }, [query, activeType, activeSource, refreshKey]);

  const visibleDocuments = React.useMemo(() => {
    return sortDocuments(
      documents.filter((item) => isWithinRange(item, dateRange)),
      sortBy,
    );
  }, [documents, dateRange, sortBy]);

  React.useEffect(() => {
    if (visibleDocuments.length === 0) {
      setSelectedId(null);
      return;
    }
    if (!visibleDocuments.some((item) => item.id === selectedId)) {
      setSelectedId(visibleDocuments[0].id);
    }
  }, [selectedId, visibleDocuments]);

  async function handleSeed() {
    setIsLoading(true);
    setError("");
    try {
      await triggerSeed();
      setRefreshKey((value) => value + 1);
    } catch {
      setError("샘플 데이터 입력에 실패했습니다. 백엔드 서버 상태를 확인하세요.");
      setIsLoading(false);
    }
  }

  const selectedDocument = visibleDocuments.find((item) => item.id === selectedId) ?? null;
  const latestCollectedAt = documents.map((item) => item.collectedAt).sort().at(-1) ?? "-";
  const activeSort = sortOptions.find((option) => option.value === sortBy) ?? sortOptions[0];
  const SortIcon = activeSort.icon;

  return (
    <>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="혼자살림 레이더 홈">
          <span className="brand-mark">ㅎ</span>
          <span>
            <strong>혼자살림 레이더</strong>
            <small>공식 소비자정보 검색</small>
          </span>
        </a>
        <nav className="nav-links" aria-label="주요 메뉴">
          <a href="#search">검색</a>
          <a href="#sources">수집원</a>
          <a href="#pipeline">구조</a>
        </nav>
      </header>

      <main id="top">
        <section className="search-workspace" id="search" aria-labelledby="search-title">
          <div className="workspace-heading">
            <p className="eyebrow">공공기관 비교정보 아카이브</p>
            <h1 id="search-title">저장된 공식 자료 검색</h1>
            <p>
              소비자24, 한국소비자원, 공정거래위원회에서 수집한 문서의 제목, 요약, 태그, 출처를 기준으로
              검색합니다.
            </p>
          </div>

          <section className="search-panel" aria-label="검색 조건">
            <label htmlFor="keyword">검색어</label>
            <div className="search-row">
              <input
                id="keyword"
                name="keyword"
                type="search"
                value={query}
                placeholder="제품명, 품목, 이슈를 입력하세요"
                autoComplete="off"
                onChange={(event) => setQuery(event.target.value)}
              />
              <button type="button" onClick={() => setRefreshKey((value) => value + 1)}>
                <Search size={18} aria-hidden="true" />
                검색
              </button>
            </div>

            <div className="control-grid">
              <label>
                자료 유형
                <select value={activeType} onChange={(event) => setActiveType(event.target.value)}>
                  {docTypes.map((type) => (
                    <option value={type} key={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                출처
                <select value={activeSource} onChange={(event) => setActiveSource(event.target.value)}>
                  <option value="">전체 출처</option>
                  {sources.map((source) => (
                    <option value={source.id} key={source.id}>
                      {source.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                기간
                <select value={dateRange} onChange={(event) => setDateRange(event.target.value)}>
                  {dateRanges.map((range) => (
                    <option value={range.value} key={range.value}>
                      {range.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                정렬
                <select value={sortBy} onChange={(event) => setSortBy(event.target.value)}>
                  {sortOptions.map((option) => (
                    <option value={option.value} key={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>

            <div className="status-strip" aria-label="검색 상태">
              <span>
                <Database size={16} aria-hidden="true" />
                {documents.length}개 로드
              </span>
              <span>
                <Filter size={16} aria-hidden="true" />
                {visibleDocuments.length}개 표시
              </span>
              <span>
                <CalendarClock size={16} aria-hidden="true" />
                최근 수집 {latestCollectedAt}
              </span>
              <span>
                <SortIcon size={16} aria-hidden="true" />
                {activeSort.label}
              </span>
            </div>

            {isLocalMode && (
              <button className="seed-button" type="button" onClick={handleSeed}>
                <Database size={18} aria-hidden="true" />
                개발용 샘플 데이터 입력
              </button>
            )}
          </section>
        </section>

        <section className="results-workspace" aria-labelledby="results-title">
          <div className="section-toolbar">
            <div>
              <p className="eyebrow">검색 결과</p>
              <h2 id="results-title">문서 목록</h2>
            </div>
            <button className="ghost-button" type="button" onClick={() => setRefreshKey((value) => value + 1)}>
              <RefreshCw size={17} aria-hidden="true" />
              다시 불러오기
            </button>
          </div>

          {error && (
            <div className="error-box" role="alert">
              <AlertCircle size={19} aria-hidden="true" />
              <p>{error}</p>
              <button type="button" onClick={() => setRefreshKey((value) => value + 1)}>
                재시도
              </button>
            </div>
          )}

          <div className="document-grid">
            {isLoading ? (
              <SkeletonList />
            ) : (
              <div className="result-list">
                {visibleDocuments.map((item) => (
                  <article
                    className={`result-card ${item.id === selectedId ? "selected" : ""}`}
                    key={item.id}
                  >
                    <button type="button" onClick={() => setSelectedId(item.id)}>
                      <span className="result-meta">
                        <span>{item.type}</span>
                        <span>{item.source}</span>
                        <span>{item.publishedAt || "게시일 미확인"}</span>
                      </span>
                      <strong>{item.title}</strong>
                      <span className="summary">{item.summary}</span>
                    </button>
                  </article>
                ))}
                {visibleDocuments.length === 0 && !error && (
                  <article className="empty-card">
                    <FileSearch size={28} aria-hidden="true" />
                    <h3>조건에 맞는 문서가 없습니다</h3>
                    <p>검색어를 줄이거나 출처, 기간, 자료 유형 필터를 넓혀보세요.</p>
                  </article>
                )}
              </div>
            )}

            <aside className="detail-panel" aria-label="문서 상세">
              {selectedDocument ? (
                <>
                  <div className="detail-header">
                    <span>{selectedDocument.type}</span>
                    <h2>{selectedDocument.title}</h2>
                    <p>{selectedDocument.summary}</p>
                  </div>
                  <dl className="detail-meta">
                    <div>
                      <dt>출처</dt>
                      <dd>{selectedDocument.source}</dd>
                    </div>
                    <div>
                      <dt>발행일</dt>
                      <dd>{selectedDocument.publishedAt || "확인 필요"}</dd>
                    </div>
                    <div>
                      <dt>수집일</dt>
                      <dd>{selectedDocument.collectedAt}</dd>
                    </div>
                    <div>
                      <dt>원문 URL</dt>
                      <dd>{selectedDocument.url}</dd>
                    </div>
                  </dl>
                  <div className="tag-row">
                    {selectedDocument.tags.map((tag) => (
                      <span key={tag}>{tag}</span>
                    ))}
                  </div>
                  <a className="primary-link" href={selectedDocument.url} target="_blank" rel="noreferrer">
                    원문 열기
                    <ExternalLink size={16} aria-hidden="true" />
                  </a>
                </>
              ) : (
                <div className="detail-empty">
                  <FileSearch size={30} aria-hidden="true" />
                  <h2>문서를 선택하세요</h2>
                  <p>검색 결과를 선택하면 출처, 발행일, 수집일, 태그를 여기에서 확인할 수 있습니다.</p>
                </div>
              )}
            </aside>
          </div>
        </section>

        <section className="source-hub" id="sources" aria-labelledby="sources-title">
          <div className="section-intro">
            <p className="eyebrow">수집 대상</p>
            <h2 id="sources-title">공식 사이트</h2>
          </div>
          <div className="source-grid">
            {sources.map((source) => (
              <article className="source-card" key={source.id}>
                <span className="source-tag">{source.crawlInterval}</span>
                <h3>{source.name}</h3>
                <p>{source.sourceType} 유형의 공식 자료를 보수적으로 수집하고 중복 URL은 저장하지 않습니다.</p>
                <a href={source.url} target="_blank" rel="noreferrer">
                  수집원 보기
                  <ExternalLink size={15} aria-hidden="true" />
                </a>
              </article>
            ))}
          </div>
        </section>

        <section className="pipeline" id="pipeline" aria-labelledby="pipeline-title">
          <div className="section-intro">
            <p className="eyebrow">서비스 구조</p>
            <h2 id="pipeline-title">수집부터 검색까지</h2>
          </div>
          <div className="pipeline-list">
            <article>
              <RefreshCw size={22} aria-hidden="true" />
              <h3>수집</h3>
              <p>GitHub Actions 또는 관리자 API가 FastAPI 크롤러를 호출합니다.</p>
            </article>
            <article>
              <FileSearch size={22} aria-hidden="true" />
              <h3>정규화</h3>
              <p>제목, 기관, 게시일, 유형, 태그, 원문 URL을 같은 스키마로 맞춥니다.</p>
            </article>
            <article>
              <Database size={22} aria-hidden="true" />
              <h3>저장</h3>
              <p>Neon Postgres 또는 로컬 SQLite에 문서와 수집 이력을 저장합니다.</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>
          검색 결과는 공식 원문을 대체하지 않습니다. 운영 시 robots.txt, 이용 조건, 요청 주기 제한과 출처
          표기를 지켜야 합니다.
        </p>
      </footer>
    </>
  );
}

export default App;
