---
name: tnadv-dashboard-diario
description: Dashboard Jurídico Diário do escritório Tiago Neves Advocacia. Varre Gmail das últimas 24h, Google Agenda de hoje e amanhã e o acervo processual, classifica movimentações por urgência, desduplica e deixa relatório pronto como rascunho no Gmail. Use quando o usuário pedir "Dashboard", "Bom dia", "Resumo do dia", varredura diária, conferência de intimações, ou quando a Routine agendada disparar.
---

# Dashboard Jurídico Diário

Produz, uma vez por dia útil, um retrato único do que exige atenção. O objetivo
é que o advogado abra um só documento e saiba o que fazer, sem varrer três
sistemas.

## Ordem de execução

Execute nesta ordem. Não pule etapa por parecer vazia: a ausência de movimentação
também é informação relatável.

### 1. Gmail (últimas 24 horas)

Busque com `search_threads` usando `newer_than:1d`. Faça três varreduras
distintas, porque uma só consulta perde material:

- `newer_than:1d` geral na caixa de entrada
- `newer_than:1d (intimação OR intimacao OR "Diário da Justiça" OR DJEN OR PJe OR "prazo" OR audiência)`
- `newer_than:1d is:unread`

Para cada mensagem relevante, extraia: remetente, assunto, número CNJ (use
`core.cnj.extrair` sobre o corpo), órgão, natureza do ato e data mencionada.

### 2. Google Agenda (hoje e amanhã)

`list_events` no calendário `tiagonevesadvo@gmail.com`, janela de hoje 00h até
amanhã 23h59. Separe audiências, reuniões e lembretes de prazo. O calendário
Todoist sincronizado também entra: tarefas com data caem ali.

### 3. Acervo processual

Carregue `data/acervo.json` com `core.acervo.Acervo.carregar()`. Liste:

- prazos em aberto vencendo em até 10 dias
- prazos em aberto **sem conferência humana** (`acervo.nao_conferidos()`)
- processos sem movimentação há mais de 60 dias

### 4. Cruzamento e desduplicação

Um mesmo ato costuma aparecer em três lugares: e-mail de intimação, evento na
agenda e prazo no acervo. Consolide por número CNJ. Quando o mesmo processo
aparecer em fontes diferentes, produza **uma** linha citando todas as fontes.

Se o e-mail indicar movimentação que o acervo não conhece, marque como
`NOVO — não cadastrado` e proponha o cadastro.

## Classificação de urgência

| Cor | Critério |
|---|---|
| 🔴 | Prazo vencendo em até 3 dias, audiência em até 2 dias, decisão com efeito imediato, ou prazo em aberto ainda não conferido que vence em até 7 dias |
| 🟡 | Prazo entre 4 e 10 dias, audiência na semana, diligência com data marcada |
| 🟢 | Movimentação sem prazo, andamento informativo, comunicação de cliente sem urgência |

Use `core.acervo.classificar_urgencia` para a parte automática e ajuste com
julgamento jurídico. Uma decisão que extingue o processo é 🔴 mesmo sem prazo
imediato aparente.

## Formato do relatório

O relatório **não é escrito à mão**. Monte o objeto `Dashboard` e deixe o
renderizador cuidar da apresentação, para que todo dia saia igual:

```python
from datetime import date
from core.dashboard_html import (
    Dashboard, Item, Compromisso, render_html, render_texto, render_pagina,
)

dash = Dashboard(
    data=date.today(),
    resumo="Duas ou três frases sobre o que realmente importa hoje. Sem enrolação.",
    itens=[
        Item(
            urgencia="vermelho",               # vermelho, amarelo ou verde
            titulo="...",
            processo="...", cliente="...", orgao="...",
            o_que_houve="...", providencia="...",
            vencimento_estimado="2026-09-28",  # opcional, AAAA-MM-DD
            alerta="...",                      # destaque, quando houver risco nomeado
            fontes=["e-mail de X", "agenda"],
        ),
    ],
    agenda=[Compromisso(quando="Hoje, 09:00", titulo="...", detalhe="...", alerta="...")],
    pendentes_conferencia=["..."],
    pendencias_sistema=["..."],
    fontes_varredura=["Gmail, últimas 24h, N mensagens", "Google Agenda, DD/MM a DD/MM"],
)
```

O renderizador cuida sozinho da faixa institucional em azul-marinho e dourado,
do placar por urgência, dos cartões com faixa colorida, do selo de vencimento
com a ressalva de conferência, dos blocos de agenda e de pendência, do aviso de
estimativa e do rodapé com o advogado e a OAB. A identidade visual vem de
`core/identidade.py`, a mesma que a planilha usa.

O campo `urgencia` aceita apenas `vermelho`, `amarelo` ou `verde`, e recusa
qualquer outro valor. O placar do topo conta sozinho.

Três saídas, do mesmo objeto:

| Função | Para quê |
|---|---|
| `render_html(dash)` | corpo do e-mail, seguro para cliente de e-mail |
| `render_texto(dash)` | alternativa em texto puro do mesmo e-mail |
| `render_pagina(dash)` | documento HTML autônomo, para arquivo ou impressão |

## Entrega

Crie **rascunho** no Gmail com `create_draft`, destinatário
`tiagoneves.jus@gmail.com`, assunto `Dashboard Jurídico — DD/MM/AAAA`, passando:

- `htmlBody` com a saída de `render_html(dash)`
- `body` com a saída de `render_texto(dash)`, que é a alternativa em texto puro
  e o que aparece na pré-visualização da caixa

Nunca envie automaticamente: o advogado revisa e dispara.

Salve também `render_pagina(dash)` em `saida/dashboard-AAAA-MM-DD.html`, que abre
no navegador e imprime limpo.

Se a execução veio de Routine agendada, informe ao final quantos itens de cada
cor foram encontrados, para que a notificação seja útil sem abrir o rascunho.

## Regras invioláveis

1. **Prazo exibido é estimativa.** Toda data vem acompanhada de "CONFERIR NO
   SISTEMA". Nunca escreva que um prazo "vence em" sem essa ressalva.
2. **Não invente movimentação.** Se a varredura não achou nada em uma fonte,
   escreva que não achou. Dashboard vazio é resultado legítimo.
3. **Não classifique por palavra-chave apenas.** Leia o teor. "Intimação" no
   assunto de newsletter jurídica não é intimação.
4. **Não apague nem arquive nada** durante a varredura. O dashboard só lê.
5. Ao encontrar número CNJ, valide com `core.cnj.validar`. Número com dígito
   verificador inválido entra no relatório como `[NÚMERO SUSPEITO]`, para
   conferência de transcrição.
