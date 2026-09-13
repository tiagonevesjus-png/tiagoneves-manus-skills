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
from core.prazos import Regime, TermoInicial, contar_prazo


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


# --------------------------------------------------------------------------
# TJCE, Comarca de Fortaleza
# Fonte: Portaria nº 2924/2025 da Presidência do TJCE (feriados de janeiro/2026
# a janeiro/2027) e Portaria nº 727/2026 (aniversário da cidade de Fortaleza),
# ambas conferidas em 13/09/2026.
# --------------------------------------------------------------------------


@pytest.fixture(scope="module")
def tjce() -> Calendario:
    return Calendario.carregar("TJCE-fortaleza")


def test_tjce_confirmado_e_com_proveniencia(tjce):
    assert tjce.confirmado is True
    assert tjce.fonte.startswith("https://")
    assert tjce.consultado_em


def test_tjce_e_o_unico_que_ja_cobre_2027(tjce, trt16, tjma):
    assert tjce.anos_cobertos() == {2026, 2027}
    assert 2027 not in trt16.anos_cobertos()
    assert 2027 not in tjma.anos_cobertos()


def test_tjce_feriados_proprios_do_ceara(tjce):
    assert not tjce.e_util(date(2026, 3, 19))   # Dia de São José
    assert not tjce.e_util(date(2026, 3, 25))   # Data Magna do Ceará
    assert not tjce.e_util(date(2026, 12, 8))   # Dia da Justiça


def test_tjce_aniversario_de_fortaleza_e_local(tjce, tjma):
    """Portaria 727/2026: ponto facultativo só na Comarca de Fortaleza."""
    assert not tjce.e_util(date(2026, 4, 13))
    assert tjma.e_util(date(2026, 4, 13))


def test_tjce_semana_santa_nao_inclui_a_quarta(tjce, tjma, trt16):
    """O TJCE para só na quinta e na sexta; TJMA e TRT16 param também na quarta."""
    assert tjce.e_util(date(2026, 4, 1))
    assert not tjma.e_util(date(2026, 4, 1))
    assert not trt16.e_util(date(2026, 4, 1))
    for dia in (date(2026, 4, 2), date(2026, 4, 3)):
        assert not tjce.e_util(dia)


def test_tjce_nao_tem_dia_do_advogado(tjce, tjma):
    assert tjce.e_util(date(2026, 8, 11))
    assert not tjma.e_util(date(2026, 8, 11))


# --- Expediente reduzido: CPC, art. 224, § 1º -----------------------------


def test_cinzas_no_tjce_e_dia_util_de_expediente_reduzido(tjce):
    """Ponto facultativo até as 14h não é dia parado: há expediente."""
    dia = date(2026, 2, 18)
    assert tjce.e_util(dia) is True
    assert tjce.expediente_pleno(dia) is False
    assert "14h" in tjce.motivo_expediente_reduzido(dia)


def test_dia_reduzido_conta_no_meio_do_prazo(tjce):
    """Ele é dia útil, logo entra na contagem."""
    r = contar_prazo(
        date(2026, 2, 9), 10,
        termo=TermoInicial.PUBLICACAO,
        calendario="TJCE-fortaleza",
    )
    contado = next(d for d in r.trilha if d.data == date(2026, 2, 18))
    assert contado.util is True
    assert contado.ordinal is not None


def test_vencimento_em_dia_reduzido_e_prorrogado(tjce):
    """CPC, art. 224, § 1º: expediente iniciado depois da hora normal protrai."""
    r = contar_prazo(
        date(2026, 2, 9), 5,
        termo=TermoInicial.PUBLICACAO,
        calendario="TJCE-fortaleza",
    )
    assert r.vencimento == date(2026, 2, 19)
    assert any("expediente reduzido" in a and "224" in a for a in r.avisos)


def test_inicio_em_dia_reduzido_e_prorrogado(tjce):
    """O dia do começo também é protraído (art. 224, § 1º)."""
    # Publicação em 17/02 faria a contagem começar em 18/02, dia reduzido.
    r = contar_prazo(
        date(2026, 2, 17), 5,
        termo=TermoInicial.PUBLICACAO,
        calendario="TJCE-fortaleza",
    )
    assert r.inicio_contagem == date(2026, 2, 19)


def test_calendario_sem_expediente_reduzido_nao_muda_de_comportamento(trt16):
    assert trt16.expediente_reduzido == {}
    assert trt16.expediente_pleno(date(2026, 9, 10)) is True


# --- A prova de que calendário trocado é prazo errado ---------------------


def test_os_tres_tribunais_do_acervo_divergem_entre_si():
    """Nenhum dos três tribunais trata estas seis datas de 2026 do mesmo modo."""
    cals = {k: Calendario.carregar(k) for k in (
        "TRT16-sao-luis", "TJMA-sao-luis", "TJCE-fortaleza"
    )}
    datas = [date(2026, 3, 25), date(2026, 4, 1), date(2026, 4, 13),
             date(2026, 8, 11), date(2026, 10, 28), date(2026, 10, 30)]
    assinaturas = {c: tuple(cal.e_util(d) for d in datas) for c, cal in cals.items()}
    assert len(set(assinaturas.values())) == 3, (
        f"dois tribunais ficaram idênticos nestas datas: {assinaturas}"
    )


def test_comarcas_do_mesmo_tribunal_tambem_divergem():
    """Dentro do TRT16, São Luís e Santa Inês não param nos mesmos dias."""
    sl = Calendario.carregar("TRT16-sao-luis")
    si = Calendario.carregar("TRT16-santa-ines")
    # Padroeira de Santa Inês, 21/01: só lá.
    assert sl.e_util(date(2026, 1, 21)) and not si.e_util(date(2026, 1, 21))
    # Fundação de São Luís, 08/09: só lá.
    assert si.e_util(date(2026, 9, 8)) and not sl.e_util(date(2026, 9, 8))
    # A emancipação de Santa Inês (14/03) não distingue nada em 2026: cai
    # num sábado, e sábado já não é dia útil em lugar nenhum.
    assert date(2026, 3, 14).weekday() == 5
