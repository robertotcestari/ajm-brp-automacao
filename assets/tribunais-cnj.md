# Número CNJ → Tribunal / UF / Sistema

Todo processo da carteira BRP vem com número no padrão CNJ:

```
NNNNNNN-DD.AAAA.J.TR.OOOO
        │     │   │ │  └── OOOO = unidade de origem (foro/comarca/vara)
        │     │   │ └───── TR  = tribunal
        │     │   └─────── J   = segmento do Judiciário
        │     └─────────── AAAA = ano de ajuizamento
        └───────────────── NNNNNNN-DD = número sequencial + dígito verificador
```

Para a carteira BRP, `J` é quase sempre **8 (Justiça Estadual)**. Nesse caso, `TR` indica a UF:

| TR | Tribunal | UF | TR | Tribunal | UF |
|----|----------|----|----|----------|----|
| 01 | TJAC | AC | 15 | TJPB | PB |
| 02 | TJAL | AL | 16 | TJPR | PR |
| 03 | TJAP | AP | 17 | TJPE | PE |
| 04 | TJAM | AM | 18 | TJPI | PI |
| 05 | TJBA | BA | 19 | TJRJ | RJ |
| 06 | TJCE | CE | 20 | TJRN | RN |
| 07 | TJDFT | DF | 21 | TJRS | RS |
| 08 | TJES | ES | 22 | TJRO | RO |
| 09 | TJGO | GO | 23 | TJRR | RR |
| 10 | TJMA | MA | 24 | TJSC | SC |
| 11 | TJMT | MT | 25 | TJSE | SE |
| 12 | TJMS | MS | 26 | TJSP | SP |
| 13 | TJMG | MG | 27 | TJTO | TO |
| 14 | TJPA | PA |    |          |    |

Outros segmentos (menos comuns nessa carteira): `4` = Justiça Federal (TRFs), `5` = Justiça do Trabalho (TRTs), `6` = Justiça Eleitoral.

## Como derivar

1. Pegue os dois números após o ano: `J.TR`.
2. Se `J = 8`, use a tabela acima para obter tribunal e UF.
3. O bloco `OOOO` é o **código de origem** (foro/comarca). Registre o código; só afirme o nome da comarca se tiver certeza — caso contrário deixe o código e marque a comarca como "a confirmar".

## Sistema do tribunal (para acessar os autos)

O sistema processual varia por tribunal e não está sempre no número. Use o que o e-mail informar:

- Se o corpo do e-mail trouxer um **link** (ex.: `eproc-consulta.tjsp.jus.br`), registre-o como o sistema/acesso.
- Se trouxer **chave do processo**, registre — ela é necessária para abrir os autos em sistemas eproc.
- Caso o e-mail só diga "via DJE", registre `DJE` como origem da intimação e deixe o sistema como "a confirmar" (a triagem humana abrirá os autos).

> A integração automática com os sistemas dos tribunais (PJe, eproc, ESAJ, Projudi) está **fora do escopo da Fase 1**. Aqui apenas registramos link/chave quando o e-mail os fornece.
