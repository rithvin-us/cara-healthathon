"""Vercel Python function entrypoint for the Cara FastAPI backend.

vercel.json rewrites every /api/* request here; FastAPI then routes on the
original path (/api/v1/...).

Without DATABASE_URL the function runs the self-contained demo: SQLite in /tmp
(the only writable path on Vercel), seeded with synthetic data on cold start.
That data is per-instance and resets on cold starts. Set DATABASE_URL to a
Postgres database for anything that must persist.
"""

import os
import sys

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
sys.path.insert(0, BACKEND_DIR)

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/cara.db")

from app.main import app  # noqa: E402
from app.seed import seed_database  # noqa: E402

if os.environ["DATABASE_URL"].startswith("sqlite:////tmp/") or os.getenv("CARA_SEED_ON_START") == "1":
    seed_database()

__all__ = ["app"]
