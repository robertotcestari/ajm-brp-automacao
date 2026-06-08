#!/usr/bin/env python3
"""Registra em lote os 5 processos BRP recebidos em 08/06/2026."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from append_to_planilha import carrega_ou_cria, monta_valores, normaliza_num, vazio, PADROES

PLANILHA = r"G:\A.Digital\BRP\Gooroo\Planilha de Defesas - Gooroo\Cópia de Defesas BRP 5.xlsx"

REGISTROS = [
    # ── 08/06/2026 (e-mails de Kristian, diretos) ───────────────────────────
    # DJE 08/06 — TJPI sem audiência
    {"numero_processo": "0803241-76.2026.8.18.0028", "parte_contraria": "AILTON DE ARAUJO CASTELO BRANCO",
     "tribunal_uf": "TJPI / PI", "data_recebimento": "08/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 08/06 — TJAM com audiência 17/07/2026 08:30
    {"numero_processo": "0114245-38.2026.8.04.1000", "parte_contraria": "SAMYA GUSMÃO ALMEIDA",
     "tribunal_uf": "TJAM / AM", "data_recebimento": "08/06/2026",
     "audiencia": "17/07/2026 08:30", "prazo_defesa": "verificar autos"},
    # DJE 08/06 — TJBA com audiência 17/07/2026 08:30
    {"numero_processo": "0122841-71.2026.8.05.0001", "parte_contraria": "RAISSA MILENA SANTOS MOURA DA SILVA",
     "tribunal_uf": "TJBA / BA", "data_recebimento": "08/06/2026",
     "audiencia": "17/07/2026 08:30", "prazo_defesa": "verificar autos"},
    # DJE 08/06 — TJAM sem audiência
    {"numero_processo": "0161695-74.2026.8.04.1000", "parte_contraria": "CHRISTIANE PERES DE SOUZA",
     "tribunal_uf": "TJAM / AM", "data_recebimento": "08/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 08/06 — TJAM sem audiência
    {"numero_processo": "0157520-37.2026.8.04.1000", "parte_contraria": "ROBERTA NASCIMENTO DA SILVA",
     "tribunal_uf": "TJAM / AM", "data_recebimento": "08/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
]


def main():
    try:
        wb, ws, colmap = carrega_ou_cria(PLANILHA)
    except Exception as e:
        print(f"ERRO ao abrir planilha: {e}", file=sys.stderr)
        sys.exit(1)

    col_proc = colmap["Nº do Processo"]
    resultados = []

    for registro in REGISTROS:
        num = registro.get("numero_processo", "")
        alvo = normaliza_num(num)
        valores = monta_valores(registro)

        linha_existente = None
        for r in range(2, ws.max_row + 1):
            if normaliza_num(ws.cell(row=r, column=col_proc).value) == alvo and alvo:
                linha_existente = r
                break

        if linha_existente:
            atualizados = []
            for coluna, valor in valores.items():
                ci = colmap[coluna]
                atual = ws.cell(row=linha_existente, column=ci).value
                if vazio(atual):
                    ws.cell(row=linha_existente, column=ci, value=valor)
                    atualizados.append(coluna)
            resultados.append({"acao": "atualizado", "processo": num, "campos": atualizados})
        else:
            nova = ws.max_row + 1
            for coluna, padrao in PADROES.items():
                valores.setdefault(coluna, padrao)
            for coluna, valor in valores.items():
                ws.cell(row=nova, column=colmap[coluna], value=valor)
            resultados.append({"acao": "inserido", "linha": nova, "processo": num})

    wb.save(PLANILHA)

    inseridos = [r for r in resultados if r["acao"] == "inserido"]
    atualizados = [r for r in resultados if r["acao"] == "atualizado"]
    print(f"\nOK: {len(inseridos)} inseridos, {len(atualizados)} ja existiam (atualizados)")
    for r in resultados:
        tag = "+" if r["acao"] == "inserido" else "~"
        print(f"  [{tag}] {r['processo']}")


if __name__ == "__main__":
    main()
