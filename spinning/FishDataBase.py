import sqlite3
from pathlib import Path
from datetime import datetime

DATABASE_PATH = Path(__file__).parent / "analytics.db"


def initialize_database():
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS catches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                caught_at TEXT NOT NULL,
                fish_class TEXT NOT NULL
            )
        """)

        connection.execute("""
            CREATE TABLE IF NOT EXISTS bot_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT
            )
        """)


def record_catch(fish_class: str):
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            INSERT INTO catches (
                caught_at,
                fish_class
            )
            VALUES (?, ?)
            """,
            (
                datetime.now().isoformat(
                    timespec="seconds",
                ),
                fish_class,
            ),
        )


def get_statistics_by_day(day: datetime) -> dict:
    with sqlite3.connect(DATABASE_PATH) as connection:
        # prepared_day = datetime.strptime(day, "%d.%m.%Y")
        today = connection.execute(
            """
            SELECT COUNT(*)
            FROM catches
            WHERE DATE(caught_at) = DATE(?, 'localtime')
            """,
                (
                    day,
                ),
        ).fetchone()[0]

        classes = dict(
            connection.execute(
                """
                SELECT fish_class, COUNT(*)
                FROM catches
                WHERE DATE(caught_at) = DATE(?, 'localtime')
                GROUP BY fish_class
                """,
                (
                    day,
                ),
            ).fetchall()
        )

    return {
        "today": today,
        "normal": classes.get("normal", 0),
        "zach": classes.get("zach", 0),
        "trof": classes.get("trof", 0),
        "blue": classes.get("blue", 0),
    }


def get_statistics() -> dict:
    with sqlite3.connect(DATABASE_PATH) as connection:
        total = connection.execute(
            "SELECT COUNT(*) FROM catches"
        ).fetchone()[0]

        today = connection.execute(
            """
            SELECT COUNT(*)
            FROM catches
            WHERE DATE(caught_at) = DATE('now', 'localtime')
            """
        ).fetchone()[0]

        classes = dict(
            connection.execute(
                """
                SELECT fish_class, COUNT(*)
                FROM catches
                WHERE DATE(caught_at) = DATE('now', 'localtime')
                GROUP BY fish_class
                """
            ).fetchall()
        )

    return {
        "total": total,
        "today": today,
        "normal": classes.get("normal", 0),
        "zach": classes.get("zach", 0),
        "trof": classes.get("trof", 0),
        "blue": classes.get("blue", 0),
    }