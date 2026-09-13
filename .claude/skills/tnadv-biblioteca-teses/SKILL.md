---
name: tnadv-biblioteca-teses
description: Biblioteca de teses e modelos do escritório Tiago Neves. Indexa peças já produzidas por tema, área, tribunal, tese e resultado, permite busca por similaridade de caso e reaproveitamento auditado de argumentação. Use quando o usuário procurar peça anterior, modelo, tese já usada, precedente próprio do escritório, ou quiser catalogar peças produzidas.
---

# Biblioteca de teses e modelos

O escritório já argumentou bem sobre quase tudo que faz. O problema é achar onde.
Esta skill transforma o histórico de peças em acervo consultável e, mais
importante, em memória de **o que funcionou**.

## Índice

Arquivo `data/biblioteca.json`. Cada registro:

```json
{
  "id": "2024-TRT16-horas-extras-001",
  "titulo": "Contestação — horas extras e intervalo intrajornada",
  "arquivo": "biblioteca/2024/contestacao-horas-extras-001.docx",
  "area": "trabalho",
  "tipo_peca": "contestação",
  "rito": "ordinário",
  "tribunal": "TRT16",
  "orgao": "3ª Vara do Trabalho de São Luís",
  "processo": "0001234-08.2024.5.16.0001",
  "polo_cliente": "passivo",
  "teses": [
    "invalidade do controle de jornada por britânico",
    "compensação de jornada por acordo individual escrito"
  ],
  "fundamentos_centrais": ["CLT, art. 74, § 2º", "Súmula 338 do TST"],
  "resultado": "procedente em parte",
  "resultado_detalhe": "afastadas as horas extras; mantido o intervalo",
  "aprendizado": "A tese de britânico convence quando acompanhada de prova testemunhal; sozinha, não.",
  "cadastrado_em": "2024-11-20"
}
```

O campo `resultado` é o que distingue esta biblioteca de uma pasta de arquivos.
Modelo sem resultado conhecido é apenas texto antigo.

Valores de `resultado`: `procedente`, `procedente em parte`, `improcedente`,
`acordo`, `extinto sem mérito`, `pendente`, `desconhecido`.

## Busca

Ao receber um caso novo, procure por, nesta ordem de peso:

1. mesma tese jurídica
2. mesma área e mesmo tipo de peça
3. mesmo tribunal, e de preferência mesmo órgão julgador
4. mesmo polo processual
5. resultado favorável

Apresente até cinco candidatos assim:

```
[id] — [título]
  Aderência: [alta/média/baixa] — [por quê, em uma linha]
  Resultado: [resultado] — [detalhe]
  Aproveitável: [o que serve neste caso]
  Cuidado: [o que mudou desde então: lei, súmula, entendimento]
```

## Reaproveitamento auditado

Peça antiga não se copia, se atualiza. Antes de reaproveitar qualquer trecho:

1. **Reconfira toda citação.** Súmula pode ter sido cancelada, lei alterada,
   tese de repetitivo superada. Acione `tnadv-pesquisa-jurisprudencial`.
2. **Troque os fatos.** O risco real do reaproveitamento é o fato do caso antigo
   sobreviver no texto novo. Faça varredura por nome, data, valor e número de
   processo remanescentes.
3. **Reavalie a estratégia.** O que funcionou naquele juízo pode não funcionar
   neste.
4. **Registre a origem** na peça nova, em nota interna, para rastreabilidade.

## Catalogação

Ao cadastrar peça nova, extraia automaticamente área, tipo, tribunal, número CNJ
(validado por `core.cnj`) e fundamentos citados. Peça ao advogado apenas o que a
automação não sabe: as teses centrais em linguagem própria, o resultado e o
aprendizado.

Quando um processo da biblioteca receber sentença ou acórdão, **volte e atualize
o resultado**. Biblioteca com resultado desatualizado engana.

## Regras invioláveis

1. Nenhuma citação reaproveitada entra sem nova verificação.
2. Não trate `resultado: desconhecido` como sucesso.
3. Peça de cliente é dado sob sigilo profissional (EOAB, art. 34, VII). A
   biblioteca fica em repositório controlado; ao usar trecho em caso de outro
   cliente, remova todo dado identificador do caso original.
4. Não crie "modelo genérico" a partir de peça real sem antes anonimizá-la.
