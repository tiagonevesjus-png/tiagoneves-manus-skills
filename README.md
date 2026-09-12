# TNADV — Automações jurídicas

Automações do escritório **Tiago Neves Advocacia Empresarial**.
Advogado responsável: Tiago Luiz Rodrigues Neves, OAB/MA n.º 10.042.

Onze automações que cobrem o ciclo de trabalho do escritório, do e-mail que
chega de manhã à peça pronta para protocolo, sobre um núcleo comum de contagem
de prazos com base legal conferida na fonte oficial.

## Camada 1 — rotina diária

| Skill | O que faz |
|---|---|
| `tnadv-dashboard-diario` | Varre Gmail, Agenda e acervo, classifica por urgência e deixa o relatório como rascunho |
| `tnadv-triagem-gmail` | Classifica e rotula a caixa pela taxonomia TNADV, sem apagar nada |
| `tnadv-radar-intimacoes` | Converte intimação em prazo estimado, com evento na agenda e registro no acervo |
| `tnadv-controle-processual` | Gera a planilha viva do acervo, com aba de conferência pendente |

## Camada 2 — produção jurídica

| Skill | O que faz |
|---|---|
| `tnadv-linha-producao-pecas` | Do fato bruto ao `.docx` formatado, com auditoria forense obrigatória |
| `tnadv-organizacao-probatoria-lote` | Renomeia, ordena, indexa e unifica anexos para protocolo |
| `tnadv-biblioteca-teses` | Indexa peças por tese, tribunal e **resultado**, para reaproveitamento auditado |
| `tnadv-pesquisa-jurisprudencial` | Pesquisa verificada em fonte oficial, com transcrição literal |
| `tnadv-kit-audiencia` | Dossiê de audiência: controvérsias, roteiro de perguntas, contradições |
| `tnadv-gestao-publica` | Análise de processo de pagamento e expediente oficial |
| `tnadv-revisor-contratos` | Checklist de risco por posição contratual, com redação alternativa |

## Núcleo

`core/` concentra o que não pode divergir entre automações:

- **`prazos.py`** — contagem por regime (CPC art. 219, CLT art. 775, Lei 9.099
  art. 12-A, dias corridos) e por termo inicial (art. 231 do CPC, Lei
  11.419/2006). Toda saída é estimativa com base legal e avisos anexados.
- **`feriados.py`** — feriados nacionais conferidos, datas móveis pela Páscoa,
  recesso do art. 220 do CPC, feriados da Justiça Federal (Lei 5.010/1966).
- **`cnj.py`** — validação do número único pelo dígito verificador.
- **`acervo.py`** — processos, movimentos e prazos, com desduplicação.
- **`planilha.py`** — planilha de controle em xlsx.
- **`filtros_gmail.py`** — filtros nativos do Gmail para a taxonomia TNADV.

## Três premissas de projeto

**Prazo é estimativa.** Nada aqui afirma prazo como certo. A conferência no
sistema do tribunal é ato do advogado, e a planilha isola numa aba própria tudo
que ainda não passou por ela.

**Zero alucinação.** Lei, súmula e precedente só entram verificados na fonte
oficial, transcritos literalmente. Onde não há precedente, o sistema declara que
não localizou.

**Nada de protocolo automático.** As automações preparam até a véspera do
clique. Peticionar exige certificado digital sob guarda pessoal do advogado.

## Uso

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -q
python3 tools/gerar_planilha.py --saida "saida/controle.xlsx"
```

## Documentação

- [`docs/BASE-LEGAL-PRAZOS.md`](docs/BASE-LEGAL-PRAZOS.md) — transcrição literal de tudo que o motor aplica
- [`docs/IMPLANTACAO.md`](docs/IMPLANTACAO.md) — estado de cada peça e o que falta destravar
- [`docs/LGPD.md`](docs/LGPD.md) — sigilo profissional e classificação de dados
- [`CLAUDE.md`](CLAUDE.md) — regras de trabalho no repositório
