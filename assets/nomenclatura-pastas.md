# Nomenclatura das pastas de processo (BRP)

Padrão **confirmado pela AJM**. A skill `criar-pasta-processo` lê daqui — para mudar o padrão,
edite este arquivo (não é preciso mexer no código).

## Caminho-base (servidor/VPN)

```
BASE = G:\A.Digital\BRP
```

> Caminho Windows (a automação roda na máquina do escritório, com o drive `G:` mapeado).

## Padrão de nome da pasta

```
<PARTE CONTRÁRIA> - <NÚMERO CNJ>
```

Exemplo real:

```
G:\A.Digital\BRP\Andressa Aparecida dos Santos - 4010600-83.2026.8.26.0007
```

Observações:

- A **parte vem primeiro**, depois ` - ` (espaço-hífen-espaço), depois o número CNJ completo.
- O nome da parte é grafado em **caixa de título** ("Andressa Aparecida dos Santos"), com
  conectivos em minúsculo (`de`, `da`, `do`, `dos`, `das`, `e`). Como o e-mail traz o nome em
  CAIXA ALTA, a skill converte para caixa de título ao montar a pasta.
- O número CNJ é mantido exatamente como vem (com pontos e traço).

## Subpastas

Pelo exemplo atual, a pasta do processo é **plana** (sem subpastas). Se a AJM quiser organizar
os documentos internamente (citação / petição / defesa), basta ligar a opção `--subpastas` na
skill — está desligada por padrão para respeitar a convenção atual.

## Regras de sanitização

- Remover do nome da parte caracteres inválidos para nome de arquivo (`/ \ : * ? " < > |`) e
  espaços nas pontas; manter acentos.
- Se a pasta já existir, **não** recriar nem sobrescrever — apenas reutilizar e seguir.
