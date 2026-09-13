"""Testes do gerador de filtros nativos do Gmail."""

import xml.etree.ElementTree as ET

import pytest

from core.filtros_gmail import (
    PROIBIDAS,
    Filtro,
    escrever,
    gerar_xml,
    regras_tnadv,
    validar_regras,
)

NS = {
    "a": "http://www.w3.org/2005/Atom",
    "apps": "http://schemas.google.com/apps/2006",
}


def _entradas(xml: str):
    return ET.fromstring(xml).findall("a:entry", NS)


def test_xml_gerado_e_bem_formado():
    entradas = _entradas(gerar_xml(regras_tnadv()))
    assert len(entradas) == len(regras_tnadv())


def test_nenhum_filtro_arquiva_apaga_ou_marca_como_lido():
    """CLAUDE.md, regra 5: automação não apaga nem envia."""
    xml = gerar_xml(regras_tnadv())
    nomes = {
        p.get("name")
        for e in _entradas(xml)
        for p in e.findall("apps:property", NS)
    }
    assert not (nomes & PROIBIDAS), f"propriedade destrutiva presente: {nomes & PROIBIDAS}"


def test_todo_filtro_aplica_rotulo_da_taxonomia():
    for e in _entradas(gerar_xml(regras_tnadv())):
        rotulos = [
            p.get("value")
            for p in e.findall("apps:property", NS)
            if p.get("name") == "label"
        ]
        assert len(rotulos) == 1
        assert rotulos[0].startswith("TNADV/")


def test_todo_filtro_tem_criterio_de_correspondencia():
    for e in _entradas(gerar_xml(regras_tnadv())):
        criterios = {
            p.get("name")
            for p in e.findall("apps:property", NS)
        } & {"from", "to", "subject", "hasTheWord", "doesNotHaveTheWord"}
        assert criterios, "filtro sem critério casaria com a caixa inteira"


def test_filtro_sem_criterio_e_rejeitado():
    with pytest.raises(ValueError, match="critério"):
        Filtro(rotulo="TNADV/Arquivo", descricao="sem critério").para_xml()


def test_propriedade_destrutiva_e_rejeitada_na_montagem():
    class FiltroMalicioso(Filtro):
        def propriedades(self):
            return [("from", "x@y.com"), ("shouldTrash", "true")]

    with pytest.raises(ValueError, match="proibida"):
        FiltroMalicioso(rotulo="TNADV/Arquivo", descricao="ruim").para_xml()


def test_validacao_detecta_rotulo_fora_da_taxonomia():
    problemas = validar_regras([Filtro(rotulo="Outro", descricao="x", de="a@b.com")])
    assert any("fora da taxonomia" in p for p in problemas)


def test_validacao_detecta_duplicata():
    f = Filtro(rotulo="TNADV/Arquivo", descricao="x", de="a@b.com")
    problemas = validar_regras([f, f])
    assert any("duplicada" in p for p in problemas)


def test_regras_do_escritorio_passam_na_validacao():
    assert validar_regras(regras_tnadv()) == []


def test_aspas_e_caracteres_especiais_sao_escapados():
    f = Filtro(
        rotulo="TNADV/Intimações",
        descricao="Assunto com aspas & sinais <>",
        assunto='"Diário da Justiça" OR intimação',
    )
    xml = gerar_xml([f])
    ET.fromstring(xml)  # não deve levantar
    assert "&amp;" in xml and "&lt;" in xml


def test_escrever_cria_arquivo(tmp_path):
    destino = escrever(regras_tnadv(), tmp_path / "sub" / "filtros.xml")
    assert destino.exists()
    ET.fromstring(destino.read_text(encoding="utf-8"))


def test_lista_vazia_e_rejeitada():
    with pytest.raises(ValueError):
        gerar_xml([])
