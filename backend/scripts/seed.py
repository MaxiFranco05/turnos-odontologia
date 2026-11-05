import argparse
import asyncio
import datetime
import logging
import sys
from pathlib import Path

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.infrastructure.config import get_settings
from app.infrastructure.database import init_engine, init_session_factory
from app.infrastructure.seed import seed_data

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("seed-cli")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parses CLI arguments for the seed runner."""
    parser = argparse.ArgumentParser(
        description="Database seeder for Turnos Odontología (C-16).",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Purge existing appointments, templates, and users before seeding.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Base date for demonstration appointments (YYYY-MM-DD). Defaults to next Monday.",
    )
    return parser.parse_args(argv)


async def run_seed(reset: bool = False, date_str: str | None = None) -> dict[str, int]:
    """Connects to database and executes the seeding routine."""
    base_date: datetime.date | None = None
    if date_str:
        base_date = datetime.date.fromisoformat(date_str)

    settings = get_settings()
    engine = init_engine(settings.async_database_url, echo=settings.DEBUG)
    session_factory = init_session_factory(engine)

    try:
        async with session_factory() as session:
            logger.info("Executing seed routine (reset=%s, base_date=%s)...", reset, base_date)
            counts = await seed_data(session=session, reset=reset, base_date=base_date)
            logger.info(
                "[SEED SUCCESS] Database populated:\n"
                "  - Usuarios: %d\n"
                "  - Plantillas: %d\n"
                "  - Turnos: %d",
                counts["usuarios"],
                counts["plantillas"],
                counts["turnos"],
            )
            return counts
    finally:
        await engine.dispose()


def main() -> None:
    """Main CLI entrypoint."""
    args = parse_args()
    try:
        asyncio.run(run_seed(reset=args.reset, date_str=args.date))
    except Exception as exc:
        logger.error("Failed to execute database seeding: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
