"""Testes de manuseio da planilha de controle.

A planilha é onde o advogado filtra, ordena e imprime o acervo. Estes testes
travam o que torna isso possível: data gravada como data, filtro em todo
cabeçalho, número do processo à vista e códigos internos traduzidos.
"""

from datetime import date, datetime

import pytest
from openpyxl import load_workbook

from core import cnj, planilha
from core.acervo import Acervo, Audiencia, Movimento, Prazo
from core.prazos import ROTULO_REGIME, ROTULO_TERMO, Regime, TermoInicial

HOJE = date(2026, 11, 3)


def _numero(seq: str, j: str, tr: str) -> str:
    return f"{seq}-{cnj.gerar_digito(seq, '2026', j, tr, '0001')}.2026.{j}.{tr}.0001"


@pytest.fixture
def planilha_gerada(tmp_path):
    acervo = Acervo()
    p1 = acervo.obter_ou_criar(_numero("0000001", "8", "10"), cliente="Cliente A")
    p1.registrar_prazo(Prazo(
        descricao="Contestação", vencimento_estimado="2026-11-05", evento="2026-10-20",
        termo_inicial="dje_disponibilizacao", regime="cpc_dias_uteis", dias=15,
    ))
    # Datas escolhidas para que a ordem do texto "dd/mm/aaaa" seja a errada.
    p1.registrar_audiencia(Audiencia(data="2026-12-01", hora="09:00"))
    p1.registrar_audiencia(Audiencia(data="2026-11-10", hora="14:00"))
    p1.registrar_movimento(Movimento(data="2026-10-20", descricao="Citação", fonte="pje"))
    p2 = acervo.obter_ou_criar(_numero("0000002", "5", "16"), cliente="Cliente B")
    p2.registrar_prazo(Prazo(
        descricao="Recurso", vencimento_estimado="2026-11-25", evento="2026-11-10",
        termo_inicial="codigo_novo_desconhecido", regime="clt_dias_uteis", dias=8,
    ))
    destino = planilha.gerar(acervo, tmp_path / "controle.xlsx", hoje=HOJE)
    return load_workbook(destino)


def test_datas_sao_gravadas_como_data_e_exibidas_em_dd_mm_aaaa(planilha_gerada):
    wb = planilha_gerada
    for aba, celula in (("Acervo", "J2"), ("Prazos", "B2"), ("Prazos", "G2"),
                        ("Audiências", "A2"), ("Movimentações", "A2"),
                        ("Conferência", "D5")):
        c = wb[aba][celula]
        assert isinstance(c.value, datetime), f"{aba}!{celula} gravada como {type(c.value)}"
        assert c.number_format == planilha.FORMATO_DATA


def test_audiencias_saem_em_ordem_cronologica(planilha_gerada):
    ws = planilha_gerada["Audiências"]
    datas = [ws.cell(row=r, column=1).value.date() for r in range(2, ws.max_row + 1)]
    assert datas == [date(2026, 11, 10), date(2026, 12, 1)]


def test_toda_aba_tem_filtro_e_painel_congelado(planilha_gerada):
    esperado = {
        "Acervo": ("A1", "B2"), "Prazos": ("A1", "E2"), "Audiências": ("A1", "E2"),
        "Movimentações": ("A1", "C2"), "Conferência": ("A4", "B5"),
    }
    for aba, (inicio_filtro, congelado) in esperado.items():
        ws = planilha_gerada[aba]
        assert ws.auto_filter.ref and ws.auto_filter.ref.startswith(inicio_filtro), aba
        assert ws.freeze_panes == congelado, aba


def test_impressao_cabe_numa_pagina_de_largura(planilha_gerada):
    for ws in planilha_gerada.worksheets:
        assert ws.page_setup.orientation == "landscape", ws.title
        assert ws.sheet_properties.pageSetUpPr.fitToPage is True, ws.title
        assert ws.page_setup.fitToWidth == 1, ws.title


def test_codigos_internos_aparecem_com_nome_legivel(planilha_gerada):
    ws = planilha_gerada["Prazos"]
    linhas = {ws.cell(row=r, column=6).value: r for r in range(2, ws.max_row + 1)}
    r = linhas["Contestação"]
    assert ws.cell(row=r, column=8).value == "Disponibilização no DJe"
    assert ws.cell(row=r, column=9).value == "CPC, dias úteis"
    # Código desconhecido não some nem vira rótulo inventado: aparece como veio.
    assert ws.cell(row=linhas["Recurso"], column=8).value == "codigo_novo_desconhecido"


def test_cabecalho_diz_de_que_dia_e_a_contagem(planilha_gerada):
    assert planilha_gerada["Prazos"]["C1"].value == "Dias restantes (em 03/11/2026)"
    assert planilha_gerada["Audiências"]["C1"].value == "Dias restantes (em 03/11/2026)"


def test_todo_regime_e_termo_tem_rotulo():
    assert set(ROTULO_REGIME) == set(Regime)
    assert set(ROTULO_TERMO) == set(TermoInicial)


def test_data_malformada_nao_derruba_a_geracao(tmp_path):
    acervo = Acervo()
    proc = acervo.obter_ou_criar(_numero("0000003", "8", "10"))
    proc.registrar_movimento(Movimento(data="sem data", descricao="Anotação", fonte="manual"))
    wb = load_workbook(planilha.gerar(acervo, tmp_path / "c.xlsx", hoje=HOJE))
    assert wb["Movimentações"]["A2"].value == "sem data"
