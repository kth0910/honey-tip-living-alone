import argparse
import asyncio

from app.crawler import crawl_all_sources
from app.database import SessionLocal, init_db
from app.seed import seed_database


async def run_crawl(seed_first: bool = False) -> None:
    init_db()
    db = SessionLocal()
    try:
        if seed_first:
            seed_database(db)
        inserted = await crawl_all_sources(db)
        print(f"crawl complete inserted={inserted}")
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["crawl"])
    parser.add_argument("--seed", action="store_true")
    args = parser.parse_args()

    if args.command == "crawl":
        asyncio.run(run_crawl(seed_first=args.seed))


if __name__ == "__main__":
    main()
