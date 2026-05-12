import sqlite3
from pathlib import Path
from datetime import datetime


DB_PATH = Path("oilintel.db")


def table_exists(cursor, table_name: str) -> bool:
    cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type='table' AND name=?
        """,
        (table_name,),
    )

    return cursor.fetchone() is not None


def get_column_info(cursor, table_name: str):
    cursor.execute(f"PRAGMA table_info({table_name})")
    return cursor.fetchall()


def get_raw_id_type(cursor) -> str | None:
    info = get_column_info(cursor, "raw_observations")

    for col in info:
        # PRAGMA table_info columns:
        # cid, name, type, notnull, dflt_value, pk
        _, name, col_type, *_ = col

        if name == "id":
            return str(col_type).upper()

    return None


def main():
    if not DB_PATH.exists():
        print(f"Database not found: {DB_PATH}")
        print("Start the app once first so SQLite creates oilintel.db.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if not table_exists(cursor, "raw_observations"):
        print("raw_observations table does not exist yet. Nothing to migrate.")
        conn.close()
        return

    current_id_type = get_raw_id_type(cursor)

    print(f"Current raw_observations.id type: {current_id_type}")

    if current_id_type == "INTEGER":
        print("raw_observations.id is already INTEGER. No migration needed.")
        conn.close()
        return

    suffix = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    backup_table = f"raw_observations_backup_bigint_id_{suffix}"

    print(f"Renaming old raw_observations table to: {backup_table}")

    cursor.execute("PRAGMA foreign_keys=OFF")

    cursor.execute(
        f"""
        ALTER TABLE raw_observations
        RENAME TO {backup_table}
        """
    )

    print("Creating new raw_observations table with INTEGER autoincrement id...")

    cursor.execute(
        """
        CREATE TABLE raw_observations (
            id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            source TEXT NOT NULL,
            series_name TEXT NOT NULL,
            raw_value FLOAT,
            metadata JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(timestamp, source, series_name)
        )
        """
    )

    print("Copying existing rows into new raw_observations table...")

    cursor.execute(
        f"""
        INSERT OR IGNORE INTO raw_observations
            (timestamp, source, series_name, raw_value, metadata, created_at)
        SELECT
            timestamp, source, series_name, raw_value, metadata, created_at
        FROM {backup_table}
        """
    )

    copied = cursor.rowcount

    conn.commit()
    conn.close()

    print("Migration complete.")
    print(f"Rows copied: {copied}")
    print(f"Backup table preserved as: {backup_table}")
    print("You can now restart FastAPI and ingest EIA again.")


if __name__ == "__main__":
    main()