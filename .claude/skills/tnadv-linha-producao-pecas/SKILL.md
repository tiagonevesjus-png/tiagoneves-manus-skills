---
name: tnadv-linha-producao-pecas
description: Linha de produção de peças processuais do escritório Tiago Neves, do fato bruto ao docx pronto para protocolo. Encadeia triagem, checklist de dados, diagnóstico de força e vulnerabilidade, estratégia, redação, formatação na identidade visual do escritório e auditoria forense crítica. Use para elaborar petição inicial, contestação, réplica, manifestação, recurso, embargos ou parecer.
---

# Linha de produção de peças

Encadeia em fluxo único o que hoje é acionado separadamente. Cada etapa tem um
portão: não se avança sem cumprir o anterior.

## Etapa 1 — Triagem

Identifique e registre por escrito, antes de qualquer redação:

- tipo de peça e rito
- área do direito e competência
- polo do cliente e parte contrária
- juízo e número CNJ, se já houver
- prazo e sua origem (com o termo inicial qualificado)
- objetivo concreto: o que se quer que o juiz faça

Se a peça é recursal, identifique também a decisão recorrida, sua data de
publicação e o cabimento.

## Etapa 2 — Checklist de dados

Levante o que é indispensável e o que falta. Formato:

```
DADOS CONFIRMADOS
- [campo]: [valor] (fonte: [documento/página])

DADOS PENDENTES
- [DADO PENDENTE] [campo] — necessário para [finalidade]
```

**Portão:** se faltar dado que compromete tese ou pedido, pergunte ao advogado
antes de redigir. Não preencha lacuna com suposição. Dado ausente vira
`[DADO PENDENTE]` no corpo da peça, visível, nunca invisível.

## Etapa 3 — Diagnóstico

Mapeie honestamente os dois lados:

**Força:** fatos incontroversos, prova documental robusta, norma expressa,
precedente vinculante favorável, presunções em favor do cliente.

**Vulnerabilidade:** fato controvertido sem prova, ônus probatório desfavorável,
prescrição ou decadência, precedente contrário, questão processual (legitimidade,
interesse, competência, litispendência), risco de sucumbência.

Escreva a vulnerabilidade com franqueza. Diagnóstico que só enxerga força não
serve para decidir estratégia.

## Etapa 4 — Estratégia

Defina, e justifique em uma linha cada:

- tese principal e teses subsidiárias, na ordem
- o que antecipar da defesa adversária e como neutralizar
- preliminares que valem levantar (e as que não valem, porque preliminar fraca
  desgasta credibilidade)
- pedidos, principal e sucessivos
- tutela de urgência ou evidência, se cabível, com os requisitos endereçados um
  a um
- prova a requerer

## Etapa 5 — Fundamentação verificada

Acione `tnadv-pesquisa-jurisprudencial` para legislação, súmulas e precedentes.
Regra: **nada entra na peça sem verificação**. Onde não houver precedente,
escreva a fundamentação legal e doutrinária, e registre a ausência ao advogado.
Nunca compense a falta com citação plausível.

## Etapa 6 — Redação

Estrutura padrão, na ordem, quando aplicável:

1. Endereçamento
2. Qualificação das partes, sem repetições
3. Síntese fática
4. Preliminares
5. Mérito
6. Fundamentação legal
7. Provas
8. Pedidos, numerados
9. Requerimentos finais

Registro: técnico, direto, sem grandiloquência. Frases curtas. Vírgulas no lugar
de travessões. Sem conectivo ornamental em início de parágrafo. O texto deve
soar escrito por advogado experiente, não por gerador.

Nos recursos, duas peças separadas: petição de interposição ao juízo *a quo* e
razões recursais ao juízo *ad quem*.

Em Recurso de Revista, cumpra o art. 896, § 1º-A, da CLT: transcrição literal do
trecho do acórdão, demonstração analítica da violação, impugnação específica dos
fundamentos. Some prequestionamento (Súmula 297 do TST) e transcendência
(art. 896-A). Divergência jurisprudencial apenas com julgados de **outro** TRT
ou da SDI do TST.

## Etapa 7 — Formatação

Aplique a skill `tiago-neves-peticiones-formato`: papel timbrado, azul-marinho e
dourado, Garamond 12, espaçamento 1,5, justificado inclusive no endereçamento e
na numeração do processo, títulos progressivos, rodapé com contatos.

Saída em `.docx` pela skill `docx`.

## Etapa 8 — Auditoria

**Portão obrigatório.** Acione `auditor-forense-alto-rigor` sobre a minuta
pronta. A auditoria procura:

- citação não verificada ou mal transcrita
- fato afirmado sem lastro no documento
- pedido incoerente com a causa de pedir
- preliminar sem requisito
- contradição interna
- vício processual (tempestividade, preparo, representação, dialeticidade)
- lacuna deixada por `[DADO PENDENTE]` que ficou sem tratamento

Se a auditoria apontar falha material, volte à etapa correspondente. Não
entregue peça que não passou pela auditoria.

## Etapa 9 — Entrega

Entregue três coisas:

1. o `.docx` formatado
2. o relatório de auditoria, com o que foi corrigido
3. a lista de `[DADO PENDENTE]` remanescentes e o checklist de protocolo

**O protocolo é ato do advogado.** A linha de produção entrega a peça pronta;
quem assina e peticiona com certificado digital é Tiago Luiz Rodrigues Neves,
OAB/MA 10.042.

## Regras invioláveis

1. Zero alucinação: lei, súmula e precedente só entram verificados.
2. Transcrição de texto legal é literal, sem alteração de palavra.
3. Lacuna vira `[DADO PENDENTE]` visível, jamais invenção.
4. Nenhuma peça pula a auditoria da etapa 8.
5. Nenhum protocolo automático.
