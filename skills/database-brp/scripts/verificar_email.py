#!/usr/bin/env python3
"""Check whether an email message_id has already been processed."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--message-id", required=True)
    args = ap.parse_args()

    db_path = brp_db.db_path_from_config(args.db)
    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        row = brp_db.email_processado(conn, args.message_id)
    finally:
        conn.close()

    print(json.dumps({
        "db": str(db_path),
        "message_id": args.message_id,
        "processado": row is not None,
        "registro": row,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
