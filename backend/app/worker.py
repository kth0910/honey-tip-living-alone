import argparse
import asyncio

from app.crawler import crawl_all_sources
from app.database import SessionLocal, init_db
from app.seed import seed_database


async def run_crawl(seed_first: bool = False, backfill: bool = False, max_pages: int = 1) -> None:
    init_db()
    db = SessionLocal()
    try:
        if seed_first:
            seed_database(db)
        inserted = await crawl_all_sources(db, backfill=backfill, max_pages=max_pages)
        print(f"crawl complete inserted={inserted} backfill={backfill} max_pages={max_pages}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["crawl"])
    parser.add_argument("--seed", action="store_true")
    parser.add_argument("--backfill", action="store_true")
    parser.add_argument("--max-pages", type=int, default=1)
    args = parser.parse_args()

    if args.command == "crawl":
        asyncio.run(run_crawl(seed_first=args.seed, backfill=args.backfill, max_pages=args.max_pages))


if __name__ == "__main__":
    main()
