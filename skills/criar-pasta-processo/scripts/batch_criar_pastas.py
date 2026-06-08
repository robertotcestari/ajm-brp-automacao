#!/usr/bin/env python3
"""Cria em lote as pastas dos 36 processos BRP (01-03/06/2026)."""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from criar_pasta import formata_parte, sanitiza

BASE = r"G:\A.Digital\BRP"

PROCESSOS = [
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

criadas, reutilizadas, erros = [], [], []

for numero, parte in PROCESSOS:
    nome = f"{formata_parte(parte)} - {sanitiza(numero)}"
    destino = Path(BASE) / nome
    try:
        ja_existia = destino.exists()
        destino.mkdir(parents=True, exist_ok=True)
        if ja_existia:
            reutilizadas.append(str(destino))
        else:
            criadas.append(str(destino))
    except Exception as e:
        erros.append({"processo": numero, "erro": str(e)})

print(f"Criadas: {len(criadas)} | Ja existiam: {len(reutilizadas)} | Erros: {len(erros)}")
for p in criadas:
    print(f"  [+] {p}")
for p in reutilizadas:
    print(f"  [=] {p}")
for e in erros:
    print(f"  [!] {e['processo']}: {e['erro']}", file=sys.stderr)
