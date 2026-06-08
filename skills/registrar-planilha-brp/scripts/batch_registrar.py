#!/usr/bin/env python3
"""Registra em lote os 37 processos BRP (01-03/06/2026) na planilha de controle."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from append_to_planilha import carrega_ou_cria, monta_valores, normaliza_num, vazio, PADROES

PLANILHA = r"G:\A.Digital\BRP\Gooroo\Planilha de Defesas - Gooroo\Cópia de Defesas BRP 5.xlsx"

REGISTROS = [
    # ── 03/06/2026 ──────────────────────────────────────────────────────────
    {"numero_processo":"0700998-36.2026.8.02.0081","parte_contraria":"LUIS GABRIEL DOS SANTOS","tribunal_uf":"TJAL / AL","data_recebimento":"03/06/2026","audiencia":"01/09/2026 08:00","prazo_defesa":"verificar autos"},
    {"numero_processo":"0157092-55.2026.8.04.1000","parte_contraria":"JOEL MELGUEIRA BEZERRA","tribunal_uf":"TJAM / AM","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"autor tem outro processo 0156831-90.2026.8.04.1000"},
    {"numero_processo":"0808708-16.2026.8.14.0006","parte_contraria":"HEBERT RODRIGUES DE FREITAS","tribunal_uf":"TJPA / PA","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"1005502-96.2026.8.13.0245","parte_contraria":"BARBARA LUDIMILA GOMES DE PAIVA","tribunal_uf":"TJMG / MG","data_recebimento":"03/06/2026","link_autos":"https://www.tjmg.jus.br/portal-tjmg/","chave":"558088873426","audiencia":"09/07/2026 14:00","audiencia_obs":"Webex https://tjmg.webex.com/tjmg/j.php?MTID=mdce2c1e429372347685794cb3816ce10 | Nº 2343 546 6902 | Senha 2jdsala1","prazo_defesa":"verificar autos"},
    {"numero_processo":"4005170-84.2026.8.26.0223","parte_contraria":"ADRIANA DE AZEVEDO PEREIRA","tribunal_uf":"TJSP / SP","data_recebimento":"03/06/2026","link_autos":"https://eproc-consulta.tjsp.jus.br/consulta_1g/externo_controlador.php?acao=tjsp@consulta_publica_eproc/exibir_processo&acao_origem=tjsp@consulta_publica_eproc/consultar&acao_retorno=tjsp@consulta_publica_eproc/consultar&num_processo=40051708420268260223","chave":"830199536826","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5007392-28.2026.8.21.0035","parte_contraria":"JULIANO WOLFART BASTOS","tribunal_uf":"TJRS / RS","data_recebimento":"03/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50073922820268210035&codComarca=35","chave":"897914561726","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"autor tem outros dois processos: 5007049-32 e 5006810-28"},
    {"numero_processo":"0157934-35.2026.8.04.1000","parte_contraria":"EVANILDO DA SILVA NASCIMENTO","tribunal_uf":"TJAM / AM","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"3002040-55.2026.8.19.0011","parte_contraria":"ARTHUR EMILIO DOS SANTOS TAVARES","tribunal_uf":"TJRJ / RJ","data_recebimento":"03/06/2026","link_autos":"https://eproc1g-ws.tjrj.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&acao_origem=processo_consulta_publica&acao_retorno=processo_consulta_publica&num_processo=30020405520268190011","chave":"179136658326","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0705158-85.2026.8.07.0010","parte_contraria":"WASHINGTON DA SILVA SOUZA","tribunal_uf":"TJDFT / DF","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0008883-48.2026.8.05.0150","parte_contraria":"GABRIEL VINICIUS BAHIA CARVALHO","tribunal_uf":"TJBA / BA","data_recebimento":"03/06/2026","audiencia":"20/07/2026 14:00","prazo_defesa":"verificar autos"},
    {"numero_processo":"0119550-63.2026.8.05.0001","parte_contraria":"CASSIO ALBERTO FRANCA MARQUES","tribunal_uf":"TJBA / BA","data_recebimento":"03/06/2026","audiencia":"14/07/2026 15:00","prazo_defesa":"verificar autos"},
    {"numero_processo":"5002403-74.2026.8.21.0165","parte_contraria":"ADENILSON ALVARENGA DO NASCIMENTO","tribunal_uf":"TJRS / RS","data_recebimento":"03/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50024037420268210165&codComarca=165","chave":"454432151726","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0023625-77.2026.8.04.1000","parte_contraria":"JHONNATAS CHAVES RODRIGUES","tribunal_uf":"TJAM / AM","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0023632-69.2026.8.04.1000","parte_contraria":"RAIMAR NEVES TAVARES","tribunal_uf":"TJAM / AM","data_recebimento":"03/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"autor tem outro processo 0023579-88.2026.8.04.1000"},
    # ── 02/06/2026 ──────────────────────────────────────────────────────────
    {"numero_processo":"0807761-88.2026.8.19.0210","parte_contraria":"MARIA ISABEL MENEZES DE SOUZA","tribunal_uf":"TJRJ / RJ","data_recebimento":"02/06/2026","audiencia":"21/07/2026 13:30","prazo_defesa":"verificar autos"},
    {"numero_processo":"0052926-69.2026.8.04.1000","parte_contraria":"JOSIMAR MEIRELES BRITO","tribunal_uf":"TJAM / AM","data_recebimento":"02/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"autor tem outro processo 0052934-46.2026.8.04.1000"},
    {"numero_processo":"5022283-93.2026.8.21.0022","parte_contraria":"JEFFERSON GLEIDE MARQUES DE SOUZA","tribunal_uf":"TJRS / RS","data_recebimento":"02/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50222839320268210022&codComarca=22","chave":"347984842726","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5022335-89.2026.8.21.0022","parte_contraria":"EBERTON BANDEIRA PINTOS","tribunal_uf":"TJRS / RS","data_recebimento":"02/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50223358920268210022&codComarca=22","chave":"549311008226","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0020733-18.2026.8.05.0080","parte_contraria":"EMERSON DE MIRANDA LAZARO","tribunal_uf":"TJBA / BA","data_recebimento":"02/06/2026","audiencia":"04/09/2026 10:40","audiencia_obs":"LifeSize https://call.lifesizecloud.com/3461784 | Código Sala 3461784","prazo_defesa":"verificar autos"},
    # ── 01/06/2026 ──────────────────────────────────────────────────────────
    {"numero_processo":"5148921-40.2026.8.21.0001","parte_contraria":"GUSTAVO DE OLIVEIRA PEREIRA","tribunal_uf":"TJRS / RS","data_recebimento":"01/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=51489214020268210001&codComarca=1","chave":"865068778926","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5012643-87.2026.8.21.0015","parte_contraria":"ANA MARA GROSS SCHERER","tribunal_uf":"TJRS / RS","data_recebimento":"01/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50126438720268210015&codComarca=15","chave":"879055447526","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0118638-66.2026.8.05.0001","parte_contraria":"LUIS HENRIQUE DOS SANTOS NOVAES","tribunal_uf":"TJBA / BA","data_recebimento":"01/06/2026","audiencia":"06/07/2026 07:40","prazo_defesa":"verificar autos"},
    # ATENÇÃO: LIMINAR CONCEDIDA — limitação descontos R$61,07, abstenção cadastros negativos, descaracterização mora. Contrato 0077215633. Outro processo 8004362-37.2026.8.05.0080
    {"numero_processo":"8004363-22.2026.8.05.0080","parte_contraria":"EMANUELE CERQUEIRA SANTIAGO DOS SANTOS","tribunal_uf":"TJBA / BA","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"LIMINAR CONCEDIDA: limitacao descontos R$61,07; abstencao cadastros negativos; descaracterizacao mora. Contrato 0077215633. Outro proc 8004362-37.2026.8.05.0080"},
    {"numero_processo":"0156831-90.2026.8.04.1000","parte_contraria":"JOEL MELGUEIRA BEZERRA","tribunal_uf":"TJAM / AM","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0139795-35.2026.8.04.1000","parte_contraria":"THERLYSSON SILVA DE OLIVEIRA","tribunal_uf":"TJAM / AM","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0137184-12.2026.8.04.1000","parte_contraria":"JESSICA DE OLIVEIRA SOUSA","tribunal_uf":"TJAM / AM","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0148504-59.2026.8.04.1000","parte_contraria":"GABRIEL DUTRAM LIMA","tribunal_uf":"TJAM / AM","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5011947-38.2026.8.24.0930","parte_contraria":"BARBARA DEL VALLE VALLEJO QUILARQUE","tribunal_uf":"TJSC / SC","data_recebimento":"01/06/2026","link_autos":"https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50119473820268240930","chave":"240426997226","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"intimacao tratada como citacao pelo BRP"},
    {"numero_processo":"5060975-72.2026.8.24.0930","parte_contraria":"MARCELO ROBERTO DA SILVA DOS SANTOS","tribunal_uf":"TJSC / SC","data_recebimento":"01/06/2026","link_autos":"https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50609757220268240930","chave":"971860561526","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5060236-02.2026.8.24.0930","parte_contraria":"RODRIGO NOZIKOWSKI","tribunal_uf":"TJSC / SC","data_recebimento":"01/06/2026","link_autos":"https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50602360220268240930","chave":"217058663226","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5057984-26.2026.8.24.0930","parte_contraria":"ANDERSON VINICIUS OLIVEIRA PESSOA","tribunal_uf":"TJSC / SC","data_recebimento":"01/06/2026","link_autos":"https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50579842620268240930","chave":"694073086426","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"5055442-35.2026.8.24.0930","parte_contraria":"ROBERT EDUARDO CASTELLANOS URBANEJA","tribunal_uf":"TJSC / SC","data_recebimento":"01/06/2026","link_autos":"https://eproc1g.tjsc.jus.br/eproc/externo_controlador.php?acao=processo_seleciona_publica&num_processo=50554423520268240930","chave":"241594922626","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0803758-20.2026.8.19.0007","parte_contraria":"ELMO LUIZ LUCHEZZI MENDES","tribunal_uf":"TJRJ / RJ","data_recebimento":"01/06/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"audiencia mencionada no DJE sem data/hora — verificar autos com urgencia"},
    {"numero_processo":"5005203-31.2026.8.21.0018","parte_contraria":"CARLOS ROBERTO FERREIRA CAMARGO","tribunal_uf":"TJRS / RS","data_recebimento":"01/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50052033120268210018&codComarca=18","chave":"224591030826","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
    {"numero_processo":"0019708-50.2026.8.16.0019","parte_contraria":"MERIELEN VERISSIMO DE SOUSA RAMOS","tribunal_uf":"TJPR / PR","data_recebimento":"01/06/2026","audiencia":"05/08/2026 16:40","audiencia_obs":"Projudi https://projudi2.tjpr.jus.br/projudi/ | Chave audiencia: PAXLU P8BGK 9XCLT W4HDM","prazo_defesa":"verificar autos"},
    {"numero_processo":"0116975-82.2026.8.05.0001","parte_contraria":"LAIRANIA CARVALHO BORGES","tribunal_uf":"TJBA / BA","data_recebimento":"01/06/2026","audiencia":"07/07/2026 10:40","prazo_defesa":"verificar autos"},
    {"numero_processo":"5007049-32.2026.8.21.0035","parte_contraria":"JULIANO WOLFART BASTOS","tribunal_uf":"TJRS / RS","data_recebimento":"01/06/2026","link_autos":"https://consulta.tjrs.jus.br/consulta-processual/processo/resumo?numeroProcesso=50070493220268210035&codComarca=35","chave":"360167982626","audiencia":"verificar autos","prazo_defesa":"verificar autos","audiencia_obs":"autor tem outro processo 5006810-28.2026.8.21.0035"},
    # ── 13/05/2026 — processo com pasta mas sem registro na planilha ────────
    {"numero_processo":"0740280-44.2026.8.07.0016","parte_contraria":"WESLEI ALVES MACHADO","tribunal_uf":"TJDFT / DF","data_recebimento":"13/05/2026","audiencia":"verificar autos","prazo_defesa":"verificar autos"},
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
