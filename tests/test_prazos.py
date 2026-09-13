"""Testes do motor de prazos.

Cada caso foi conferido manualmente contra o texto legal transcrito em
docs/BASE-LEGAL-PRAZOS.md. Ao alterar o motor, refaça a conferência à mão antes
de ajustar os valores esperados.
"""

from datetime import date

import pytest

from core.feriados import Calendario, feriados_moveis, pascoa
from core.prazos import Regime, TermoInicial, contar_prazo


def test_pascoa_datas_conhecidas():
    assert pascoa(2024) == date(2024, 3, 31)
    assert pascoa(2025) == date(2025, 4, 20)
    assert pascoa(2026) == date(2026, 4, 5)
    assert pascoa(2027) == date(2027, 3, 28)


def test_corpus_christi_60_dias_apos_pascoa():
    moveis = feriados_moveis(2026)
    assert moveis[date(2026, 6, 4)][0] == "Corpus Christi"


def test_feriados_nacionais_conferidos():
    cal = Calendario(nome="teste")
    for dia in (
        date(2026, 1, 1), date(2026, 4, 21), date(2026, 5, 1), date(2026, 9, 7),
        date(2026, 10, 12), date(2026, 11, 2), date(2026, 11, 15), date(2026, 11, 20),
        date(2026, 12, 25),
    ):
        assert not cal.e_util(dia), f"{dia} deveria ser feriado nacional"


def test_dje_publicacao_e_inicio_no_dia_util_seguinte():
    """Lei 11.419/2006, art. 4º, §§ 3º e 4º; CPC, art. 224, §§ 2º e 3º."""
    r = contar_prazo(date(2026, 6, 1), 15)
    assert r.intimacao_considerada == date(2026, 6, 2)   # publicação
    assert r.inicio_contagem == date(2026, 6, 3)         # início da contagem
    assert r.vencimento == date(2026, 6, 24)             # 15º dia útil
    assert r.requer_conferencia is True


def test_corpus_christi_nao_e_computado():
    r = contar_prazo(date(2026, 6, 1), 15)
    dia = next(d for d in r.trilha if d.data == date(2026, 6, 4))
    assert dia.util is False
    assert dia.ordinal is None


def test_prazo_atravessa_recesso_forense():
    """CPC, art. 220; CLT, art. 775-A: suspensão de 20/12 a 20/01."""
    r = contar_prazo(date(2025, 12, 10), 15)
    assert r.inicio_contagem == date(2025, 12, 12)
    assert r.vencimento == date(2026, 2, 2)
    assert any("recesso" in a for a in r.avisos)


def test_dias_corridos_da_juntada_do_ar():
    """CPC, art. 231, I, com contagem em dias corridos."""
    r = contar_prazo(
        date(2026, 5, 4), 10,
        regime=Regime.DIAS_CORRIDOS,
        termo=TermoInicial.JUNTADA_AR,
    )
    assert r.inicio_contagem == date(2026, 5, 5)
    assert r.vencimento == date(2026, 5, 14)


def test_dias_corridos_prorroga_vencimento_em_dia_nao_util():
    """CPC, art. 224, § 1º."""
    # Início em 02/01/2026 cairia dentro do recesso; usa-se calendário sem recesso
    # para isolar a regra de prorrogação do vencimento.
    cal = Calendario(nome="sem recesso", aplicar_recesso=False, confirmado=True,
                     locais={"2026-05-16": "feriado local fictício de teste"})
    r = contar_prazo(
        date(2026, 5, 4), 10,
        regime=Regime.DIAS_CORRIDOS,
        termo=TermoInicial.JUNTADA_AR,
        calendario=cal,
    )
    # 05/05 + 9 = 14/05 (quinta, útil): sem prorrogação neste recorte
    assert r.vencimento == date(2026, 5, 14)


def test_decurso_do_prazo_de_consulta_dez_dias_corridos():
    """Lei 11.419/2006, art. 5º, § 3º; CPC, art. 231, V."""
    r = contar_prazo(
        date(2026, 3, 2), 15,
        termo=TermoInicial.DECURSO_PRAZO_CONSULTA,
    )
    assert r.intimacao_considerada == date(2026, 3, 12)  # 10 dias corridos
    assert r.inicio_contagem == date(2026, 3, 13)
    assert r.vencimento == date(2026, 4, 2)
    assert any("10 dias corridos" in a for a in r.avisos)


def test_consulta_em_dia_nao_util_desloca_intimacao():
    """Lei 11.419/2006, art. 5º, § 2º."""
    r = contar_prazo(
        date(2026, 3, 7), 5,  # sábado
        termo=TermoInicial.CONSULTA_ELETRONICA,
    )
    assert r.intimacao_considerada == date(2026, 3, 9)  # segunda
    assert any("dia não útil" in a for a in r.avisos)


def test_prazo_em_dobro_fazenda_publica():
    """CPC, art. 183."""
    r = contar_prazo(date(2026, 6, 1), 15, prerrogativa_dobro="fazenda_publica")
    assert r.dias_efetivos == 30
    assert r.vencimento == date(2026, 7, 15)
    assert any("art. 183" in b for b in r.base_legal)


def test_dobro_do_art_229_avisa_sobre_autos_eletronicos():
    r = contar_prazo(
        date(2026, 6, 1), 15, prerrogativa_dobro="litisconsortes_autos_fisicos"
    )
    assert any("autos eletrônicos" in a for a in r.avisos)


def test_regime_clt_carrega_base_legal_correta():
    r = contar_prazo(
        date(2026, 6, 1), 8,
        regime=Regime.CLT_DIAS_UTEIS,
        calendario="justica-do-trabalho",
    )
    assert any("art. 775" in b and "13.467" in b for b in r.base_legal)


def test_regime_jec_carrega_base_legal_correta():
    r = contar_prazo(date(2026, 6, 1), 10, regime=Regime.JEC_DIAS_UTEIS)
    assert any("art. 12-A" in b for b in r.base_legal)


def test_calendario_nao_confirmado_gera_aviso():
    r = contar_prazo(date(2026, 6, 1), 15)
    assert any("não foi confirmado" in a for a in r.avisos)
    assert any("ESTIMATIVA" in a for a in r.avisos)


def test_justica_federal_aplica_lei_5010():
    cal = Calendario.carregar("justica-federal")
    assert not cal.e_util(date(2026, 8, 11))   # Dia do Advogado, art. 62, IV
    assert not cal.e_util(date(2026, 12, 8))   # art. 62, IV
    assert not cal.e_util(date(2026, 4, 2))    # quinta-feira da Semana Santa, art. 62, II


def test_prazo_nao_positivo_e_rejeitado():
    with pytest.raises(ValueError):
        contar_prazo(date(2026, 6, 1), 0)


def test_prerrogativa_desconhecida_e_rejeitada():
    with pytest.raises(ValueError):
        contar_prazo(date(2026, 6, 1), 15, prerrogativa_dobro="inexistente")


def test_resumo_declara_estimativa():
    r = contar_prazo(date(2026, 6, 1), 15)
    texto = r.resumo()
    assert "VENCIMENTO ESTIMADO" in texto
    assert "CONFERÊNCIA OBRIGATÓRIA" in texto
