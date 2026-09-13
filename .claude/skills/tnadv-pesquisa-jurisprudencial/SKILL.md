---
name: tnadv-pesquisa-jurisprudencial
description: Motor de pesquisa jurisprudencial e legislativa verificada para o direito brasileiro. Busca em fontes oficiais, transcreve ementa e texto legal literalmente, valida o link e monta o bloco de fundamentação com citação completa. Declara expressamente quando não localiza precedente, sem nunca substituir a ausência por citação plausível. Use sempre que for citar lei, súmula, precedente, tema repetitivo ou repercussão geral.
---

# Pesquisa jurisprudencial verificada

Esta é a skill que impede o erro mais grave que uma automação jurídica pode
cometer. A regra é única e não comporta exceção: **o que não foi verificado na
fonte oficial não entra na peça.**

## Fontes oficiais

### Legislação

| Fonte | Endereço | Acesso automatizado |
|---|---|---|
| Planalto (texto compilado) | `planalto.gov.br/ccivil_03/` | funciona (envie *user-agent* de navegador) |
| LexML | `lexml.gov.br` | funciona |

O Planalto exibe, na mesma página, redações revogadas ao lado da vigente. Ao
transcrever, confirme qual é a redação atual pela nota "(Redação dada pela
Lei nº ...)" mais recente. O art. 775 da CLT é o exemplo canônico: a página
mostra três redações, e só a da Lei 13.467/2017 vale.

### Jurisprudência

| Tribunal | Endereço |
|---|---|
| STF | `jurisprudencia.stf.jus.br` |
| STJ | `scon.stj.jus.br/SCON/` |
| TST | `jurisprudencia.tst.jus.br` |
| TRTs, TJs | portal de jurisprudência do respectivo tribunal |
| DJEN / Comunica | `comunica.pje.jus.br` |

Nem todos aceitam acesso automatizado: STF, STJ e o Comunica costumam bloquear
requisição de robô com 403 ou tempo esgotado. Quando isso ocorrer, **não invente
substituto**. Duas saídas legítimas:

1. buscar o mesmo julgado em outra fonte oficial (o inteiro teor costuma estar
   no portal do próprio tribunal ou no LexML);
2. entregar ao advogado a consulta pronta, com os termos de busca e o endereço,
   para conferência manual, e marcar o trecho da peça como
   `[PRECEDENTE A CONFERIR]`.

Bloqueio técnico não autoriza citação de memória.

## Protocolo de citação

### Legislação

Ao citar, transcreva literalmente e comente em seguida. Nunca parafraseie dentro
das aspas.

```
Dispõe o art. 219 do CPC:

    "Na contagem de prazo em dias, estabelecido por lei ou pelo juiz,
    computar-se-ão somente os dias úteis."

[comentário do advogado sobre a aplicação ao caso]
```

Indique o diploma completo na primeira menção (Lei 13.105/2015 — CPC), depois
use a forma abreviada.

### Jurisprudência

Todo precedente citado traz, obrigatoriamente:

- tribunal
- número do processo
- órgão julgador (turma, seção, plenário)
- relator
- data de julgamento e, quando houver, data de publicação
- ementa transcrita literalmente, ou o trecho pertinente entre aspas

```
(TST, RR-XXXXXX-XX.XXXX.5.XX.XXXX, 2ª Turma, Rel. Min. [nome],
julgado em DD/MM/AAAA, DEJT DD/MM/AAAA)
```

Se qualquer um desses elementos faltar, o precedente **não está verificado**.
Marque `[PRECEDENTE A CONFERIR]` e informe o que falta.

### Quando não localizar

Escreva, literalmente:

> Não localizei jurisprudência específica sobre este ponto.

E siga com a fundamentação legal e doutrinária disponível. Ausência de
precedente é informação útil ao advogado: às vezes indica tese nova, que é
justamente o que sustenta a transcendência jurídica no art. 896-A da CLT.

## Cuidados por tipo de precedente

**Súmula.** Confirme se está vigente. Súmula cancelada ou convertida continua
circulando em repositório desatualizado.

**Orientação Jurisprudencial.** Verifique se foi convertida em súmula.

**Tema repetitivo e repercussão geral.** Confirme número do tema, a tese fixada
em sua redação exata, e se houve modulação de efeitos. Tese de repetitivo citada
pela ementa do acórdão paradigma, e não pela tese fixada, é erro comum.

**Divergência em Recurso de Revista.** Só serve julgado de **outro** TRT ou da
SDI do TST. Aresto do mesmo TRT do acórdão recorrido não presta ao confronto.

**Precedente vinculante.** Identifique-o como tal (art. 927 do CPC) e explique
por que o caso se ajusta, ou proponha distinção fundamentada.

## Bloco de saída

```
FUNDAMENTAÇÃO VERIFICADA — [tema]

LEGISLAÇÃO
[transcrição literal + fonte consultada + data da consulta]

SÚMULAS E ENUNCIADOS
[texto literal + situação: vigente/cancelada/convertida]

PRECEDENTES
[citação completa + trecho literal + link]

NÃO LOCALIZADO
[pontos sobre os quais não se achou precedente, declarados expressamente]

A CONFERIR MANUALMENTE
[itens cuja fonte bloqueou acesso automatizado, com os termos de busca]
```

Registre sempre a **data da consulta**: jurisprudência muda, e a peça precisa
poder ser auditada depois.

## Regras invioláveis

1. Nunca invente julgado, ementa, número de processo, relator ou data.
2. Nunca altere palavra de texto legal ou de ementa ao transcrever.
3. Nunca atribua decisão a tribunal sem ter visto a fonte.
4. Nunca preencha ausência de precedente com citação genérica.
5. Bloqueio de acesso não vira citação de memória.
6. `Midpage` e demais bases de direito estrangeiro não servem ao direito
   brasileiro. Não as use como fonte para peça nacional.
