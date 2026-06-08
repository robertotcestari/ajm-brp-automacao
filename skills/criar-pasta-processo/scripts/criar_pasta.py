#!/usr/bin/env python3
"""
Cria a pasta de um processo BRP no servidor/VPN, seguindo a nomenclatura do escritório.

- Sanitiza o nome da parte para nome de pasta válido (mantém acentos).
- Cria a pasta e as subpastas padrão; se já existir, reutiliza (não sobrescreve).
- Modo --simular: só mostra o que faria, sem gravar (útil enquanto a BASE não é confirmada).

Uso:
  python criar_pasta.py --base "/Volumes/ajm/Processos/BRP" \
      --numero "0800680-38.2026.8.10.0049" --parte "ALEXANDRE GLEISON SOUSA ANDRADE"
"""
import argparse
import json
import re
import sys
from pathlib import Path

# Subpastas opcionais (ligar com --subpastas). Ver assets/nomenclatura-pastas.md
SUBPASTAS = ["01 - Citação", "02 - Petição inicial", "03 - Defesa"]
INVALIDOS = r'[/\\:*?"<>|]'
# conectivos que ficam em minúsculo na caixa de título de nomes em português
CONECTIVOS = {"de", "da", "do", "das", "dos", "e", "di", "du"}


def sanitiza(nome):
    nome = re.sub(INVALIDOS, "", str(nome or ""))
    return re.sub(r"\s+", " ", nome).strip()


def formata_parte(nome):
    """Caixa de título à brasileira: 'ALEXANDRE DE SOUSA' -> 'Alexandre de Sousa'."""
    nome = sanitiza(nome)
    palavras = []
    for i, p in enumerate(nome.split(" ")):
        baixo = p.lower()
        if i > 0 and baixo in CONECTIVOS:
            palavras.append(baixo)
        else:
            palavras.append(baixo.capitalize())
    return " ".join(palavras)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default=r"G:\A.Digital\BRP", help="Caminho-base no servidor/VPN")
    ap.add_argument("--numero", required=True, help="Número CNJ do processo")
    ap.add_argument("--parte", required=True, help="Parte contrária")
    ap.add_argument("--subpastas", action="store_true", help="Cria subpastas internas (citação/petição/defesa)")
    ap.add_argument("--simular", action="store_true", help="Não grava; só mostra o caminho")
    args = ap.parse_args()

    # Padrão da AJM: <PARTE> - <NÚMERO>, parte em caixa de título
    nome_pasta = f"{formata_parte(args.parte)} - {sanitiza(args.numero)}"
    destino = Path(args.base) / nome_pasta
    subpastas = [destino / s for s in SUBPASTAS] if args.subpastas else []

    if args.simular:
        print(json.dumps({
            "acao": "simulado",
            "caminho": str(destino),
            "subpastas": [str(s) for s in subpastas],
        }, ensure_ascii=False))
        return

    try:
        ja_existia = destino.exists()
        destino.mkdir(parents=True, exist_ok=True)
        for s in subpastas:
            s.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        sys.exit(f"Não consegui criar a pasta em {destino}: {e}. "
                 "Verifique a VPN/permissões. Caminho pretendido acima para criação manual.")

    print(json.dumps({
        "acao": "reutilizada" if ja_existia else "criada",
        "caminho": str(destino),
        "subpastas": [str(s) for s in subpastas],
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
