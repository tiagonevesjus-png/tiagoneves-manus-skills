"""Integridade de todos os arquivos de calendário do diretório.

Existe para que um calendário novo, acrescentado à mão, não entre no
repositório malformado. O CI roda isto a cada push.
"""

import json
from datetime import date

import pytest

from core.feriados import CALENDARIOS_DIR, Calendario

ARQUIVOS = sorted(CALENDARIOS_DIR.glob("*.json"))
CHAVES = [p.stem for p in ARQUIVOS]


def test_existem_calendarios():
    assert CHAVES, "nenhum calendário encontrado"


@pytest.mark.parametrize("chave", CHAVES)
def test_todo_calendario_carrega(chave):
    cal = Calendario.carregar(chave)
    assert cal.nome


@pytest.mark.parametrize("chave", CHAVES)
def test_datas_locais_sao_iso_validas(chave):
    cal = Calendario.carregar(chave)
    for iso in list(cal.locais) + list(cal.expediente_reduzido):
        date.fromisoformat(iso)  # levanta se estiver malformada


@pytest.mark.parametrize("chave", CHAVES)
def test_dia_reduzido_nao_e_tambem_feriado(chave):
    """Um dia não pode ser, ao mesmo tempo, parado e de expediente reduzido."""
    cal = Calendario.carregar(chave)
    sobreposicao = set(cal.locais) & set(cal.expediente_reduzido)
    assert not sobreposicao, f"datas em conflito em {chave}: {sobreposicao}"


@pytest.mark.parametrize("chave", CHAVES)
def test_calendario_confirmado_declara_a_fonte(chave):
    """Calendário marcado como confirmado precisa dizer de onde veio."""
    cal = Calendario.carregar(chave)
    if cal.confirmado:
        assert cal.fonte.startswith("http"), f"{chave} confirmado sem fonte"
        assert cal.consultado_em, f"{chave} confirmado sem data de consulta"


@pytest.mark.parametrize("chave", CHAVES)
def test_calendario_confirmado_tem_feriado_local(chave):
    """Confirmar um calendário vazio seria declarar que não há feriado local."""
    cal = Calendario.carregar(chave)
    if cal.confirmado:
        assert cal.locais, f"{chave} confirmado mas sem nenhuma data"


@pytest.mark.parametrize("caminho", ARQUIVOS, ids=CHAVES)
def test_json_bem_formado_e_com_chaves_conhecidas(caminho):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    conhecidas = {
        "_comentario", "_fonte", "_consultado_em", "nome", "justica_federal",
        "aplicar_recesso", "considerar_moveis", "locais", "expediente_reduzido",
        "confirmado", "observacoes",
    }
    desconhecidas = set(dados) - conhecidas
    assert not desconhecidas, f"chaves não reconhecidas em {caminho.name}: {desconhecidas}"
