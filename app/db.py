import sqlite3
from datetime import datetime

from flask import current_app, g


SCHEMA_STATEMENTS = [
    """
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone_number TEXT UNIQUE NOT NULL,
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS otp_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT NOT NULL,
        otp_hash TEXT NOT NULL,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        attempts INTEGER NOT NULL DEFAULT 0,
        verified INTEGER NOT NULL DEFAULT 0
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS medicines (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        expiry_date TEXT NOT NULL,
        stock_quantity INTEGER NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        medicine_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        payment_mode TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id),
        FOREIGN KEY (medicine_id) REFERENCES medicines (id)
    );
    """,
]

SAMPLE_MEDICINES = [
    ("Paracetamol 500mg", 32.0, "2026-01-31", 120),
    ("Cetirizine 10mg", 28.5, "2025-11-15", 85),
    ("Vitamin C Tablets", 99.0, "2026-03-10", 60),
    ("Digital Thermometer", 145.0, "2028-12-31", 40),
]


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    @app.before_request
    def _ensure_db():
        get_db()

    @app.teardown_appcontext
    def _close_db(exception=None):
        close_db(exception)

    with app.app_context():
        db = get_db()
        for statement in SCHEMA_STATEMENTS:
            db.execute(statement)
        db.commit()
        seed_medicines(db)


def now_iso():
    return datetime.utcnow().isoformat()


def seed_medicines(db):
    """Insert sample medicines if the table is empty."""
    existing = db.execute("SELECT COUNT(*) as count FROM medicines").fetchone()
    if existing["count"] > 0:
        return
    db.executemany(
        """
        INSERT INTO medicines (name, price, expiry_date, stock_quantity)
        VALUES (?, ?, ?, ?)
        """,
        SAMPLE_MEDICINES,
    )
    db.commit()
