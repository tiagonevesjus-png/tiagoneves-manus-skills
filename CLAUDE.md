# TNADV — Automações jurídicas

Repositório das automações do escritório **Tiago Neves Advocacia Empresarial**.
Advogado responsável: Tiago Luiz Rodrigues Neves, OAB/MA n.º 10.042.

## O que existe aqui

```
core/                  motor compartilhado (prazos, feriados, CNJ, acervo, planilha)
core/calendarios/      calendários forenses por juízo, confirmados pelo advogado
.claude/skills/        as onze skills de automação
tools/                 utilitários de linha de comando
tests/                 testes do núcleo
docs/                  base legal transcrita, implantação e LGPD
data/                  acervo processual (não versionado)
```

## Regras que valem para qualquer trabalho neste repositório

Estas regras existem porque erro jurídico automatizado é erro em escala.

### 1. Zero alucinação

Lei, súmula, precedente e doutrina só entram depois de verificados na fonte
oficial. Transcrição é literal, sem alteração de palavra. Quando não houver
precedente, escreva "não localizei jurisprudência específica sobre este ponto".
Nunca substitua ausência por citação plausível.

### 2. Prazo é estimativa, não decisão

O motor de `core/prazos.py` produz estimativa com `requer_conferencia=True`.
Nenhuma saída deste repositório afirma prazo como certo. A conferência no
sistema do tribunal é ato do advogado, e é a última barreira.

Ao alterar o motor de prazos ou os calendários, confira o texto legal na fonte
oficial e atualize `docs/BASE-LEGAL-PRAZOS.md`. Não codifique contagem de
memória.

### 3. Dado ausente é `[DADO PENDENTE]`

Marcador visível no lugar exato. Nunca preenchimento por suposição.

### 4. Nada de protocolo automático

O sistema prepara a peça até a véspera do clique. Peticionar exige certificado
digital sob guarda pessoal do advogado, e é ato dele.

### 5. Automação não apaga nem envia

Triagem de e-mail apenas rotula. Dashboard cria rascunho, não envia. Nenhuma
automação exclui arquivo, mensagem ou registro.

### 6. Sigilo e LGPD

Ver `docs/LGPD.md`. O diretório `data/` não é versionado. Documentos de cliente
não entram no repositório.

## Desenvolvimento

```bash
pip install -r requirements.txt
python3 -m pytest tests/ -q
python3 tools/gerar_planilha.py --saida "saida/controle.xlsx"
```

Todo teste do motor de prazos foi conferido manualmente contra o texto legal. Ao
mudar valor esperado em teste, refaça a conferência à mão e registre o porquê no
commit.

## Estilo de redação jurídica

Técnico, direto, sem grandiloquência. Frases curtas. Vírgulas no lugar de
travessões longos. Sem conectivo ornamental abrindo parágrafo. O texto deve
soar escrito por advogado experiente que quer ser compreendido.
