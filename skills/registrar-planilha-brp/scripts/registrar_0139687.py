#!/usr/bin/env python3
"""Registra o processo 0139687-06.2026.8.04.1000 - JOAO BATISTA MARIALVA DE SOUZA (01/06/2026, perdido no batch anterior)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from append_to_planilha import carrega_ou_cria, monta_valores, normaliza_num, vazio, PADROES

PLANILHA = r"G:\A.Digital\BRP\Gooroo\Planilha de Defesas - Gooroo\Cópia de Defesas BRP 5.xlsx"

REGISTROS = [
    {
        "numero_processo": "0139687-06.2026.8.04.1000",
        "parte_contraria": "JOAO BATISTA MARIALVA DE SOUZA",
        "tribunal_uf": "TJAM / AM",
        "data_recebimento": "01/06/2026",
        "audiencia": "verificar autos",
        "prazo_defesa": "verificar autos",
        "status_pasta": "Criada",
        "caminho_pasta": r"G:\A.Digital\BRP\Joao Batista Marialva de Souza - 0139687-06.2026.8.04.1000",
    },
]


def main():
    try:
        wb, ws, colmap = carrega_ou_cria(PLANILHA)
    except Exception as e:
        print(f"ERRO ao abrir planilha: {e}", file=sys.stderr)
        sys.exit(1)

    col_proc = colmap["No do Processo"] if "No do Processo" in colmap else colmap["Nº do Processo"]
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
