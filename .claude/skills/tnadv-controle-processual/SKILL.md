---
name: tnadv-controle-processual
description: Planilha viva de controle processual do escritório Tiago Neves. Gera e atualiza o arquivo xlsx do acervo a partir dos dados consolidados, com abas de acervo, prazos semaforizados, movimentações e conferência pendente. Use quando o usuário pedir planilha de controle, relatório de acervo, mapa de prazos, ou depois de qualquer atualização relevante do acervo.
---

# Planilha viva de controle processual

Converte o acervo (`data/acervo.json`) em um xlsx que o advogado abre, filtra e
leva para reunião. "Viva" porque é regenerada a cada atualização, não mantida à
mão.

## Geração

```bash
python3 tools/gerar_planilha.py --saida "saida/Controle Processual - AAAA-MM-DD.xlsx"
```

Ou, no fluxo de uma sessão:

```python
from datetime import date
from core.acervo import Acervo
from core import planilha

acervo = Acervo.carregar()
planilha.gerar(acervo, "saida/controle.xlsx", hoje=date.today())
```

## Abas

**Acervo.** Um processo por linha: número, cliente, polo, parte contrária, órgão,
classe, assunto, situação, quantidade de prazos abertos e próximo vencimento
(colorido pelo semáforo).

**Prazos.** Um prazo por linha, ordenado por vencimento. Traz urgência, dias
restantes, providência, termo inicial aplicado, regime, e a coluna
`Conferido?`. Quando está em NÃO, aparece em vermelho e negrito.

**Movimentações.** Histórico consolidado, do mais recente para o mais antigo,
com a fonte de cada movimento (gmail, datajud, pje, manual). Serve para
reconstituir de onde veio cada informação.

**Conferência.** A aba mais importante. Isola os prazos estimados que ainda não
foram validados por humano, com a base legal aplicada e os avisos emitidos. Se
esta aba está vazia, o acervo está conferido. Se não está, há risco em aberto.

## Semáforo

Vermelho até 3 dias, amarelo até 10, verde acima. Calculado por
`core.acervo.classificar_urgencia`.

## Alimentação do acervo

A planilha não é a fonte de dados, é a saída. O acervo é alimentado por:

- **radar de intimações**, a partir do Gmail
- **skill `datajud`**, para movimentos por número CNJ
- **skill `pje-controle-processual`**, para inventário do acervo por OAB
- **entrada manual**, para o que só o advogado sabe

Quando levantar acervo novo pelo PJe ou pelo DataJud, reconcilie por número CNJ
antes de inserir: o mesmo processo aparece com grafias diferentes em fontes
diferentes. Use `core.cnj.validar(...).formatado` como chave canônica.

## Conferência humana

Depois de conferir um prazo no sistema do tribunal, marque no acervo:

```python
acervo = Acervo.carregar()
prazo = acervo.processos["0001234-08.2024.5.16.0001"].prazos[0]
prazo.conferido_por_humano = True
prazo.vencimento_estimado = "2026-06-24"   # corrija se a conferência divergiu
acervo.salvar()
```

Quando a conferência divergir da estimativa, **registre a divergência**: é sinal
de que o calendário do tribunal precisa de ajuste em
`core/calendarios/`, ou de que o termo inicial foi mal qualificado. Corrigir a
causa vale mais que corrigir a data.

## Regras invioláveis

1. A planilha exibe estimativas. O rodapé da aba Conferência diz isso, e o texto
   não deve ser removido.
2. Não sobrescreva planilha anterior: nomeie com a data de geração, para manter
   histórico.
3. Não inclua na planilha dado sensível de cliente além do necessário à gestão
   do prazo. Documentos ficam no repositório de arquivos, não aqui.
