#!/usr/bin/env python3
"""Create a validated SQLite backup in the AJM network folder."""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def integrity_check(path: Path) -> str:
    conn = sqlite3.connect(path)
    try:
        return conn.execute("PRAGMA integrity_check").fetchone()[0]
    finally:
        conn.close()


def copy_with_sqlite_backup(source: Path, dest: Path) -> None:
    source_conn = sqlite3.connect(source)
    dest_conn = sqlite3.connect(dest)
    try:
        source_conn.backup(dest_conn)
    finally:
        dest_conn.close()
        source_conn.close()


def cleanup_old_backups(backup_dir: Path, retention_days: int) -> list[str]:
    if retention_days <= 0:
        return []
    cutoff = datetime.now() - timedelta(days=retention_days)
    removed: list[str] = []
    for path in backup_dir.glob("ajm-brp-sqlite-*.sqlite3"):
        try:
            if datetime.fromtimestamp(path.stat().st_mtime) >= cutoff:
                continue
            checksum = path.with_suffix(path.suffix + ".sha256")
            path.unlink()
            removed.append(str(path))
            if checksum.exists():
                checksum.unlink()
                removed.append(str(checksum))
        except OSError:
            continue
    return removed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None, help="SQLite source path")
    ap.add_argument("--backup-dir", default=None, help="AJM network backup folder")
    ap.add_argument("--retention-days", type=int, default=None)
    args = ap.parse_args()

    config = brp_db.load_config()
    db_path = brp_db.db_path_from_config(args.db)
    backup_dir = brp_db.resolve_path(
        args.backup_dir or config.get("backup_dir"),
        brp_db.ROOT / "backups",
    )
    retention_days = (
        args.retention_days
        if args.retention_days is not None
        else int(config.get("backup_retention_days", 90))
    )

    if not db_path.exists():
        sys.exit(f"Banco SQLite não encontrado: {db_path}")

    source_integrity = integrity_check(db_path)
    if source_integrity != "ok":
        sys.exit(f"Banco origem falhou no integrity_check: {source_integrity}")

    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    final_path = backup_dir / f"ajm-brp-sqlite-{stamp}.sqlite3"
    tmp_path = backup_dir / f".{final_path.name}.tmp"

    if tmp_path.exists():
        tmp_path.unlink()
    copy_with_sqlite_backup(db_path, tmp_path)
    dest_integrity = integrity_check(tmp_path)
    if dest_integrity != "ok":
        tmp_path.unlink(missing_ok=True)
        sys.exit(f"Backup gerado falhou no integrity_check: {dest_integrity}")

    tmp_path.replace(final_path)
    checksum = sha256_file(final_path)
    checksum_path = final_path.with_suffix(final_path.suffix + ".sha256")
    checksum_path.write_text(f"{checksum}  {final_path.name}\n", encoding="utf-8")

    size = final_path.stat().st_size
    removed = cleanup_old_backups(backup_dir, retention_days)

    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        conn.execute(
            """
            INSERT INTO backups_sqlite
              (arquivo, checksum_sha256, tamanho_bytes, integrity_check, criado_em)
            VALUES (?, ?, ?, ?, ?)
            """,
            (str(final_path), checksum, size, dest_integrity, brp_db.now_iso()),
        )
        conn.commit()
    finally:
        conn.close()

    print(json.dumps({
        "acao": "backup_sqlite_criado",
        "origem": str(db_path),
        "arquivo": str(final_path),
        "checksum": str(checksum_path),
        "sha256": checksum,
        "tamanho_bytes": size,
        "integrity_check": dest_integrity,
        "retention_days": retention_days,
        "removidos": removed,
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
