#!/usr/bin/env python3
"""Cria em lote as pastas dos 3 processos BRP novos recebidos em 08/06/2026."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from criar_pasta import formata_parte, sanitiza

BASE = r"G:\A.Digital\BRP"

PROCESSOS = [
    ("0803241-76.2026.8.18.0028", "AILTON DE ARAUJO CASTELO BRANCO"),
    ("0114245-38.2026.8.04.1000", "SAMYA GUSMÃO ALMEIDA"),
    ("0122841-71.2026.8.05.0001", "RAISSA MILENA SANTOS MOURA DA SILVA"),
]

criadas, reutilizadas, erros = [], [], []

for numero, parte in PROCESSOS:
    nome = f"{formata_parte(parte)} - {sanitiza(numero)}"
    destino = Path(BASE) / nome
    try:
        ja_existia = destino.exists()
        destino.mkdir(parents=True, exist_ok=True)
        for sub in ["01 - Citação", "02 - Petição inicial", "03 - Defesa"]:
            (destino / sub).mkdir(parents=True, exist_ok=True)
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
