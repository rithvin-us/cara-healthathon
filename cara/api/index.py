"""Vercel serverless entrypoint for the Cara FastAPI backend.

Vercel's filesystem is read-only except /tmp, so the SQLite database lives
there and is re-seeded with synthetic demo data on each cold start.
"""
import os
import sys

BACKEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend")
sys.path.insert(0, os.path.abspath(BACKEND_DIR))

os.environ.setdefault("DATABASE_URL", "sqlite:////tmp/cara.db")

from app.main import app  # noqa: E402

if os.environ["DATABASE_URL"].startswith("sqlite:////tmp/"):
    from seed_data import seed_database  # noqa: E402

    seed_database()
