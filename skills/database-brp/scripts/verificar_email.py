#!/usr/bin/env python3
"""Check whether an email has already been processed."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--message-id", default=None)
    ap.add_argument("--internet-message-id", default=None)
    ap.add_argument(
        "--reference-message-id",
        action="append",
        default=[],
        help="Message-Id listed in References/In-Reply-To; may be passed multiple times",
    )
    args = ap.parse_args()
    if not args.message_id and not args.internet_message_id and not args.reference_message_id:
        sys.exit("Informe --message-id, --internet-message-id ou --reference-message-id.")

    db_path = brp_db.db_path_from_config(args.db)
    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        row = None
        matched_by = None
        matched_value = None
        if args.message_id:
            row = brp_db.email_processado(conn, args.message_id)
            if row:
                matched_by = "message_id"
                matched_value = args.message_id
        if row is None and args.internet_message_id:
            row = brp_db.email_processado_por_internet_message_id(
                conn, args.internet_message_id
            )
            if row:
                matched_by = "internet_message_id"
                matched_value = args.internet_message_id
        for ref in args.reference_message_id:
            if row is not None:
                break
            row = brp_db.email_processado_por_internet_message_id(conn, ref)
            if row:
                matched_by = "reference_message_id"
                matched_value = ref
    finally:
        conn.close()

    print(json.dumps({
        "db": str(db_path),
        "message_id": args.message_id,
        "internet_message_id": args.internet_message_id,
        "reference_message_ids": args.reference_message_id,
        "processado": row is not None,
        "matched_by": matched_by,
        "matched_value": matched_value,
        "registro": row,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
