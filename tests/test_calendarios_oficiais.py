"""Testes dos calendários forenses oficiais do TRT16 e do TJMA.

As datas abaixo foram conferidas nas fontes oficiais em 12/09/2026:

- TRT16: calendário institucional em iCal
  https://www.trt16.jus.br/site/conteudo/calendario/cieEvtExportaIcs.php?ano=2026
- TJMA: Calendário Forense 2026, imagens mensais
  https://www.tjma.jus.br/midia/tj/calendario-forense/titulo-calendario/432875

Ao regenerar um calendário, reconfira na fonte antes de alterar valor esperado.
"""

from datetime import date

import pytest

from core.feriados import Calendario
from core.prazos import Regime, contar_prazo


@pytest.fixture(scope="module")
def trt16() -> Calendario:
    return Calendario.carregar("TRT16-sao-luis")


@pytest.fixture(scope="module")
def tjma() -> Calendario:
    return Calendario.carregar("TJMA-sao-luis")


def test_calendarios_estao_confirmados(trt16, tjma):
    assert trt16.confirmado is True
    assert tjma.confirmado is True


def test_proveniencia_registrada(trt16, tjma):
    """Instrumento jurídico sem origem rastreável não serve."""
    for cal in (trt16, tjma):
        assert cal.fonte.startswith("https://")
        assert cal.consultado_em


def test_ambos_cobrem_2026(trt16, tjma):
    assert trt16.anos_cobertos() == {2026}
    assert tjma.anos_cobertos() == {2026}


# --- Divergências reais entre os dois tribunais, por transferência de feriado ---

DIVERGENCIAS = [
    # (data, útil no TRT16, útil no TJMA, feriado)
    (date(2026, 7, 27), False, True, "Adesão do Maranhão"),
    (date(2026, 7, 28), True, False, "Adesão do Maranhão"),
    (date(2026, 8, 10), False, True, "Dia do Advogado"),
    (date(2026, 8, 11), True, False, "Dia do Advogado"),
    (date(2026, 10, 28), True, False, "Dia do Servidor Público"),
    (date(2026, 10, 30), False, True, "Dia do Servidor Público"),
]


@pytest.mark.parametrize("dia,util_trt,util_tj,feriado", DIVERGENCIAS)
def test_divergencia_entre_tribunais(trt16, tjma, dia, util_trt, util_tj, feriado):
    assert trt16.e_util(dia) is util_trt, f"{feriado} no TRT16 em {dia}"
    assert tjma.e_util(dia) is util_tj, f"{feriado} no TJMA em {dia}"


def test_feriados_municipais_de_sao_luis_em_ambos(trt16, tjma):
    """São Pedro e a fundação da cidade valem nos dois tribunais."""
    for dia in (date(2026, 6, 29), date(2026, 9, 8)):
        assert not trt16.e_util(dia)
        assert not tjma.e_util(dia)


def test_semana_santa_completa_nos_dois(trt16, tjma):
    """Quarta, quinta e sexta da Semana Santa, não apenas a Paixão."""
    for dia in (date(2026, 4, 1), date(2026, 4, 2), date(2026, 4, 3)):
        assert not trt16.e_util(dia)
        assert not tjma.e_util(dia)


def test_quarta_de_cinzas_e_dia_sem_expediente(trt16, tjma):
    assert not trt16.e_util(date(2026, 2, 18))
    assert not tjma.e_util(date(2026, 2, 18))


def test_trt16_tem_ponto_facultativo_e_inspecao(trt16):
    assert not trt16.e_util(date(2026, 4, 20))   # ponto facultativo
    assert not trt16.e_util(date(2026, 1, 14))   # inspeção judicial


def test_calendario_generico_nao_pega_feriado_local():
    """O motor não presume feriado local: é essa a razão dos arquivos oficiais."""
    generico = Calendario.carregar("justica-do-trabalho")
    assert generico.e_util(date(2026, 9, 8))     # fundação de São Luís passa batido
    assert generico.e_util(date(2026, 7, 27))    # adesão do Maranhão passa batido
    assert not generico.confirmado


def test_ano_nao_coberto_gera_aviso_explicito(trt16):
    avisos = trt16.avisos(ano=2027)
    assert any("não cobre o ano de 2027" in a for a in avisos)


def test_ano_coberto_nao_gera_aviso_de_cobertura(trt16):
    avisos = trt16.avisos(ano=2026)
    assert not any("não cobre o ano" in a for a in avisos)


def test_prazo_que_vira_o_ano_avisa_sobre_feriados_ausentes():
    r = contar_prazo(
        date(2026, 12, 15), 15,
        regime=Regime.CLT_DIAS_UTEIS,
        calendario="TRT16-sao-luis",
    )
    assert r.vencimento.year == 2027
    assert any("termina em 2027" in a for a in r.avisos)


def test_prazo_com_calendario_oficial_nao_avisa_falta_de_confirmacao():
    r = contar_prazo(
        date(2026, 9, 8), 8,
        regime=Regime.CLT_DIAS_UTEIS,
        calendario="TRT16-sao-luis",
    )
    assert not any("não foi confirmado" in a for a in r.avisos)
    assert any("Fonte do calendário" in a for a in r.avisos)
    assert r.requer_conferencia is True  # continua estimativa, sempre
