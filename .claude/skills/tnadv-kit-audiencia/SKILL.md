---
name: tnadv-kit-audiencia
description: Dossiê de preparação para audiência. Monta síntese do caso, pontos controvertidos, roteiro de perguntas por testemunha, mapa de contradições nos depoimentos e documentos, teses prováveis da parte contrária e cenários de acordo. Use quando houver audiência designada, pedido de preparação para audiência, instrução, oitiva ou sustentação oral.
---

# Kit de audiência

Produz o dossiê que o advogado leva para a sala. Objetivo: entrar sabendo o que
perguntar, o que evitar e onde o adversário é frágil.

## Entrada

Autos ou peças principais, documentos, depoimentos já colhidos (se houver),
tipo de audiência (una, instrução, conciliação, justificação) e o objetivo do
cliente.

## Estrutura do dossiê

### 1. Cabeçalho operacional

Processo, órgão, data e hora, modalidade (presencial ou telepresencial, com o
link), partes, preposto, testemunhas arroladas de cada lado, e o que **precisa
sair da audiência**.

### 2. Síntese do caso em uma página

Fatos, pedidos, defesa e situação processual atual. Uma página, não mais: o
dossiê é para consulta rápida, não para releitura dos autos.

### 3. Pontos controvertidos

O ponto central de toda audiência de instrução. Para cada um:

```
CONTROVÉRSIA: [o que exatamente está em disputa]
Nossa versão: [...]
Versão adversa: [...]
Ônus da prova: [de quem, com base legal — CPC, art. 373; CLT, art. 818]
Prova já produzida: [documento, com localização nos autos]
O que falta provar: [...]
Como provar em audiência: [testemunha X sobre o fato Y]
```

### 4. Roteiro de perguntas

Por testemunha, separando as **nossas** das **da parte contrária**.

Para testemunha própria: perguntas abertas, que deixem a pessoa narrar. Ordem
cronológica. Cada pergunta deve ter finalidade probatória declarada.

```
P: [pergunta]
   Objetivo: comprovar [fato controvertido nº]
   Resposta esperada: [...]
   Risco: [o que pode dar errado e como recuperar]
```

Para testemunha adversa: perguntas fechadas, que admitam sim ou não, encadeadas
para fechar saídas. Nunca faça pergunta cuja resposta você não conhece nem pode
prever, quando o risco for material.

Marque as **perguntas proibidas**: as que abrem porta para fato prejudicial, e
as indutivas que o juízo indeferirá.

### 5. Mapa de contradições

Confronte cada afirmação com as demais fontes:

| Afirmação | Onde consta | Contradiz | Como explorar |
|---|---|---|---|
| "Nunca fiz hora extra" | Depoimento pessoal, fl. 210 | Cartão de ponto, DOC-05, e e-mail de 22h, DOC-11 | Confrontar com o documento antes de a testemunha se comprometer |

Contradição vale menos se exposta cedo. Planeje o momento.

### 6. Teses prováveis da parte contrária

Antecipe o que o outro lado vai sustentar e prepare a réplica de cada uma. Traga
a fundamentação já verificada, pela skill `tnadv-pesquisa-jurisprudencial`.

### 7. Cenário de acordo

Faixa aceitável, ponto de partida, ponto de recuo, e o que **não** é negociável.
Registre os riscos de não acordar: prognóstico realista de resultado, custo,
tempo, sucumbência.

### 8. Checklist material

```
[ ] Procuração e substabelecimento em ordem
[ ] Carta de preposição, quando for o caso
[ ] Documentos originais que possam ser exigidos
[ ] Rol de testemunhas protocolado no prazo
[ ] Testemunhas cientificadas de data, hora e local
[ ] Link e teste de conexão (audiência telepresencial)
[ ] Peças e documentos acessíveis durante a sessão
[ ] Contatos do cliente e das testemunhas
```

## Regras invioláveis

1. **Não invente depoimento nem antecipe resposta como se fosse fato.** Resposta
   esperada é hipótese de trabalho, sinalizada como tal.
2. **Não invente contradição.** Toda contradição apontada indica a fonte exata,
   com localização nos autos.
3. Toda fundamentação passa pela pesquisa verificada.
4. O que faltar vira `[DADO PENDENTE]`, nunca preenchimento por suposição.
5. Orientação a testemunha se limita ao lícito: esclarecer o rito, o dever de
   dizer a verdade e o que se espera do depoimento. Sugerir conteúdo de resposta
   é conduta vedada, e esta skill não a produz.
