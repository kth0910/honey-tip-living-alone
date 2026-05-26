import {
  Archive,
  BadgeCheck,
  CalendarClock,
  Database,
  ExternalLink,
  FileSearch,
  Filter,
  RotateCw,
  Search,
  ShieldAlert,
} from "lucide-react";
import React from "react";
import heroImage from "../assets/hero-consumer-guide.png";
import { fetchDocuments, fetchSources, triggerSeed } from "./api.js";

const filters = ["전체", "비교정보", "리콜", "보도자료", "안전주의"];

function sourceIcon(sourceType) {
  if (sourceType === "recall") return ShieldAlert;
  if (sourceType === "press") return BadgeCheck;
  return FileSearch;
}

function App() {
  const [query, setQuery] = React.useState("");
  const [activeFilter, setActiveFilter] = React.useState("전체");
  const [documents, setDocuments] = React.useState([]);
  const [sources, setSources] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(true);
  const [error, setError] = React.useState("");

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
        const data = await fetchDocuments({ query, type: activeFilter });
        if (!ignore) setDocuments(data);
      } catch {
        if (!ignore) {
          setDocuments([]);
          setError("백엔드 API에 연결할 수 없습니다. FastAPI 서버가 실행 중인지 확인하세요.");
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
  }, [query, activeFilter]);

  async function handleSeed() {
    setIsLoading(true);
    setError("");
    try {
      await triggerSeed();
      const [nextSources, nextDocuments] = await Promise.all([
        fetchSources(),
        fetchDocuments({ query, type: activeFilter }),
      ]);
      setSources(nextSources);
      setDocuments(nextDocuments);
    } catch {
      setError("샘플 데이터 입력에 실패했습니다. 백엔드 서버 상태를 확인하세요.");
    } finally {
      setIsLoading(false);
    }
  }

  const latestCollectedAt = documents.map((item) => item.collectedAt).sort().at(-1) ?? "-";

  return (
    <>
      <header className="topbar">
        <a className="brand" href="#top" aria-label="혼자살림 레이더 홈">
          <span className="brand-mark">ㅎ</span>
          <span>
            <strong>혼자살림 레이더</strong>
            <small>공공 소비자정보 아카이브</small>
          </span>
        </a>
        <nav className="nav-links" aria-label="주요 메뉴">
          <a href="#search">검색</a>
          <a href="#sources">수집원</a>
          <a href="#pipeline">구조</a>
        </nav>
      </header>

      <main id="top">
        <section className="hero archive-hero" aria-labelledby="hero-title">
          <div className="hero-copy">
            <p className="eyebrow">공식 자료를 긁어와 저장하는 생활정보 검색엔진</p>
            <h1 id="hero-title">가성비템·리콜·안전정보를 수집해서 한곳에서 검색합니다.</h1>
            <p className="hero-text">
              소비자24, 공정거래위원회, 한국소비자원에 흩어진 비교정보와 리콜 공지를 백엔드가 수집하고
              데이터베이스에 저장합니다. 사용자는 제품명, 카테고리, 이슈로 저장된 문서를 다시 검색합니다.
            </p>
            <div className="hero-stats" aria-label="아카이브 상태">
              <strong>{documents.length}</strong>
              <span>현재 검색 결과</span>
              <strong>{sources.length}</strong>
              <span>등록된 수집원</span>
              <strong>{latestCollectedAt}</strong>
              <span>최근 수집일</span>
            </div>
          </div>

          <section className="archive-panel" id="search" aria-label="아카이브 검색">
            <div className="panel-header">
              <p className="eyebrow">실서비스 검색</p>
              <h2>DB에 저장된 자료에서 찾기</h2>
              <p>이 화면은 FastAPI의 `/api/documents`와 `/api/sources`를 호출합니다.</p>
            </div>
            <label htmlFor="keyword">제품명, 카테고리, 이슈</label>
            <div className="search-row">
              <input
                id="keyword"
                name="keyword"
                type="search"
                value={query}
                placeholder="예: 노트북, 전기매트, 요구르트, 리콜"
                autoComplete="off"
                onChange={(event) => setQuery(event.target.value)}
              />
              <button type="button" aria-label="검색">
                <Search size={18} aria-hidden="true" />
                검색
              </button>
            </div>
            <div className="filter-row" aria-label="자료 유형 필터">
              {filters.map((filter) => (
                <button
                  type="button"
                  className={filter === activeFilter ? "active" : ""}
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                >
                  {filter}
                </button>
              ))}
            </div>
            <button className="seed-button" type="button" onClick={handleSeed}>
              <Database size={18} aria-hidden="true" />
              로컬 샘플 데이터 넣기
            </button>
            <figure className="finder-visual">
              <img src={heroImage} alt="노트북과 휴대폰으로 생활제품 정보를 확인하는 사람 일러스트" />
            </figure>
          </section>
        </section>

        <section className="results-section" aria-labelledby="results-title">
          <div className="section-intro">
            <p className="eyebrow">검색 결과</p>
            <h2 id="results-title">DB에 저장된 문서</h2>
            <p>{isLoading ? "불러오는 중입니다." : `${documents.length}개의 문서가 조건과 일치합니다.`}</p>
            {error && <p className="error-text">{error}</p>}
          </div>
          <div className="result-list">
            {documents.map((item) => (
              <article className="result-card" key={item.id}>
                <div className="result-meta">
                  <span>{item.type}</span>
                  <span>{item.source}</span>
                  <span>{item.publishedAt || "게시일 미확인"}</span>
                </div>
                <h3>{item.title}</h3>
                <p>{item.summary}</p>
                <div className="tag-row">
                  {item.tags.map((tag) => (
                    <span key={tag}>{tag}</span>
                  ))}
                </div>
                <div className="result-footer">
                  <span>수집일 {item.collectedAt}</span>
                  <a href={item.url} target="_blank" rel="noreferrer">
                    원문 확인
                    <ExternalLink size={15} aria-hidden="true" />
                  </a>
                </div>
              </article>
            ))}
            {!isLoading && documents.length === 0 && !error && (
              <article className="empty-card">
                <h3>검색 결과가 없습니다</h3>
                <p>다른 키워드를 입력하거나 샘플 데이터를 먼저 넣어보세요.</p>
              </article>
            )}
          </div>
        </section>

        <section className="source-hub" id="sources" aria-labelledby="sources-title">
          <div className="section-intro">
            <p className="eyebrow">수집 대상</p>
            <h2 id="sources-title">백엔드가 주기적으로 확인하는 공식 사이트</h2>
          </div>
          <div className="source-grid">
            {sources.map((source) => {
              const Icon = sourceIcon(source.sourceType);
              return (
                <article className="source-card" key={source.id}>
                  <Icon size={24} aria-hidden="true" />
                  <span className="source-tag">{source.crawlInterval}</span>
                  <h3>{source.name}</h3>
                  <p>{source.sourceType} 유형의 공식 자료를 수집하고 중복 URL은 저장하지 않습니다.</p>
                  <a href={source.url} target="_blank" rel="noreferrer">
                    수집원 보기
                    <ExternalLink size={15} aria-hidden="true" />
                  </a>
                </article>
              );
            })}
          </div>
        </section>

        <section className="pipeline" id="pipeline" aria-labelledby="pipeline-title">
          <div className="section-intro">
            <p className="eyebrow">서비스 구조</p>
            <h2 id="pipeline-title">크롤링부터 검색까지 실제 흐름</h2>
          </div>
          <div className="pipeline-list">
            <article>
              <RotateCw size={24} aria-hidden="true" />
              <h3>수집</h3>
              <p>GitHub Actions 또는 관리자 API가 FastAPI 크롤러를 호출합니다.</p>
            </article>
            <article>
              <Archive size={24} aria-hidden="true" />
              <h3>정규화</h3>
              <p>제목, 기관, 게시일, 유형, 태그, 원문 URL을 같은 스키마로 맞춥니다.</p>
            </article>
            <article>
              <Database size={24} aria-hidden="true" />
              <h3>저장</h3>
              <p>Neon Postgres 또는 로컬 SQLite에 문서와 수집 이력을 저장합니다.</p>
            </article>
            <article>
              <Filter size={24} aria-hidden="true" />
              <h3>검색</h3>
              <p>React 프론트엔드가 FastAPI 검색 API를 호출해 결과를 보여줍니다.</p>
            </article>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>
          이 서비스는 원문을 대체하지 않고 공식 자료를 찾기 쉽게 색인합니다. 운영 시 robots.txt, 이용 조건,
          요청 주기 제한과 원문 출처 표기를 반드시 지켜야 합니다.
        </p>
        <div>
          <span>
            <CalendarClock size={15} aria-hidden="true" />
            FastAPI + React + Postgres
          </span>
        </div>
      </footer>
    </>
  );
}

export default App;
