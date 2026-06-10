#!/usr/bin/env python3
"""Write BRP process records from SQLite into the control spreadsheet on demand."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "lib"))
import brp_db  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from append_to_planilha import (  # noqa: E402
    PADROES,
    carrega_ou_cria,
    monta_valores,
    normaliza_num,
    norm,
    vazio,
)


PLACEHOLDER_PRAZO = "verificar autos"


def planilha_path(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit)
    config = brp_db.load_config()
    value = config.get("planilha_path")
    if not value:
        raise ValueError("Informe --planilha ou configure planilha_path em config/brp.config.json.")
    return brp_db.resolve_path(value, brp_db.ROOT / "Defesas BRP.xlsx")


def carregar_registros(conn, numero: str | None, todos: bool):
    if numero:
        rows = conn.execute(
            "SELECT * FROM processos WHERE numero_processo = ?",
            (numero,),
        ).fetchall()
    elif todos:
        rows = conn.execute(
            """
            SELECT *
            FROM processos
            ORDER BY COALESCE(data_recebimento, ''), numero_processo
            """
        ).fetchall()
    else:
        raise ValueError("Use --numero <CNJ> ou --todos para confirmar o escopo.")
    return [brp_db.row_to_dict(row) for row in rows]


def aplicar_registro(ws, colmap, registro):
    num = registro.get("numero_processo")
    if vazio(num):
        return {"acao": "pulado", "motivo": "sem_numero_processo"}

    valores = monta_valores(registro)
    col_proc = colmap["Nº do Processo"]
    alvo = normaliza_num(num)

    linha_existente = None
    for row_idx in range(2, ws.max_row + 1):
        if normaliza_num(ws.cell(row=row_idx, column=col_proc).value) == alvo and alvo:
            linha_existente = row_idx
            break

    if linha_existente:
        atualizados = []
        for coluna, valor in valores.items():
            col_idx = colmap[coluna]
            atual = ws.cell(row=linha_existente, column=col_idx).value
            substituir = vazio(atual)
            if (
                not substituir
                and coluna == "Prazo de defesa"
                and norm(atual) == norm(PLACEHOLDER_PRAZO)
                and norm(valor) != norm(PLACEHOLDER_PRAZO)
            ):
                substituir = True
            if substituir:
                ws.cell(row=linha_existente, column=col_idx, value=valor)
                atualizados.append(coluna)
        return {
            "acao": "atualizado" if atualizados else "sem_alteracao",
            "linha": linha_existente,
            "processo": num,
            "campos_preenchidos": atualizados,
        }

    nova = ws.max_row + 1
    for coluna, padrao in PADROES.items():
        valores.setdefault(coluna, padrao)
    for coluna, valor in valores.items():
        ws.cell(row=nova, column=colmap[coluna], value=valor)
    return {"acao": "inserido", "linha": nova, "processo": num}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=None)
    ap.add_argument("--planilha", default=None)
    scope = ap.add_mutually_exclusive_group(required=True)
    scope.add_argument("--numero", help="Registra apenas um processo CNJ vindo do SQLite")
    scope.add_argument("--todos", action="store_true", help="Registra todos os processos do SQLite")
    args = ap.parse_args()

    db_path = brp_db.db_path_from_config(args.db)
    destino = planilha_path(args.planilha)

    conn = brp_db.connect(db_path)
    try:
        brp_db.init_db(conn)
        registros = carregar_registros(conn, args.numero, args.todos)
    finally:
        conn.close()

    if args.numero and not registros:
        sys.exit(f"Processo não encontrado no SQLite: {args.numero}")

    try:
        wb, ws, colmap = carrega_ou_cria(destino)
    except Exception as exc:
        sys.exit(
            f"Não consegui abrir a planilha ({destino}): {exc}. "
            "Verifique a VPN e se o arquivo não está aberto/bloqueado."
        )

    resultados = [aplicar_registro(ws, colmap, registro) for registro in registros]
    wb.save(destino)

    resumo = {
        "acao": "planilha_registrada_do_sqlite",
        "db": str(db_path),
        "planilha": str(destino),
        "processos_lidos": len(registros),
        "inseridos": sum(1 for item in resultados if item["acao"] == "inserido"),
        "atualizados": sum(1 for item in resultados if item["acao"] == "atualizado"),
        "sem_alteracao": sum(1 for item in resultados if item["acao"] == "sem_alteracao"),
        "pulados": sum(1 for item in resultados if item["acao"] == "pulado"),
        "resultados": resultados,
    }
    print(json.dumps(resumo, ensure_ascii=False))


if __name__ == "__main__":
    main()
