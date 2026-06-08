#!/usr/bin/env python3
"""Registra em lote os 6 processos BRP recebidos em 05/06/2026."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from append_to_planilha import carrega_ou_cria, monta_valores, normaliza_num, vazio, PADROES

PLANILHA = r"G:\A.Digital\BRP\Gooroo\Planilha de Defesas - Gooroo\Cópia de Defesas BRP 5.xlsx"

REGISTROS = [
    # ── 05/06/2026 (e-mails de Ana Heloisa) ────────────────────────────────
    # Citação via correios — data de recebimento estimada pelo BRP como 03/06
    {"numero_processo": "0802349-48.2026.8.14.0136", "parte_contraria": "ELIONAY SOUSA FERREIRA",
     "tribunal_uf": "TJPA / PA", "data_recebimento": "03/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos",
     "audiencia_obs": "citacao via correios (nao DJE); data estimada pelo BRP"},
    # Carta de citação correios — BRP confirma recebimento em 03/06
    {"numero_processo": "0879645-70.2025.8.20.5001", "parte_contraria": "LUCIANA RAYANE MARTINS CIPRIANO",
     "tribunal_uf": "TJRN / RN", "data_recebimento": "03/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 05/06 — TJRS com link e chave
    {"numero_processo": "5016919-46.2026.8.21.0021", "parte_contraria": "LUIS PAULO TROMBETTA",
     "tribunal_uf": "TJRS / RS", "data_recebimento": "05/06/2026",
     "link_autos": "https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50169194620268210021&codComarca=21",
     "chave": "663871481526",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 05/06 — TJSP (eproc) com link e chave
    {"numero_processo": "4004370-40.2026.8.26.0099", "parte_contraria": "WILLIAM DAVID DE OLIVEIRA SAVIELO",
     "tribunal_uf": "TJSP / SP", "data_recebimento": "05/06/2026",
     "link_autos": "https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php?acao=tjsp@consulta_publica_eproc/exibir_processo&acao_origem=tjsp@consulta_publica_eproc/consultar&acao_retorno=tjsp@consulta_publica_eproc/consultar&num_processo=40043704020268260099",
     "chave": "752279539726",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 05/06 — TJMT sem link/chave
    {"numero_processo": "1029453-09.2026.8.11.0041", "parte_contraria": "DANIEL ASSIS DE MORAES",
     "tribunal_uf": "TJMT / MT", "data_recebimento": "05/06/2026",
     "audiencia": "verificar autos", "prazo_defesa": "verificar autos"},
    # DJE 05/06 — TJSP (eproc) com link e chave
    {"numero_processo": "4005983-52.2026.8.26.0566", "parte_contraria": "MARIA DA PENHA DA SILVA CESCHI",
     "tribunal_uf": "TJSP / SP", "data_recebimento": "05/06/2026",
     "link_autos": "https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php?acao=tjsp@consulta_publica_eproc/exibir_processo&acao_origem=tjsp@consulta_publica_eproc/consultar&acao_retorno=tjsp@consulta_publica_eproc/consultar&num_processo=40059835220268260566",
     "chave": "163628497726",
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
