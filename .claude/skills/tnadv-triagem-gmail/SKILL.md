---
name: tnadv-triagem-gmail
description: Triagem, classificação e reorganização da caixa de e-mail jurídica do escritório Tiago Neves. Aplica a taxonomia TNADV de rótulos, separa intimação de propaganda, identifica processos e providências, e faz varredura de recuperação no acervo de mensagens não lidas. Use quando o usuário pedir para organizar, classificar, triar ou limpar o Gmail, ou quando a Routine de triagem disparar.
---

# Triagem e reorganização do Gmail

A caixa do escritório acumulou milhares de mensagens não lidas e uma taxonomia
herdada de migração IMAP, com pastas do tipo `[Gmail]/Lixeira/PENDENTES` que já
não significam nada. Esta skill separa o que exige providência do que virou
histórico, sem apagar nada.

## Arquitetura: filtro nativo faz o mecânico, a triagem faz o julgamento

O conector Gmail é somente leitura e rascunho. Ele não aplica rótulo, e não há
como fazê-lo aplicar. Em vez de contornar isso com integração de terceiro, o
trabalho foi partido em duas metades, cada uma no lugar onde funciona melhor:

**Os filtros nativos do Gmail** cuidam do que é determinístico: remetente de
tribunal, domínio `.jus.br`, assunto com marcador inequívoco, bancos, ferramentas.
Rodam no servidor do Google, em toda mensagem que chega, sem sessão aberta e sem
dependência externa. Gerados por `tools/gerar_filtros_gmail.py` e importados uma
única vez em Gmail, Configurações, Filtros e endereços bloqueados, Importar
filtros. Ver `references/filtros-nativos.md`.

**Esta skill** cuida do que exige leitura e julgamento, e que filtro nenhum
resolve: distinguir intimação de aviso de movimentação, cliente de fornecedor,
conta do escritório de conta pessoal, urgência real de ruído. A saída é
**relatório**, entregue como rascunho no Gmail, não rótulo aplicado.

Quando a classificação por julgamento indicar rótulo que o filtro não pegou, o
relatório diz qual mensagem e qual rótulo, e você aplica com dois cliques, ou
me pede uma regra nova de filtro para que aquele caso nunca mais precise de
julgamento.

## Taxonomia TNADV

Rótulos oficiais, criados e verificados na implantação:

| Rótulo | Uso |
|---|---|
| `TNADV/Intimações` | Comunicações de tribunal: DJe, DJEN, PJe, portais, oficial de justiça |
| `TNADV/Prazos` | Mensagens de que decorre providência com data |
| `TNADV/Audiências` | Designação, remarcação, links de sessão telepresencial |
| `TNADV/Clientes` | Comunicação direta com cliente |
| `TNADV/Financeiro` | Honorários, RPV, precatório, alvará, cobrança, nota fiscal, contas do escritório |
| `TNADV/Gestão Pública` | Órgãos públicos assessorados, processos administrativos, ofícios |
| `TNADV/Administrativo` | OAB, certidões, fornecedores, ferramentas, rotina do escritório |
| `TNADV/Pessoal` | Assunto pessoal do advogado, sem relação com o escritório |
| `TNADV/Arquivo` | Encerrado, apenas histórico |
| `TNADV/Triagem/Processado` | Já passou pela triagem automática |
| `TNADV/Triagem/Revisar` | Automação não teve confiança suficiente; exige olho humano |

`TNADV/Pessoal` existe porque a caixa é mista. A primeira varredura mostrou que
a maior parte do não lido recente é notificação bancária, alerta de conta Google
e marketing, não matéria jurídica. Sem essa categoria, tudo isso acabaria
empilhado em Administrativo e a triagem perderia utilidade.

Conta bancária em nome de "Guimarães e Neves Advogados" é `TNADV/Financeiro`.
Conta em nome pessoal é `TNADV/Pessoal`. Quando o nome não distinguir, aplique
`TNADV/Financeiro` e mande para `Revisar`.

Os rótulos antigos herdados do IMAP não são apagados. Eles permanecem como
histórico; a taxonomia nova convive com eles.

## Como classificar

Leia o teor, não só o assunto. A ordem de decisão é esta:

1. **É comunicação oficial de tribunal?** Remetente institucional, número CNJ
   válido no corpo, referência a ato processual. Vai para `TNADV/Intimações`.
   Se dela decorre providência com data, receba **também** `TNADV/Prazos` e
   acione a skill `tnadv-radar-intimacoes`.

2. **É audiência?** Designação, redesignação, link de sessão. `TNADV/Audiências`,
   e verifique se já existe evento correspondente na agenda.

3. **É cliente falando?** Endereço pessoal, assunto sobre caso próprio.
   `TNADV/Clientes`.

4. **Tem conteúdo financeiro?** `TNADV/Financeiro`.

5. **É órgão público assessorado?** `TNADV/Gestão Pública`.

6. **Sobrou?** `TNADV/Administrativo`, ou `TNADV/Arquivo` se claramente histórico.

Ao final, aplique `TNADV/Triagem/Processado`. Quando a classificação ficar
abaixo de confiança razoável, aplique `TNADV/Triagem/Revisar` **em vez de**
chutar uma categoria.

### Armadilhas conhecidas

- Newsletter jurídica e boletim de escritório usam as mesmas palavras de uma
  intimação. Verifique remetente e presença de número CNJ válido.
- **O PUSH do PJe não é intimação.** As mensagens de `nao-responda@trt16.jus.br`
  com assunto `[TRT16] [PUSH] Atualizações de Informações Processuais` avisam que
  houve movimentação. Recebem `TNADV/Intimações` por serem comunicação oficial de
  tribunal, mas **não deflagram prazo**: o termo inicial vem do DJe ou do portal.
  Nunca acione o radar de prazos a partir de um PUSH.
- Convite de audiência aceito por cliente (resposta de calendário com "Aceito:"
  no assunto) traz o número do processo, a data e o juízo no próprio título.
  Vale `TNADV/Audiências` e `TNADV/Clientes`, e é boa fonte para conferir a
  agenda.
- Uma thread pode mudar de natureza. Classifique pela mensagem mais recente.

## Varredura de recuperação

Para o passivo de mensagens não lidas, trabalhe em lotes e do mais recente para
o mais antigo, porque o valor decai com o tempo:

```
is:unread newer_than:30d
is:unread older_than:30d newer_than:90d
is:unread older_than:90d newer_than:1y
is:unread older_than:1y
```

Em cada lote: classifique e produza o relatório. Mensagens com mais de um ano e
sem número CNJ são candidatas a `TNADV/Arquivo`.

Processe no máximo 100 mensagens por execução e informe onde parou, para que a
execução seguinte continue do ponto certo.

Atenção ao alcance do filtro nativo: ele age sobre o que **chega**, não sobre o
passivo já na caixa. Para o acervo antigo, o Gmail permite selecionar o
resultado de uma busca e aplicar o rótulo em massa, pela própria interface. O
relatório desta skill entrega as buscas prontas para isso, no formato:

```
Busca: from:(trt16.jus.br) older_than:1y
Rótulo a aplicar: TNADV/Intimações
Mensagens estimadas: [n]
```

Assim a varredura do passivo vira uma sequência de operações em massa na
interface do Gmail, não milhares de chamadas de automação.

## Regras invioláveis

1. **Nunca apague, mova para lixeira ou marque como spam.** Exclusão é decisão do
   advogado, tomada mensagem a mensagem.
2. **Nunca marque como lida** uma mensagem classificada como `TNADV/Intimações`
   ou `TNADV/Prazos`. O não lido é a última barreira contra perda de prazo.
3. **Nunca responda e-mail** a partir da triagem.
4. Nenhuma regra de filtro gerada aqui arquiva, marca como lida, exclui ou
   encaminha. Filtro TNADV só rotula, e `core/filtros_gmail.py` recusa a
   montagem de qualquer regra que viole isso.
5. Ao encontrar número CNJ, valide com `core.cnj.validar` antes de usar.
6. Em caso de dúvida entre duas categorias, indique as duas e marque para
   `Revisar`. Erro de classificação silencioso é pior que ruído.

## Relatório de execução

Entregue como rascunho no Gmail, com:

```
TRIAGEM TNADV — [período examinado]

RESUMO
Total examinado: [n] | Já rotulado por filtro nativo: [n] | Requer sua ação: [n]

CLASSIFICAÇÃO POR JULGAMENTO
[Rótulo sugerido] — [assunto], de [remetente], [data]
   Por quê: [uma linha]
   Link: [link direto da mensagem]

REVISAR
[casos em que a automação não teve confiança, com as duas leituras possíveis]

OPERAÇÕES EM MASSA SUGERIDAS
Busca: [query Gmail] → Rótulo: [rótulo] → [n] mensagens

REGRAS DE FILTRO A ACRESCENTAR
[padrões que se repetiram e merecem virar filtro nativo, para não voltarem
a exigir julgamento]

NÚMEROS CNJ NOVOS
[detectados e validados, ausentes do acervo]

PARADA
[onde a varredura parou, para a próxima execução continuar]
```

A seção de regras a acrescentar é o que faz o sistema melhorar com o uso: todo
padrão que se repete deve migrar do julgamento para o filtro.
