import argparse
import asyncio
import datetime
import logging
import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.infrastructure.config import get_settings
from app.infrastructure.database import init_engine, init_session_factory
from app.infrastructure.seed_calendar_demo import seed_calendar_demo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed-calendar-demo-cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for the calendar demo appointment seeder."""
    parser = argparse.ArgumentParser(
        description="Idempotently add synthetic appointments for calendar dots demo (C-22).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Reference date within target month (YYYY-MM-DD). Defaults to clinic today.",
    )
    return parser.parse_args(argv)


async def run_seed_calendar_demo(date_str: str | None = None) -> dict[str, int]:
    """Connect to the configured database and run seed_calendar_demo."""
    base_date = datetime.date.fromisoformat(date_str) if date_str else None
    settings = get_settings()
    engine = init_engine(settings.DATABASE_URL)
    session_factory = init_session_factory(engine)

    try:
        async with session_factory() as session:
            return await seed_calendar_demo(
                session=session,
                base_date=base_date,
                timezone_str=settings.TIMEZONE,
            )
    finally:
        await engine.dispose()


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    logger.info("Ejecutando seed_calendar_demo (date=%s)...", args.date or "today")
    result = asyncio.run(run_seed_calendar_demo(date_str=args.date))
    logger.info(
        "Seed demo de calendario finalizado: creados=%d, omitidos=%d",
        result["creados"],
        result["omitidos"],
    )


if __name__ == "__main__":
    main()
