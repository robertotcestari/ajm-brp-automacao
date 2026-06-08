# Schema da planilha de controle BRP

Define as colunas da planilha de controle e o vocabulário de status. As skills de ação
(`registrar-planilha-brp`) preenchem o que conseguem; o restante é triagem humana.

A planilha atual da AJM tem 5 colunas (`Nº do Processo`, `Parte Contrária`,
`advogado responsável`, `audiência`, `prazo defesa`). Este schema **mantém** esses dados e
acrescenta o que a automação precisa, sem quebrar o que a equipe já usa.

## Colunas

### Identificação — preenchidas automaticamente a partir do e-mail

| Coluna | Descrição | Origem |
|--------|-----------|--------|
| `Nº do Processo` | Número CNJ completo | Assunto do e-mail |
| `Parte Contrária` | Nome da parte autora (quem acionou o Banco BRP) | Assunto do e-mail |
| `Tribunal/UF` | Ex.: `TJSP / SP` | Derivado do número (ver `tribunais-cnj.md`) |
| `Link dos autos` | URL de acesso, quando o e-mail traz | Corpo do e-mail |
| `Chave` | Chave do processo, quando o e-mail traz | Corpo do e-mail |
| `Data de recebimento` | Data em que o BRP recebeu a citação | Data do e-mail **original** do BRP |

### Fluxo — distribuição e triagem

| Coluna | Descrição | Vocabulário |
|--------|-----------|-------------|
| `Advogado responsável` | A quem foi distribuído | nome (ou vazio até distribuir) |
| `Status da triagem` | Onde o caso está no fluxo | `Novo` · `Em análise` · `Distribuído` · `Concluído` |

### Prazos — vêm dos autos (humano, por enquanto)

| Coluna | Descrição | Observação |
|--------|-----------|------------|
| `Audiência` | Data/hora da audiência | Preencher se o e-mail informar; senão `verificar autos`. Use `não` quando confirmado que não há |
| `Prazo de defesa` | Data-limite da contestação | Quase nunca vem no e-mail → `verificar autos` |
| `Fonte do prazo` | De onde veio a informação | `E-mail` · `Autos` · `Provisório` |

### Automação — controle do projeto

| Coluna | Descrição | Vocabulário |
|--------|-----------|-------------|
| `Status da pasta` | Pasta do processo no servidor | `Criada` · `Pendente` |
| `Caminho da pasta` | Caminho completo da pasta | texto |
| `Petição baixada` | PDF da inicial na pasta | `Sim` · `Não` |
| `Status da minuta` | Estágio do rascunho de defesa | `Não iniciada` · `Rascunho gerado` · `Em revisão` · `Protocolada` |
| `Teses aplicáveis` | Teses selecionadas (Fase 2) | lista separada por `;` |

## Regras importantes

- **Data de recebimento = data do e-mail original do BRP**, não a data em que alguém
  reencaminhou. O corpo costuma trazer "Recebemos hoje, via DJE, a citação" — a data desse
  envio original é a que vale para contagem de prazo.
- Campo que a automação não consegue preencher recebe **`verificar autos`**, nunca um valor
  inventado. É melhor um campo honestamente vazio do que um prazo errado.
- Não duplicar linha: antes de inserir, conferir se o `Nº do Processo` já existe na planilha.
