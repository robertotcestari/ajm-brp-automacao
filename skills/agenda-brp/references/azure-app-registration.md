# Registro de app no Azure AD (Microsoft Entra ID) — passo a passo

Necessário uma vez, para a automação **escrever** no calendário BRP via Microsoft Graph.
Executado pelo administrador do Microsoft 365 da AJM. Tempo: ~15 min.

## Papéis necessários

- Para **registrar o app**: no mínimo *Application Developer*.
- Para **conceder consentimento** de uma permissão de aplicativo do Microsoft Graph
  (`Calendars.ReadWrite` é uma *application permission*): **Privileged Role Administrator**
  (ou Administrador Global). Cloud Application Administrator **não** basta para permissões de
  aplicativo do Graph. Vale confirmar antes de começar.

## Passo 1 — Registrar o aplicativo

1. Entrar em **https://entra.microsoft.com**.
2. **Identidade → Aplicativos → Registros de aplicativo → Novo registro**.
3. **Nome:** `AJM-BRP-Automacao`.
4. **Tipos de conta com suporte:** *Somente neste diretório organizacional* (single tenant).
5. Deixar **URI de redirecionamento** em branco (não é app interativo). **Registrar**.

## Passo 2 — Anotar os identificadores

Na página **Visão geral** do app, copiar:

- **ID do aplicativo (cliente)** → `GRAPH_CLIENT_ID`
- **ID do diretório (locatário)** → `GRAPH_TENANT_ID`

## Passo 3 — Criar o segredo do cliente

1. No app, ir em **Certificados e segredos → Segredos do cliente → Novo segredo do cliente**.
2. Descrição (ex.: `automacao-brp`) e validade (a Microsoft limita a 24 meses e recomenda
   menos de 12; anotar a data para renovar antes de expirar).
3. Clicar em **Adicionar** e **copiar o Valor imediatamente** — ele só aparece uma vez →
   `GRAPH_CLIENT_SECRET`.

> Mais seguro que segredo é usar **certificado**; se a AJM preferir, dá para trocar depois. Para
> começar, o segredo do cliente é suficiente.

## Passo 4 — Permissão de calendário + consentimento

1. **Permissões de API → Adicionar uma permissão → Microsoft Graph**.
2. **Permissões de aplicativo** (não "delegadas") → buscar e marcar **`Calendars.ReadWrite`**
   → **Adicionar permissões**.
3. Clicar em **Conceder consentimento do administrador para [AJM]** e confirmar. O status das
   permissões deve ficar com o ✔ verde ("Concedido para…").

## Passo 5 (recomendado) — Restringir a uma única caixa

Por padrão a permissão de aplicativo alcança o calendário de **todas** as caixas. Para limitar
à caixa que hospeda o calendário BRP, criar uma *Application Access Policy* no Exchange Online
PowerShell:

```powershell
New-ApplicationAccessPolicy -AppId <GRAPH_CLIENT_ID> `
  -PolicyScopeGroupId <caixa-ou-grupo-do-BRP> -AccessRight RestrictAccess `
  -Description "Restringe AJM-BRP-Automacao a caixa do calendario BRP"
```

## Passo 6 — Entregar para a automação

Configurar como variáveis de ambiente na máquina onde a automação roda:

```
GRAPH_TENANT_ID=...
GRAPH_CLIENT_ID=...
GRAPH_CLIENT_SECRET=...
BRP_MAILBOX=<caixa que hospeda o calendário "BRP">@ajmadvogados.com.br
```

## Pré-requisito do calendário

O calendário **"BRP"** deve existir na caixa de `BRP_MAILBOX` e estar **compartilhado com a
equipe**. O script `criar_evento_graph.py` procura o calendário pelo nome; se não existir, avisa.

## Segurança

- O segredo é sensível: guardar em variável de ambiente/cofre, nunca em texto plano
  compartilhado ou em repositório.
- Renovar antes da expiração (Passo 3).
- A política do Passo 5 garante o **menor privilégio** — o app só toca na caixa do BRP.

---

*Fontes: Microsoft Learn — "How to register an app in Microsoft Entra ID"
(https://learn.microsoft.com/en-us/entra/identity-platform/quickstart-register-app),
"Add and manage app credentials"
(https://learn.microsoft.com/en-us/entra/identity-platform/how-to-add-credentials) e
"Grant tenant-wide admin consent to an application"
(https://learn.microsoft.com/en-us/entra/identity/enterprise-apps/grant-admin-consent).*
