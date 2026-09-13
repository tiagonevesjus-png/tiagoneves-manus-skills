---
name: tnadv-radar-intimacoes
description: Radar de intimações ligado ao Google Agenda. Identifica comunicações de tribunal, extrai número CNJ, órgão e natureza do ato, calcula o prazo estimado com o motor legal auditado, cria evento na agenda com checklist e registra tudo no acervo processual. Use quando chegar intimação, quando o usuário pedir para cadastrar prazo ou lançar prazo na agenda, ou quando a Routine do radar disparar.
---

# Radar de intimações

Transforma comunicação de tribunal em prazo rastreado. É a automação de maior
risco do escritório, por isso opera sob a premissa de que **toda data produzida
aqui é estimativa** e nenhuma dispensa conferência no sistema do tribunal.

## Fluxo

### 1. Detecção

Varra o Gmail por comunicações oficiais (a skill `tnadv-triagem-gmail` já rotula
`TNADV/Intimações`). Para cada uma, extraia:

- número CNJ, validado com `core.cnj.validar`
- órgão julgador e vara
- natureza do ato (sentença, despacho, decisão interlocutória, acórdão, edital)
- **qual foi o meio da comunicação**, que determina o termo inicial
- a data do evento correspondente ao meio

Se qualquer um desses campos faltar, registre `[DADO PENDENTE]` e leve o item
para revisão humana. Não estime prazo com termo inicial incerto.

### 2. Qualificação do termo inicial

Esta é a etapa que erra com mais frequência. Mapeie o meio ao inciso do art. 231
do CPC:

| Situação no e-mail | `TermoInicial` | Data que você precisa |
|---|---|---|
| Publicação no DJe / DJEN | `DJE_DISPONIBILIZACAO` | data da **disponibilização** |
| "Publicado em DD/MM" já como publicação | `PUBLICACAO` | data da publicação |
| Intimação em portal, com consulta feita | `CONSULTA_ELETRONICA` | data da consulta |
| Intimação em portal, sem consulta | `DECURSO_PRAZO_CONSULTA` | data do **envio** |
| Carta com AR | `JUNTADA_AR` | data da juntada do AR |
| Oficial de justiça | `JUNTADA_MANDADO` | data da juntada do mandado |
| Carga dos autos | `CARGA` | data da carga |

Atenção a duas confusões clássicas:

- **Disponibilização não é publicação.** A publicação é o primeiro dia útil
  seguinte à disponibilização (Lei 11.419/2006, art. 4º, § 3º), e a contagem só
  começa no dia útil seguinte à publicação (§ 4º).
- **Aviso de movimentação não é intimação.** E-mail do tipo "houve nova
  movimentação" apenas sinaliza. O termo inicial vem do DJe ou do portal.

### 3. Cálculo

```python
from datetime import date
from core.prazos import contar_prazo, Regime, TermoInicial
from core.cnj import validar

numero = validar("0001234-08.2024.5.16.0001")
r = contar_prazo(
    date(2026, 6, 1), 15,
    regime=Regime.CLT_DIAS_UTEIS,
    termo=TermoInicial.DJE_DISPONIBILIZACAO,
    calendario=numero.calendario_sugerido,
    descricao_evento="disponibilização no DJe",
)
print(r.resumo())
```

O regime não é escolhido pelo segmento do tribunal, e sim pelo rito: CPC
(art. 219), CLT (art. 775), Juizados (art. 12-A da Lei 9.099/1995) ou dias
corridos. Na dúvida, pergunte ao advogado em vez de assumir.

Verifique prerrogativa de prazo em dobro quando a parte for Fazenda Pública
(art. 183), Ministério Público (art. 180) ou Defensoria (art. 186). O dobro do
art. 229 não vale em autos eletrônicos (§ 2º).

### 4. Evento na agenda

Crie **dois** eventos no calendário `tiagonevesadvo@gmail.com`:

**Alerta de preparação**, três dias úteis antes do vencimento estimado, dia
inteiro:

```
⚖️ PREPARAR: [providência] — [Cliente]
Processo [CNJ] | [Órgão]
Vencimento estimado: DD/MM/AAAA
```

**Vencimento**, no dia estimado, dia inteiro:

```
🔴 PRAZO (ESTIMADO): [providência] — [Cliente]
```

Descrição de ambos, sempre com este bloco:

```
PRAZO ESTIMADO POR AUTOMAÇÃO — CONFERÊNCIA OBRIGATÓRIA

Processo: [CNJ]
Órgão: [órgão]
Cliente: [cliente]
Ato: [natureza]
Termo inicial: [inciso do art. 231 aplicado]
Evento deflagrador: [DD/MM/AAAA]
Início da contagem: [DD/MM/AAAA]
Regime: [dias úteis CPC/CLT/JEC ou corridos]
Prazo legal: [N] dias

BASE LEGAL APLICADA
[lista de r.base_legal]

AVISOS
[lista de r.avisos]

CHECKLIST
[ ] Conferir o prazo no sistema do tribunal
[ ] Confirmar termo inicial nos autos
[ ] Verificar feriado local e suspensão de expediente
[ ] Levantar documentos necessários
[ ] Elaborar a peça
[ ] Revisar com o auditor forense
[ ] Protocolar (ato do advogado, com certificado digital)

Origem: e-mail de [remetente] em [data]
```

### 5. Registro no acervo

```python
from core.acervo import Acervo, Movimento, Prazo

acervo = Acervo.carregar()
proc = acervo.obter_ou_criar(numero.formatado, orgao="...", cliente="...")
proc.registrar_movimento(Movimento(
    data="2026-06-01", descricao="Sentença publicada", fonte="gmail",
    id_externo="<message-id>",
))
proc.registrar_prazo(Prazo(
    descricao="Recurso ordinário", vencimento_estimado=str(r.vencimento),
    evento=str(r.evento), termo_inicial=r.__dict__["regime"].value,
    regime=r.regime.value, dias=r.dias_prazo,
    base_legal=r.base_legal, avisos=r.avisos,
    id_evento_agenda="<id do evento criado>",
))
acervo.salvar()
```

`id_externo` evita que a mesma intimação, reenviada ou reencaminhada, gere prazo
duplicado.

## Regras invioláveis

1. **Nunca escreva um prazo como certo.** Todo evento, mensagem e registro traz
   "ESTIMADO" e a instrução de conferência.
2. **Nunca protocole nada.** O radar prepara; o protocolo é ato do advogado com
   certificado digital.
3. **Nunca deduza o termo inicial.** Sem a data do meio de comunicação correto,
   o item vai para revisão humana com `[DADO PENDENTE]`.
4. **Nunca marque `conferido_por_humano=True`.** Só o advogado faz isso, e é o
   que retira o prazo da aba Conferência da planilha.
5. **Na dúvida, encurte.** Se houver duas leituras possíveis do termo inicial,
   registre a que produz o prazo mais curto e sinalize a divergência.
6. Se o número CNJ tiver dígito verificador inválido, não cadastre: reporte como
   suspeita de erro de transcrição.
