#!/usr/bin/env python3
"""Root CLI entrypoint for database seeding."""
import sys
from pathlib import Path

# Add backend directory to sys.path so app imports work seamlessly
root_dir = Path(__file__).resolve().parent.parent
backend_dir = root_dir / "backend"
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from scripts.seed import main  # type: ignore[import-not-found]

if __name__ == "__main__":
    main()
