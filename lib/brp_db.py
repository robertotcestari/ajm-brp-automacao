"""
SQLite helpers for the AJM/BRP local automation database.

The database is intentionally local-first: Daniel's computer owns the writable
SQLite file, and the network folder receives validated backup copies.
"""
from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "config" / "brp.config.json"
DEFAULT_DB = ROOT / "data" / "ajm-brp.sqlite3"


SCHEMA_VERSION = 1


PROCESSO_FIELDS = [
    "numero_processo",
    "parte_contraria",
    "tribunal_uf",
    "comarca_origem",
    "link_autos",
    "chave",
    "data_recebimento",
    "advogado_responsavel",
    "status_triagem",
    "audiencia",
    "audiencia_obs",
    "prazo_defesa",
    "fonte_prazo",
    "status_pasta",
    "caminho_pasta",
    "peticao_baixada",
    "status_minuta",
    "teses_aplicaveis",
]


PROCESSO_DEFAULTS = {
    "status_triagem": "Novo",
    "prazo_defesa": "verificar autos",
    "status_pasta": "Pendente",
    "peticao_baixada": "Não",
    "status_minuta": "Não iniciada",
}


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def load_config() -> dict[str, Any]:
    if not CONFIG_FILE.exists():
        return {}
    return json.loads(CONFIG_FILE.read_text(encoding="utf-8"))


def resolve_path(value: str | None, default: Path) -> Path:
    if not value:
        return default
    path = Path(os.path.expandvars(os.path.expanduser(value)))
    if not path.is_absolute():
        path = ROOT / path
    return path


def db_path_from_config(explicit: str | None = None) -> Path:
    config = load_config()
    return resolve_path(explicit or config.get("sqlite_path"), DEFAULT_DB)


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA busy_timeout = 5000")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS meta (
          chave TEXT PRIMARY KEY,
          valor TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS processos (
          numero_processo TEXT PRIMARY KEY,
          parte_contraria TEXT,
          tribunal_uf TEXT,
          comarca_origem TEXT,
          link_autos TEXT,
          chave TEXT,
          data_recebimento TEXT,
          advogado_responsavel TEXT,
          status_triagem TEXT NOT NULL DEFAULT 'Novo',
          audiencia TEXT,
          audiencia_obs TEXT,
          prazo_defesa TEXT NOT NULL DEFAULT 'verificar autos',
          fonte_prazo TEXT,
          status_pasta TEXT NOT NULL DEFAULT 'Pendente',
          caminho_pasta TEXT,
          peticao_baixada TEXT NOT NULL DEFAULT 'Não',
          status_minuta TEXT NOT NULL DEFAULT 'Não iniciada',
          teses_aplicaveis TEXT,
          payload_json TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS emails_processados (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          message_id TEXT NOT NULL UNIQUE,
          internet_message_id TEXT,
          assunto TEXT,
          remetente TEXT,
          destinatarios TEXT,
          recebido_em TEXT,
          processado_em TEXT NOT NULL,
          numero_processo TEXT,
          status TEXT NOT NULL,
          erro TEXT,
          raw_ref TEXT,
          payload_json TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_emails_internet_message_id
          ON emails_processados(internet_message_id);

        CREATE INDEX IF NOT EXISTS idx_emails_numero_processo
          ON emails_processados(numero_processo);

        CREATE TABLE IF NOT EXISTS logs_automacao (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_processo TEXT,
          email_message_id TEXT,
          acao TEXT NOT NULL,
          resultado TEXT NOT NULL,
          detalhes_json TEXT,
          registrado_em TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS backups_sqlite (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          arquivo TEXT NOT NULL,
          checksum_sha256 TEXT NOT NULL,
          tamanho_bytes INTEGER NOT NULL,
          integrity_check TEXT NOT NULL,
          criado_em TEXT NOT NULL
        );
        """
    )
    conn.execute(
        "INSERT OR REPLACE INTO meta (chave, valor) VALUES (?, ?)",
        ("schema_version", str(SCHEMA_VERSION)),
    )
    conn.commit()


def row_to_dict(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return {key: row[key] for key in row.keys()}


def compact_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def load_json_arg(value: str | None, file_path: str | None) -> dict[str, Any]:
    if value:
        return json.loads(value)
    if file_path:
        return json.loads(Path(file_path).read_text(encoding="utf-8"))
    raise ValueError("Informe --registro ou --registro-arquivo.")


def upsert_processo(conn: sqlite3.Connection, registro: dict[str, Any]) -> dict[str, Any]:
    numero = str(registro.get("numero_processo") or "").strip()
    if not numero:
        raise ValueError("Registro sem 'numero_processo'.")

    now = now_iso()
    atual = conn.execute(
        "SELECT * FROM processos WHERE numero_processo = ?", (numero,)
    ).fetchone()

    dados = {field: registro.get(field) for field in PROCESSO_FIELDS}
    dados["numero_processo"] = numero
    dados["payload_json"] = compact_json(registro)

    if atual is None:
        for field, default in PROCESSO_DEFAULTS.items():
            if dados.get(field) in (None, ""):
                dados[field] = default
        dados["created_at"] = now
        dados["updated_at"] = now
        fields = PROCESSO_FIELDS + ["payload_json", "created_at", "updated_at"]
        placeholders = ",".join(["?"] * len(fields))
        conn.execute(
            f"INSERT INTO processos ({','.join(fields)}) VALUES ({placeholders})",
            [dados.get(field) for field in fields],
        )
        acao = "inserido"
        campos_atualizados: list[str] = []
    else:
        campos_atualizados = []
        for field in PROCESSO_FIELDS:
            if field == "numero_processo":
                continue
            novo = dados.get(field)
            atual_val = atual[field]
            if novo not in (None, "") and atual_val in (None, ""):
                conn.execute(
                    f"UPDATE processos SET {field} = ?, updated_at = ? WHERE numero_processo = ?",
                    (novo, now, numero),
                )
                campos_atualizados.append(field)
            elif field == "prazo_defesa" and atual_val == "verificar autos" and novo not in (None, "", "verificar autos"):
                conn.execute(
                    "UPDATE processos SET prazo_defesa = ?, updated_at = ? WHERE numero_processo = ?",
                    (novo, now, numero),
                )
                campos_atualizados.append(field)
        conn.execute(
            "UPDATE processos SET payload_json = ?, updated_at = ? WHERE numero_processo = ?",
            (dados["payload_json"], now, numero),
        )
        acao = "atualizado"

    conn.commit()
    return {"acao": acao, "processo": numero, "campos_atualizados": campos_atualizados}


def registrar_email(conn: sqlite3.Connection, registro: dict[str, Any]) -> dict[str, Any]:
    message_id = str(registro.get("message_id") or "").strip()
    if not message_id:
        raise ValueError("Registro sem 'message_id'.")

    status = str(registro.get("status") or "processado").strip()
    payload = compact_json(registro)
    campos = {
        "message_id": message_id,
        "internet_message_id": registro.get("internet_message_id"),
        "assunto": registro.get("assunto"),
        "remetente": registro.get("remetente"),
        "destinatarios": registro.get("destinatarios"),
        "recebido_em": registro.get("recebido_em"),
        "processado_em": registro.get("processado_em") or now_iso(),
        "numero_processo": registro.get("numero_processo"),
        "status": status,
        "erro": registro.get("erro"),
        "raw_ref": registro.get("raw_ref"),
        "payload_json": payload,
    }
    fields = list(campos.keys())
    placeholders = ",".join(["?"] * len(fields))
    updates = ",".join(
        f"{field}=excluded.{field}" for field in fields if field != "message_id"
    )
    conn.execute(
        f"""
        INSERT INTO emails_processados ({','.join(fields)})
        VALUES ({placeholders})
        ON CONFLICT(message_id) DO UPDATE SET {updates}
        """,
        [campos[field] for field in fields],
    )
    conn.commit()
    return {"acao": "email_registrado", "message_id": message_id, "status": status}


def email_processado(conn: sqlite3.Connection, message_id: str) -> dict[str, Any] | None:
    return row_to_dict(
        conn.execute(
            "SELECT * FROM emails_processados WHERE message_id = ?", (message_id,)
        ).fetchone()
    )


def log_acao(
    conn: sqlite3.Connection,
    *,
    acao: str,
    resultado: str,
    numero_processo: str | None = None,
    email_message_id: str | None = None,
    detalhes: Any | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO logs_automacao
          (numero_processo, email_message_id, acao, resultado, detalhes_json, registrado_em)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            numero_processo,
            email_message_id,
            acao,
            resultado,
            compact_json(detalhes) if detalhes is not None else None,
            now_iso(),
        ),
    )
    conn.commit()
