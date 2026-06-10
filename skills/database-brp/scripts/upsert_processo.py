#!/usr/bin/env python3
"""Insert or update a BRP process in the local SQLite database."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--registro")
    g.add_argument("--registro-arquivo")
    args = ap.parse_args()

    registro = brp_db.load_json_arg(args.registro, args.registro_arquivo)
    db_path = brp_db.db_path_from_config(args.db)
    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        result = brp_db.upsert_processo(conn, registro)
    finally:
        conn.close()

    result["db"] = str(db_path)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
