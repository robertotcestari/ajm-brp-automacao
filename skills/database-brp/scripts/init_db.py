#!/usr/bin/env python3
"""Create or migrate the local AJM/BRP SQLite database."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="SQLite path. Defaults to config sqlite_path or data/ajm-brp.sqlite3")
    args = ap.parse_args()

    db_path = brp_db.db_path_from_config(args.db)
    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()

    print(json.dumps({
        "acao": "db_inicializado",
        "db": str(db_path),
        "schema_version": brp_db.SCHEMA_VERSION,
        "integrity_check": integrity,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
