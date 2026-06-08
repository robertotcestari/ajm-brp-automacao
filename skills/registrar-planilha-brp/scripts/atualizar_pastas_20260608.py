#!/usr/bin/env python3
"""Atualiza caminho_pasta e status_pasta para os 5 processos de 08/06/2026."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from append_to_planilha import carrega_ou_cria, monta_valores, normaliza_num, vazio

PLANILHA = r"G:\A.Digital\BRP\Gooroo\Planilha de Defesas - Gooroo\Cópia de Defesas BRP 5.xlsx"

ATUALIZACOES = [
    {"numero_processo": "0803241-76.2026.8.18.0028",
     "status_pasta": "Criada",
     "caminho_pasta": r"G:\A.Digital\BRP\Ailton de Araujo Castelo Branco - 0803241-76.2026.8.18.0028"},
    {"numero_processo": "0114245-38.2026.8.04.1000",
     "status_pasta": "Criada",
     "caminho_pasta": r"G:\A.Digital\BRP\Samya Gusmão Almeida - 0114245-38.2026.8.04.1000"},
    {"numero_processo": "0122841-71.2026.8.05.0001",
     "status_pasta": "Criada",
     "caminho_pasta": r"G:\A.Digital\BRP\Raissa Milena Santos Moura da Silva - 0122841-71.2026.8.05.0001"},
    {"numero_processo": "0161695-74.2026.8.04.1000",
     "status_pasta": "Criada",
     "caminho_pasta": r"G:\A.Digital\BRP\Christiane Peres de Souza - 0161695-74.2026.8.04.1000"},
    {"numero_processo": "0157520-37.2026.8.04.1000",
     "status_pasta": "Criada",
     "caminho_pasta": r"G:\A.Digital\BRP\Roberta Nascimento da Silva - 0157520-37.2026.8.04.1000"},
]


def main():
    try:
        wb, ws, colmap = carrega_ou_cria(PLANILHA)
    except Exception as e:
        print(f"ERRO ao abrir planilha: {e}", file=sys.stderr)
        sys.exit(1)

    col_proc = colmap["Nº do Processo"]
    resultados = []

    for registro in ATUALIZACOES:
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
            resultados.append({"acao": "nao_encontrado", "processo": num})

    wb.save(PLANILHA)

    for r in resultados:
        if r["acao"] == "atualizado":
            campos = r.get("campos", [])
            tag = "~" if campos else "="
            print(f"  [{tag}] {r['processo']} — campos preenchidos: {campos or 'nenhum (já estava preenchido)'}")
        else:
            print(f"  [!] {r['processo']} — NÃO ENCONTRADO na planilha")


if __name__ == "__main__":
    main()
