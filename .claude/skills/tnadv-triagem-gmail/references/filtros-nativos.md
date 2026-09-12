# Filtros nativos do Gmail — taxonomia TNADV

## Por que filtro nativo, e não integração externa

O conector Gmail da Anthropic lê, busca e cria rascunho. Ele **não** cria nem
aplica rótulo: a chamada devolve `Insufficient scope`, exigindo `gmail.labels`
ou `gmail.modify`, escopos que esse conector não solicita. Reautorizar o Google
Workspace não altera isso, porque o conector nunca os pede. Verificado três
vezes, inclusive após reautorização.

A resposta do escritório não foi contornar com integração de terceiro, e sim
usar o mecanismo que o próprio Gmail oferece.

Vantagens do filtro nativo sobre qualquer automação externa:

- **Roda sempre.** Age no servidor do Google, em toda mensagem que chega, sem
  sessão aberta, sem agendamento, sem cota.
- **Não depende de ninguém.** Nenhuma credencial de terceiro, nenhum serviço
  intermediário vendo o conteúdo da caixa. Ponto relevante para sigilo
  profissional e para a LGPD: menos um operador no caminho do dado.
- **É auditável.** As regras ficam visíveis na interface do Gmail e versionadas
  neste repositório.
- **Não erra por interpretação.** Remetente `trt16.jus.br` é `trt16.jus.br`.

O que o filtro não faz é julgar. Distinguir intimação de aviso de movimentação,
ou conta do escritório de conta pessoal, exige leitura. Essa metade fica com a
skill, que produz relatório em vez de rótulo.

## Gerar e importar

```bash
python3 tools/gerar_filtros_gmail.py --saida "saida/filtros-tnadv-gmail.xml"
```

Importe em: **Gmail → Configurações → Ver todas as configurações → Filtros e
endereços bloqueados → Importar filtros → escolher arquivo → Abrir arquivo →
Criar filtros**.

Marque "Aplicar novo filtro às conversas correspondentes" apenas se quiser que
o Gmail rotule também o passivo já existente. Para caixa grande, prefira aplicar
em lote pela busca, controlando o alcance.

## Regras atuais

| Rótulo | Critério |
|---|---|
| `TNADV/Intimações` | remetente `trt16.jus.br` |
| `TNADV/Intimações` | remetente `jus.br` (qualquer órgão do Judiciário) |
| `TNADV/Intimações` | remetente `comunica.pje.jus.br` ou `djen.csjt.jus.br` |
| `TNADV/Intimações` | assunto com "intimação" ou "Diário da Justiça" |
| `TNADV/Audiências` | assunto com "audiência" |
| `TNADV/Administrativo` | remetente `oab.org.br`, `oabma.org.br` |
| `TNADV/Financeiro` | remetente `asaas`, `pagbank`, `stone`, `cora` |
| `TNADV/Pessoal` | remetente `nubank`, `recargapay`, `mercadolivre`, `drogasil`, Google Wallet |
| `TNADV/Pessoal` | remetente `noreply-accounts@google.com` |
| `TNADV/Administrativo` | remetente `anthropic`, `midpage`, `easyjur`, `microsoft` |

Todos os remetentes foram observados na caixa em 12/09/2026. Nenhum é suposição.
Ao acrescentar regra, confirme antes que o remetente existe.

## Garantia de que nenhum filtro é destrutivo

`core/filtros_gmail.py` recusa a montagem de regra que contenha
`shouldArchive`, `shouldTrash`, `shouldMarkAsRead`, `forwardTo` ou `shouldSpam`.
Filtro TNADV só rotula. O teste `test_nenhum_filtro_arquiva_apaga_ou_marca_como_lido`
trava isso, e falha se alguém tentar afrouxar a regra.

Todas as regras carregam `shouldNeverSpam`, para que comunicação de tribunal
jamais caia em spam.

## Identificadores dos rótulos

Úteis para conferência e para operações em massa. Confira com `list_labels`
antes de usar em lote: rótulo recriado à mão ganha ID novo.

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

Os onze rótulos já existem na caixa. As cores precisam ser aplicadas uma única
vez, à mão, na interface do Gmail: Intimações em vermelho, Prazos em vermelho
escuro, Audiências em laranja, Clientes em azul, Financeiro em verde, Gestão
Pública em roxo, Administrativo em cinza, Pessoal em azul claro, Arquivo em
cinza claro, Processado em menta, Revisar em amarelo.

## Aplicar rótulo ao passivo, em massa

Pela interface do Gmail, sem automação:

1. Busque, por exemplo, `from:(trt16.jus.br) -label:TNADV/Intimações`
2. Selecione tudo, e confirme "Selecionar todas as conversas que correspondem"
3. Aplique o rótulo pelo menu de rótulos

Buscas úteis para a primeira arrumação:

```
from:(jus.br) -label:TNADV/Intimações
subject:(audiência OR audiencia) -label:TNADV/Audiências
from:(asaas OR pagbank OR stone OR cora) -label:TNADV/Financeiro
from:(nubank OR recargapay OR mercadolivre) -label:TNADV/Pessoal
is:unread older_than:1y -from:(jus.br)
```
