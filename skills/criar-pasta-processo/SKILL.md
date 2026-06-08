---
name: criar-pasta-processo
description: >-
  Cria a pasta de um processo da carteira BRP no servidor/VPN do escritório AJM Advogados,
  seguindo a nomenclatura padrão definida em assets/nomenclatura-pastas.md, com as subpastas
  de citação, petição e defesa. Reutiliza a pasta se já existir e devolve o caminho para
  registrar na planilha. Use depois de processar-citacao-brp, ou sempre que precisar abrir a
  pasta de um processo novo da BRP.
---

# Criar pasta do processo BRP

Cria a estrutura de pastas de um processo no servidor/VPN. A pasta é onde a citação, a
petição inicial (Fase 2) e a minuta de defesa vão morar, então criá-la cedo e de forma
padronizada evita que documentos fiquem soltos.

> **Padrão confirmado pela AJM.** Base `G:\A.Digital\BRP`, nome no formato
> `<PARTE> - <NÚMERO>` (ver `assets/nomenclatura-pastas.md`). O modo `--simular` continua
> útil para conferir o caminho sem gravar, ou em máquinas sem o drive `G:` mapeado.

## Como executar

1. Leia `assets/nomenclatura-pastas.md` para obter o caminho-base (`BASE`), o padrão de nome
   e a lista de subpastas.
2. Monte o nome da pasta a partir do registro da citação (`numero_processo` e
   `parte_contraria`), aplicando as regras de sanitização do asset.
3. Use o script `scripts/criar_pasta.py`, que sanitiza o nome, cria a pasta e as subpastas
   (sem sobrescrever se já existir) e devolve o caminho completo. Em modo simulação
   (`--simular`), ele só imprime o que faria.

```
python scripts/criar_pasta.py --base "<BASE>" --numero "<numero>" --parte "<parte>"
# ou, enquanto a BASE não estiver confirmada:
python scripts/criar_pasta.py --base "<BASE>" --numero "<numero>" --parte "<parte>" --simular
```

4. Devolva o caminho criado para alimentar a planilha (`caminho_pasta` e
   `status_pasta = Criada`) via `registrar-planilha-brp`.

Se o caminho-base não estiver acessível (sem VPN, permissão negada), **não falhe em
silêncio**: relate o caminho pretendido e o erro, para a triagem humana criar manualmente.

## Exemplo

Entrada: `numero=4010600-83.2026.8.26.0007`, `parte=ANDRESSA APARECIDA DOS SANTOS`.

Caminho resultante (padrão confirmado da AJM):

```
G:\A.Digital\BRP\Andressa Aparecida dos Santos - 4010600-83.2026.8.26.0007
```

A parte entra em caixa de título (conectivos como "dos" em minúsculo) e o número CNJ é mantido
como veio. A pasta é plana por padrão; com `--subpastas` cria também `01 - Citação`,
`02 - Petição inicial` e `03 - Defesa` dentro dela.
