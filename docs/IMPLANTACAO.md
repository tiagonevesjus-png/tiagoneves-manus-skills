# Implantação — estado e passos pendentes

Situação verificada em 12/09/2026. Este documento diz o que está funcionando, o
que está pronto mas bloqueado, e o que fazer para destravar.

## Quadro geral

| Automação | Estado | O que falta |
|---|---|---|
| Motor de prazos, feriados, CNJ, acervo | **Funcionando** | confirmar calendários locais |
| Planilha viva de controle | **Funcionando** | popular o acervo |
| Dashboard diário (skill) | **Funcionando sob demanda** | — |
| Dashboard diário (Routine) | **Criada e desativada** | vincular conectores e ativar |
| Radar de intimações (skill) | **Funcionando sob demanda** | — |
| Radar de intimações (Routine) | **Criada e desativada** | vincular conectores e ativar |
| Triagem do Gmail | **Bloqueada** | autorizar escrita de rótulos no Gmail |
| Sete skills da camada 2 | **Funcionando sob demanda** | — |

## Permissões verificadas

Testadas de fato nesta implantação, não presumidas:

| Capacidade | Resultado |
|---|---|
| Ler Gmail (buscar, ler mensagem, listar rótulos) | funciona |
| Criar rascunho no Gmail | funciona |
| **Criar ou aplicar rótulo no Gmail** | **negado por escopo** |
| Ler Google Agenda | funciona |
| Criar e excluir evento no Google Agenda | funciona |

O erro do Gmail nomeia os escopos ausentes, entre eles
`https://www.googleapis.com/auth/gmail.labels` e
`https://www.googleapis.com/auth/gmail.modify`.

### Como destravar a triagem

Em claude.ai, **Configurações → Conectores**, reconecte o Gmail concedendo
permissão de modificação. Feito isso, peça a criação dos dez rótulos da
taxonomia:

```
TNADV/Intimações        vermelho
TNADV/Prazos            vermelho escuro
TNADV/Audiências        laranja
TNADV/Clientes          azul
TNADV/Financeiro        verde
TNADV/Gestão Pública    roxo
TNADV/Administrativo    cinza
TNADV/Arquivo           cinza claro
TNADV/Triagem/Processado    menta
TNADV/Triagem/Revisar       amarelo
```

Os rótulos herdados da migração IMAP não são tocados.

## Routines criadas

| Nome | ID | Agenda | Estado |
|---|---|---|---|
| TNADV — Dashboard Jurídico Diário | `trig_01UFpA5FJq8zT8uebZ5ikPoX` | dias úteis, 07h00 (10h UTC) | desativada |
| TNADV — Radar de intimações | `trig_01YawDtejxxCbAg1381xqC9j` | dias úteis, 12h e 18h (15h e 21h UTC) | desativada |

Ambas foram criadas **desativadas de propósito**. O motivo: esta organização não
permite vincular conectores a Routines criadas por ferramenta, e o serviço
avisou que as sessões disparadas rodariam **sem acesso a Gmail e Agenda**. Uma
Routine assim dispararia todo dia útil e produziria relatório vazio.

O prompt completo de cada uma já está armazenado. Para colocá-las no ar:

1. Abra a lista de Routines em claude.ai.
2. Em cada uma, vincule os conectores **Gmail** e **Google Agenda**.
3. Ative.

Se a interface não permitir vincular conector a Routine existente, recrie-a por
lá usando o prompt armazenado, que pode ser lido com `list_triggers`.

## Calendários forenses

`core/calendarios/` traz três perfis prontos e um modelo. Nenhum vem com feriado
estadual ou municipal, por decisão de projeto: feriado local não é presumido.

Enquanto `"confirmado": false`, todo cálculo sai com aviso e permanece marcado
como estimativa.

Para confirmar o calendário de um juízo:

1. Copie `MODELO-tribunal-local.json` para, por exemplo, `TRT16.json`.
2. Preencha `locais` com as datas conferidas no portal do tribunal (data magna do
   Estado, feriados municipais da comarca, portarias de suspensão de expediente).
3. Registre em `observacoes` a fonte e a data da consulta.
4. Só então marque `"confirmado": true`.

Refaça isso a cada início de ano judiciário.

## Ordem sugerida de partida

**Semana 1.** Reconectar o Gmail com escrita. Criar os rótulos. Rodar a triagem
nos não lidos dos últimos 30 dias. Confirmar o calendário dos dois ou três juízos
onde está a maior parte do acervo.

**Semana 2.** Popular `data/acervo.json` pela skill `pje-controle-processual` e
pela `datajud`. Gerar a primeira planilha. Conferir à mão os prazos estimados e
marcar `conferido_por_humano`.

**Semana 3.** Vincular conectores às duas Routines e ativá-las. Acompanhar de
perto a primeira semana: comparar cada prazo estimado com o prazo real.

**Depois.** Camada 2 conforme a demanda de cada caso. Essas skills não precisam
de implantação, respondem sob demanda.

## Sinal de que algo está errado

Se a conferência humana divergir da estimativa, **não corrija só a data**.
Divergência indica uma de três causas, e todas se consertam na origem:

1. feriado local ausente do calendário
2. termo inicial mal qualificado
3. regime de contagem trocado

Corrija a causa e registre no commit. Estimativa que erra duas vezes pelo mesmo
motivo é defeito de sistema, não descuido.
