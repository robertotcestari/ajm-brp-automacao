---
name: registrar-planilha-brp
description: >-
  Registra (ou atualiza) uma linha na planilha de controle da carteira BRP da AJM
  Advogados a partir dos dados de uma citação já extraída. Garante que cada processo
  apareça uma única vez (dedup pelo número CNJ) e preenche apenas os campos conhecidos,
  deixando os demais como "verificar autos". Use esta skill depois de processar-citacao-brp,
  ou sempre que precisar lançar/atualizar um processo da BRP na planilha de controle.
---

# Registrar na planilha de controle BRP

Esta skill grava na planilha de controle o resultado da triagem de uma citação. Ela é a
"memória" do fluxo: é contra ela que o intake confere se um processo já foi tratado, então a
consistência aqui importa mais que velocidade.

A planilha mora em um **arquivo `.xlsx` no servidor/VPN local**. A automação roda na máquina
do escritório com esse caminho acessível. As colunas e o vocabulário de status estão em
`assets/schema-planilha.md` — leia esse arquivo se tiver dúvida sobre algum campo.

## Princípios

- **Não duplicar.** Antes de inserir, procure o `numero_processo` na coluna "Nº do Processo".
  Se já existe, atualize a linha existente (preenchendo campos que estavam vazios) em vez de
  criar outra. É o filtro de segurança que torna a execução horária idempotente — rodar duas
  vezes não bagunça a planilha.
- **Não inventar.** Campo sem informação recebe `verificar autos` ou fica vazio, nunca um
  palpite. Ver o porquê em `assets/schema-planilha.md`.
- **Preservar o que a equipe já preencheu.** Se um advogado já pôs o prazo ou o responsável à
  mão, não sobrescreva com `verificar autos`.

## Como executar

Use o script `scripts/append_to_planilha.py`, que cuida do dedup, do mapeamento de colunas e
de preservar valores já preenchidos. Ele recebe o caminho da planilha e os campos do registro
(em JSON) e devolve se inseriu, atualizou ou pulou.

```
python scripts/append_to_planilha.py --planilha "<caminho.xlsx>" --registro '<json>'
```

O JSON do registro usa as chaves produzidas por `processar-citacao-brp` (`numero_processo`,
`parte_contraria`, `tribunal_uf`, `comarca_origem`, `link_autos`, `chave`, `data_recebimento`,
`audiencia`, `audiencia_obs`, `prazo_defesa`, `fonte_prazo`). Campos de fluxo e automação
(`advogado_responsavel`, `status_triagem`, `status_pasta`, `caminho_pasta`, etc.) podem vir
junto quando já conhecidos; o que faltar entra com o padrão do schema (`Novo`, `Pendente`...).

Se o caminho da planilha não estiver acessível (sem VPN, arquivo aberto/bloqueado), **não
falhe em silêncio**: relate o que tentou e o registro que seria gravado, para a triagem
humana resolver.

## Exemplo

Registro de entrada (do Exemplo 3, TJPA):

```json
{
  "numero_processo": "0854280-80.2026.8.14.0301",
  "parte_contraria": "FELIX NUNES DE ALMEIDA NETO",
  "tribunal_uf": "TJPA / PA",
  "comarca_origem": "0301 (a confirmar)",
  "data_recebimento": "27/05/2026",
  "audiencia": "30/09/2026 09:30",
  "audiencia_obs": "telepresencial via Microsoft Teams",
  "prazo_defesa": "verificar autos",
  "fonte_prazo": "E-mail"
}
```

Resultado esperado: como o número ainda não está na planilha, insere uma nova linha com
`Status da triagem = Novo`, `Status da pasta = Pendente`, `Status da minuta = Não iniciada`,
e `Prazo de defesa = verificar autos`.
