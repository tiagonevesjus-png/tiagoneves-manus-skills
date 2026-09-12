# Rótulos TNADV — identificadores e via de escrita

Criados e verificados em 12/09/2026 na caixa do escritório.

## Por que a escrita passa pelo Zapier

O conector Gmail da Anthropic é **somente leitura e rascunho**. Ele lê mensagens,
lista rótulos e cria rascunho, mas não cria nem aplica rótulo: a chamada retorna
`Insufficient scope`, exigindo `gmail.labels` ou `gmail.modify`, escopos que esse
conector não solicita. Reautorizar o Google Workspace não resolve, porque o
conector nunca pede esses escopos.

A escrita de rótulo passa, então, pelo **Zapier**, app Gmail
(`selected_api: GoogleMailV2CLIAPI`), conexão `tiagonevesadvo@gmail.com`.

Verificado por teste de ida e volta: rótulo criado pelo Zapier aparece na
listagem do conector Gmail. É a mesma caixa. Ela recebe tanto em
`tiagonevesadvo@gmail.com` quanto em `tiagoneves.jus@gmail.com`, e envia como
`tiagoneves.jus@gmail.com`.

### Ações habilitadas, e as que ficaram de fora

Habilitadas: `label` (cria), `add_label`, `remove_label`, `remove_thread_label`.

Deliberadamente **não** habilitadas: `delete_email`, `archive_email`,
`forward_email`, `reply_to_message`, `draft_v2`. A triagem não apaga, não
arquiva, não encaminha e não responde. Manter essas ações fora do servidor é
barreira técnica, não apenas regra de conduta.

## Identificadores

| Rótulo | ID |
|---|---|
| `TNADV/Intimações` | `Label_59` |
| `TNADV/Prazos` | `Label_60` |
| `TNADV/Audiências` | `Label_61` |
| `TNADV/Clientes` | `Label_62` |
| `TNADV/Financeiro` | `Label_63` |
| `TNADV/Gestão Pública` | `Label_64` |
| `TNADV/Administrativo` | `Label_65` |
| `TNADV/Arquivo` | `Label_66` |
| `TNADV/Triagem/Processado` | `Label_67` |
| `TNADV/Triagem/Revisar` | `Label_68` |
| `TNADV/Pessoal` | `Label_69` |

Confira os IDs com `list_labels` do conector Gmail antes de uma varredura em
lote: rótulo recriado à mão ganha ID novo.

## Como aplicar

```
execute_zapier_write_action
  selected_api: GoogleMailV2CLIAPI
  action: add_label
  params:
    message_id: <id da mensagem, obtido em search_threads do conector Gmail>
    new_label_ids: ["Label_59", "Label_67"]
```

Fluxo de trabalho: **leia pelo conector Gmail, escreva pelo Zapier.** A leitura é
mais rica pelo conector (busca com sintaxe Gmail, corpo completo via
`get_thread`); a escrita só existe no Zapier.

`add_label` preserva `UNREAD`. Confirmado em produção: mensagens de audiência
rotuladas continuaram não lidas.

## Cores

O Zapier não define cor de rótulo. A paleta prevista (Intimações em vermelho,
Prazos em vermelho escuro, Audiências em laranja, Clientes em azul, Financeiro
em verde, Gestão Pública em roxo, Administrativo em cinza, Arquivo em cinza
claro, Processado em menta, Revisar em amarelo, Pessoal em azul claro) precisa
ser aplicada uma única vez, à mão, na interface do Gmail.
