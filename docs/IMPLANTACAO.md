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
| Triagem do Gmail | **Funcionando, 100% nativa** | importar os filtros; aplicar cores à mão |
| Sete skills da camada 2 | **Funcionando sob demanda** | — |

## Permissões verificadas

Testadas de fato nesta implantação, não presumidas:

| Capacidade | Resultado |
|---|---|
| Ler Gmail (buscar, ler mensagem, listar rótulos) | funciona (conector Gmail) |
| Criar rascunho no Gmail | funciona (conector Gmail) |
| **Criar ou aplicar rótulo pelo conector Gmail** | **negado por escopo, sem remédio** |
| Rotular por filtro nativo do Gmail | funciona, sem dependência externa |
| Ler Google Agenda | funciona |
| Criar e excluir evento no Google Agenda | funciona |

### O escopo do conector Gmail não é ajustável

O conector Gmail da Anthropic se descreve como "Draft replies, summarize threads,
& search your inbox", e é exatamente isso que ele faz. A chamada de criação de
rótulo devolve `Insufficient scope`, exigindo `gmail.labels` ou `gmail.modify`,
que esse conector não solicita. Reautorizar o Google Workspace não muda nada:
o conector nunca pede esses escopos.

Verificado três vezes, inclusive depois de o advogado reautorizar todo o
Workspace. Não é problema de configuração da conta, é limite do aplicativo.

### A solução adotada: filtro nativo, sem terceiros

O trabalho foi partido em duas metades:

- **Filtro nativo do Gmail** para o que é determinístico (remetente de tribunal,
  domínio `.jus.br`, assunto com marcador, bancos, ferramentas). Roda no servidor
  do Google, em toda mensagem que chega, sem sessão aberta e sem intermediário.
- **Skill de triagem** para o que exige julgamento. Produz relatório em rascunho,
  não rótulo.

Chegou-se a usar o Zapier como via de escrita, e ele funcionou. Foi retirado a
pedido do advogado, em favor da solução nativa. A decisão se sustenta por si:
um operador a menos no caminho de dado protegido por sigilo profissional é ganho,
não perda.

```bash
python3 tools/gerar_filtros_gmail.py --saida "saida/filtros-tnadv-gmail.xml"
```

Importar em Gmail, Configurações, Filtros e endereços bloqueados, Importar
filtros. Detalhes em
`.claude/skills/tnadv-triagem-gmail/references/filtros-nativos.md`.

`core/filtros_gmail.py` recusa a montagem de qualquer regra que arquive, exclua,
marque como lida ou encaminhe, e um teste trava essa recusa.

### O que se perde sem via de escrita programática

Duas coisas, ambas contornáveis:

1. **Rotulação retroativa em lote pela automação.** O passivo de mais de seis mil
   não lidos não pode ser rotulado por chamada de ferramenta. Contorno: a skill
   entrega as buscas prontas, e a rotulação em massa se faz pela interface do
   Gmail, que aliás é mais rápida para volumes grandes.
2. **Rótulo aplicado por julgamento, na hora.** Casos ambíguos saem no relatório
   com o rótulo sugerido e o link direto, para aplicação em dois cliques.

Todo padrão ambíguo que se repetir deve virar regra de filtro. É assim que o
sistema reduz o próprio trabalho manual com o tempo.

### A caixa é única e tem três endereços

- `tiagonevesadvo@gmail.com` — conta Google subjacente, também usada pela Agenda
  e pelo Zapier
- `tiagoneves.jus@gmail.com` — endereço de envio, também recebe na mesma caixa
- `advtneves@gmail.com` — destinatário dos relatórios diários

Antes de qualquer automação nova sobre e-mail, confirme em qual desses endereços
ela vai operar.

### Rótulos criados

Onze, todos verificados na caixa:

```
TNADV/Intimações   TNADV/Prazos       TNADV/Audiências   TNADV/Clientes
TNADV/Financeiro   TNADV/Gestão Pública   TNADV/Administrativo
TNADV/Pessoal      TNADV/Arquivo
TNADV/Triagem/Processado   TNADV/Triagem/Revisar
```

`TNADV/Pessoal` não estava no desenho original. Entrou porque a primeira
varredura mostrou que a maior parte do não lido recente é notificação bancária,
alerta de conta Google e marketing. Sem essa categoria, tudo isso acabaria em
Administrativo e a triagem perderia utilidade.

A paleta de cores precisa ser aplicada uma vez, à mão, na interface do Gmail.
Os rótulos herdados da migração IMAP não foram tocados.

### Primeira leva de triagem

Doze mensagens classificadas e rotuladas em 12/09/2026, ainda pela via
programática, antes da migração para filtro nativo:

- sete PUSH do PJe/TRT16 → `TNADV/Intimações` + `Processado`
- cinco confirmações de audiência do cliente Fixtell Telecom →
  `TNADV/Audiências` + `TNADV/Clientes` + `Processado`

Os rótulos aplicados permanecem. Daqui em diante, mensagens do mesmo tipo são
capturadas pelo filtro nativo.

Treze números CNJ extraídos foram validados pelo dígito verificador, todos
íntegros. O não lido foi preservado nas mensagens de audiência, como a regra
exige.

Fica registrada uma constatação importante: os PUSH do TRT16 **avisam**
movimentação, não intimam. Recebem o rótulo de comunicação oficial, mas nunca
devem acionar o radar de prazos.

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

### Confirmados

Quatro calendários já foram levantados nas fontes oficiais:

| Arquivo | Fonte | Cobertura |
|---|---|---|
| `TRT16-sao-luis.json` | iCal institucional do TRT16 | 2026 |
| `TRT16-santa-ines.json` | iCal institucional do TRT16 | 2026 |
| `TJMA-sao-luis.json` | Calendário Forense 2026 do TJMA | 2026 |
| `TJCE-fortaleza.json` | Portarias TJCE nº 2924/2025 e nº 727/2026 | 2026 e janeiro de 2027 |

O TRT16 publica o ano inteiro em iCal, com abrangência por município.
`tools/importar_calendario_trt16.py` lê essa fonte e gera o arquivo:

```bash
python3 tools/importar_calendario_trt16.py --ano 2027 --municipio "São Luís"
```

O TJMA publica em imagens mensais, então a transcrição é manual.

### Por que isso não podia ser presumido

O levantamento provou o ponto. Em 2026 os tribunais **divergem** entre si, por
transferência de data e por feriado próprio:

| Feriado | TRT16 | TJMA | TJCE |
|---|---|---|---|
| Adesão do Maranhão à Independência | 27/07 | 28/07 | trabalha |
| Dia do Advogado | trabalha | 11/08 | trabalha |
| Dia do Servidor Público | 30/10 | 28/10 | 28/10 |
| Quarta-feira da Semana Santa | para | para | trabalha |
| Data Magna do Ceará (25/03) | trabalha | trabalha | para |
| Aniversário de Fortaleza (13/04) | trabalha | trabalha | para |

Nenhum dos três trata essas datas do mesmo modo, e há teste travando cada uma.

E dentro do próprio TRT16, comarcas divergem: Santa Inês não trabalha em 21/01,
dia da Padroeira, quando São Luís trabalha; São Luís não trabalha em 08/09,
fundação da cidade, quando Santa Inês trabalha.

### Dia parado não é a mesma coisa que dia de expediente reduzido

O TJCE trouxe um caso que o motor passou a modelar: em 18/02/2026, Quarta-feira
de Cinzas, há ponto facultativo até as 14h e expediente normal a partir daí.
Não é dia parado.

O art. 224, § 1º, do CPC trata os dois de formas diferentes. Dia de expediente
reduzido **conta** como dia útil no meio do prazo, e ao mesmo tempo **protrai**
o dia do começo e o do vencimento. O campo `expediente_reduzido` do calendário
existe para isso, e o motor emite aviso citando o dispositivo quando prorroga.

Um calendário usado no lugar do outro produz prazo errado. Por isso cada
processo do acervo aponta para o calendário do seu juízo, e não para um genérico.

### Ainda pendentes

- **Paço do Lumiar** (TJMA). Há audiência designada nessa comarca em 01/10/2026 e
  o calendário não foi confirmado. Fonte: calendário de feriados das comarcas
  publicado pelo TJMA.
- **2027**, salvo o TJCE, que já vem coberto até 06/01/2027 por alcance da
  própria portaria. O motor avisa quando um prazo termina em ano sem feriado
  local cadastrado, mas o aviso não substitui o cadastro. Regenere no início do
  ano judiciário.

### Para acrescentar um juízo novo

1. Justiça do Trabalho da 16ª: rode o importador com `--municipio`.
2. Outros: copie `MODELO-tribunal-local.json`, preencha `locais` com datas
   conferidas, registre a fonte em `_fonte` e a data em `_consultado_em`, e só
   então marque `"confirmado": true`.

`tests/test_integridade_calendarios.py` roda sobre todos os arquivos do
diretório e recusa calendário com data malformada, com o mesmo dia marcado como
parado e reduzido ao mesmo tempo, ou confirmado sem declarar a fonte.

## Integração contínua

`.github/workflows/testes.yml` roda os testes a cada push e em todo pull
request, em Python 3.11 e 3.12, e confere que os filtros do Gmail continuam
sendo gerados como XML válido. Antes disso, os testes só rodavam quando alguém
se lembrava de executá-los.

## Ordem sugerida de partida

**Semana 1.** Importar `saida/filtros-tnadv-gmail.xml` no Gmail. Aplicar as cores
dos rótulos à mão. Rodar as buscas em massa para arrumar o passivo. Confirmar o
calendário do TRT16 e do TJMA, que concentram o acervo visível.

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
