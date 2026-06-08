#!/usr/bin/env python3
"""Lança em lote audiências e tarefas de verificação de prazo para os 36 processos BRP."""
import json, os, sys
from pathlib import Path

# Carrega credenciais do graph.env
ENV_FILE = Path(__file__).parents[3] / "config" / "graph.env"
if ENV_FILE.exists():
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

sys.path.insert(0, str(Path(__file__).parent))
from criar_evento_graph import get_token, garante_categoria, acha_calendario, monta_evento, upsert_evento, CATEGORIAS

MAILBOX = os.environ.get("BRP_MAILBOX", "ajmadvogados@ajmadvogados.com.br")
CALENDARIO = "BRP"
HOJE = "2026-06-04"

# 9 audiências com data/hora confirmada
AUDIENCIAS = [
    ("0700998-36.2026.8.02.0081",  "LUIS GABRIEL DOS SANTOS",               "2026-09-01T08:00:00", ""),
    ("1005502-96.2026.8.13.0245",  "BARBARA LUDIMILA GOMES DE PAIVA",        "2026-07-09T14:00:00", "Webex https://tjmg.webex.com/tjmg/j.php?MTID=mdce2c1e429372347685794cb3816ce10 | Num 2343 546 6902 | Senha 2jdsala1"),
    ("0008883-48.2026.8.05.0150",  "GABRIEL VINICIUS BAHIA CARVALHO",        "2026-07-20T14:00:00", ""),
    ("0119550-63.2026.8.05.0001",  "CASSIO ALBERTO FRANCA MARQUES",          "2026-07-14T15:00:00", ""),
    ("0807761-88.2026.8.19.0210",  "MARIA ISABEL MENEZES DE SOUZA",          "2026-07-21T13:30:00", ""),
    ("0020733-18.2026.8.05.0080",  "EMERSON DE MIRANDA LAZARO",              "2026-09-04T10:40:00", "LifeSize https://call.lifesizecloud.com/3461784 | Codigo Sala 3461784"),
    ("0118638-66.2026.8.05.0001",  "LUIS HENRIQUE DOS SANTOS NOVAES",        "2026-07-06T07:40:00", ""),
    ("0019708-50.2026.8.16.0019",  "MERIELEN VERISSIMO DE SOUSA RAMOS",      "2026-08-05T16:40:00", "Projudi https://projudi2.tjpr.jus.br/projudi/ | Chave audiencia PAXLU P8BGK 9XCLT W4HDM"),
    ("0116975-82.2026.8.05.0001",  "LAIRANIA CARVALHO BORGES",               "2026-07-07T10:40:00", ""),
]

# Todos os 36 processos (prazo = verificar autos)
TODOS_PROCESSOS = [
    ("0700998-36.2026.8.02.0081", "LUIS GABRIEL DOS SANTOS"),
    ("0157092-55.2026.8.04.1000", "JOEL MELGUEIRA BEZERRA"),
    ("0808708-16.2026.8.14.0006", "HEBERT RODRIGUES DE FREITAS"),
    ("1005502-96.2026.8.13.0245", "BARBARA LUDIMILA GOMES DE PAIVA"),
    ("4005170-84.2026.8.26.0223", "ADRIANA DE AZEVEDO PEREIRA"),
    ("5007392-28.2026.8.21.0035", "JULIANO WOLFART BASTOS"),
    ("0157934-35.2026.8.04.1000", "EVANILDO DA SILVA NASCIMENTO"),
    ("3002040-55.2026.8.19.0011", "ARTHUR EMILIO DOS SANTOS TAVARES"),
    ("0705158-85.2026.8.07.0010", "WASHINGTON DA SILVA SOUZA"),
    ("0008883-48.2026.8.05.0150", "GABRIEL VINICIUS BAHIA CARVALHO"),
    ("0119550-63.2026.8.05.0001", "CASSIO ALBERTO FRANCA MARQUES"),
    ("5002403-74.2026.8.21.0165", "ADENILSON ALVARENGA DO NASCIMENTO"),
    ("0023625-77.2026.8.04.1000", "JHONNATAS CHAVES RODRIGUES"),
    ("0023632-69.2026.8.04.1000", "RAIMAR NEVES TAVARES"),
    ("0807761-88.2026.8.19.0210", "MARIA ISABEL MENEZES DE SOUZA"),
    ("0052926-69.2026.8.04.1000", "JOSIMAR MEIRELES BRITO"),
    ("5022283-93.2026.8.21.0022", "JEFFERSON GLEIDE MARQUES DE SOUZA"),
    ("5022335-89.2026.8.21.0022", "EBERTON BANDEIRA PINTOS"),
    ("0020733-18.2026.8.05.0080", "EMERSON DE MIRANDA LAZARO"),
    ("5148921-40.2026.8.21.0001", "GUSTAVO DE OLIVEIRA PEREIRA"),
    ("5012643-87.2026.8.21.0015", "ANA MARA GROSS SCHERER"),
    ("0118638-66.2026.8.05.0001", "LUIS HENRIQUE DOS SANTOS NOVAES"),
    ("8004363-22.2026.8.05.0080", "EMANUELE CERQUEIRA SANTIAGO DOS SANTOS"),
    ("0156831-90.2026.8.04.1000", "JOEL MELGUEIRA BEZERRA"),
    ("0139795-35.2026.8.04.1000", "THERLYSSON SILVA DE OLIVEIRA"),
    ("0137184-12.2026.8.04.1000", "JESSICA DE OLIVEIRA SOUSA"),
    ("0148504-59.2026.8.04.1000", "GABRIEL DUTRAM LIMA"),
    ("5011947-38.2026.8.24.0930", "BARBARA DEL VALLE VALLEJO QUILARQUE"),
    ("5060975-72.2026.8.24.0930", "MARCELO ROBERTO DA SILVA DOS SANTOS"),
    ("5060236-02.2026.8.24.0930", "RODRIGO NOZIKOWSKI"),
    ("5057984-26.2026.8.24.0930", "ANDERSON VINICIUS OLIVEIRA PESSOA"),
    ("5055442-35.2026.8.24.0930", "ROBERT EDUARDO CASTELLANOS URBANEJA"),
    ("0803758-20.2026.8.19.0007", "ELMO LUIZ LUCHEZZI MENDES"),
    ("5005203-31.2026.8.21.0018", "CARLOS ROBERTO FERREIRA CAMARGO"),
    ("0019708-50.2026.8.16.0019", "MERIELEN VERISSIMO DE SOUSA RAMOS"),
    ("0116975-82.2026.8.05.0001", "LAIRANIA CARVALHO BORGES"),
    ("5007049-32.2026.8.21.0035", "JULIANO WOLFART BASTOS"),
    ("0740280-44.2026.8.07.0016", "WESLEI ALVES MACHADO"),
]


def main():
    token = get_token()

    # Garante categorias
    for tipo in ("audiencia", "prazo", "verificar"):
        nome, cor = CATEGORIAS[tipo]
        garante_categoria(token, MAILBOX, nome, cor)

    # Acha (ou cria) calendário BRP
    cal_id = acha_calendario(token, MAILBOX, CALENDARIO, criar=True)

    criados, atualizados, erros = [], [], []

    def lancar(tipo, numero, parte, inicio, dur, obs):
        evento = monta_evento(tipo, numero, parte, inicio, dur, obs)
        try:
            acao, _ = upsert_evento(token, MAILBOX, cal_id, tipo, numero, evento)
            marca = "+" if acao == "criado" else "~"
            print(f"  [{marca}] ({acao}) {evento['subject']}")
            (criados if acao == "criado" else atualizados).append(evento["subject"])
        except SystemExit as e:
            print(f"  [!] ERRO {numero}: {e}", file=sys.stderr)
            erros.append(numero)

    # ── Audiências ──────────────────────────────────────────────────────────
    print("=== Lancando audiencias ===")
    for numero, parte, inicio, obs in AUDIENCIAS:
        lancar("audiencia", numero, parte, inicio, 60, obs)

    # ── Verificar prazo (todos os 36) ───────────────────────────────────────
    print("\n=== Criando tarefas verificar prazo ===")
    for numero, parte in TODOS_PROCESSOS:
        lancar("verificar", numero, parte, HOJE, 0, "")

    print(f"\nTotal: {len(criados)} criados, {len(atualizados)} atualizados, {len(erros)} erros")
    if erros:
        print("Erros:", erros)


if __name__ == "__main__":
    main()
