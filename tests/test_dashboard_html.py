"""Testes do renderizador do Dashboard Jurídico Diário.

O dashboard é entregue como rascunho no Gmail. Cliente de e-mail descarta folha
de estilo externa, não entende flexbox nem grid, e às vezes remove o bloco
<style> inteiro. Estes testes travam as restrições que fazem o layout sobreviver
a isso, e também as regras jurídicas que a saída precisa carregar.
"""

import re
from datetime import date

import pytest

from core import identidade
from core.dashboard_html import (
    Compromisso,
    Dashboard,
    Item,
    data_por_extenso,
    render_html,
    render_pagina,
    render_texto,
)


@pytest.fixture
def dash() -> Dashboard:
    return Dashboard(
        data=date(2026, 9, 14),
        resumo="Duas audiências conflitantes e um recurso admitido sem efeito suspensivo.",
        itens=[
            Item(
                urgencia="vermelho",
                titulo="Conflito de audiências",
                processo="0801774-18.2026.8.10.0050",
                cliente="Cliente Exemplo LTDA",
                orgao="Juizado de Paço do Lumiar",
                o_que_houve="Duas audiências presenciais no mesmo dia.",
                providencia="Pedir redesignação ou constituir audiencista.",
                vencimento_estimado="2026-09-28",
                alerta="Não comparecer produz presunção de veracidade (Lei 9.099, art. 20).",
                fontes=["agenda", "e-mail do cliente"],
            ),
            Item(
                urgencia="amarelo",
                titulo="Recurso ordinário admitido",
                processo="0017806-39.2025.5.16.0022",
                cliente="Outro Cliente LTDA",
            ),
            Item(urgencia="verde", titulo="Despacho de mero expediente"),
        ],
        agenda=[
            Compromisso(quando="Hoje, 09:00", titulo="Reunião",
                        detalhe="Pauta pendente", alerta="Data divergente",
                        data=date(2026, 9, 14)),
            Compromisso(quando="Amanhã, 14:30", titulo="Audiência de instrução",
                        data=date(2026, 9, 15)),
        ],
        pendentes_conferencia=["Nenhum prazo cadastrado no acervo."],
        pendencias_sistema=["Comarca sem calendário confirmado."],
        fontes_varredura=["Gmail (24h)", "Google Agenda", "acervo"],
    )


# --- Restrições de cliente de e-mail --------------------------------------


def test_layout_usa_tabela_e_nao_depende_de_css_moderno(dash):
    html = render_html(dash)
    assert "<table" in html
    for proibido in ("display:flex", "display:grid", "position:absolute",
                     "position:fixed", "@media", "var(--"):
        assert proibido not in html, f"{proibido} não sobrevive em cliente de e-mail"


def test_nao_carrega_recurso_externo(dash):
    """Fonte, folha de estilo ou imagem remota são bloqueadas ou quebram."""
    html = render_html(dash)
    for proibido in ("<link", "<script", "@import", "https://fonts",
                     "url(http", "<img"):
        assert proibido not in html


def test_estilos_sao_inline(dash):
    """Gmail remove <style> do corpo; o estilo tem de estar em cada elemento."""
    html = render_html(dash)
    assert "<style" not in html
    assert html.count('style="') > 20


def test_largura_fixa_com_teto_percentual(dash):
    html = render_html(dash)
    assert "640" in html
    assert "max-width:100%" in html


# --- Identidade do escritório ---------------------------------------------


def test_usa_as_cores_institucionais(dash):
    html = render_html(dash)
    assert identidade.AZUL_MARINHO in html
    assert identidade.DOURADO in html


def test_traz_o_advogado_e_a_oab(dash):
    html = render_html(dash)
    assert identidade.ESCRITORIO.advogado in html
    assert "10.042" in html


def test_campo_pendente_do_escritorio_nao_vaza_para_o_rodape(dash):
    """Endereço e telefone ainda não informados: não imprimir o marcador."""
    html = render_html(dash)
    assert "[DADO PENDENTE]" not in html
    assert identidade.ESCRITORIO.pendencias()  # continuam registrados no modelo


# --- Regras jurídicas que a saída precisa carregar ------------------------


def test_todo_prazo_vem_com_a_ressalva_de_conferencia(dash):
    html = render_html(dash)
    assert "VENCIMENTO ESTIMADO" in html
    assert "CONFERIR NO SISTEMA" in html


def test_aviso_de_estimativa_esta_presente_nas_tres_saidas(dash):
    for saida in (render_html(dash), render_pagina(dash), render_texto(dash)):
        assert "ESTIMATIVAS" in saida


def test_alerta_do_item_aparece(dash):
    html = render_html(dash)
    assert "art. 20" in html


# --- Agenda do dia ---------------------------------------------------------


def test_agenda_do_dia_separa_hoje_do_que_vem_depois(dash):
    assert [c.titulo for c in dash.agenda_do_dia()] == ["Reunião"]
    assert [c.titulo for c in dash.agenda_adiante()] == ["Audiência de instrução"]


def test_bloco_do_dia_vem_antes_dos_cartoes_de_urgencia(dash):
    """O dia é a primeira coisa que se lê, depois do resumo."""
    html = render_html(dash)
    assert html.index("Agenda do dia") < html.index("Conflito de audiências")
    assert html.index("Agenda do dia") < html.index("Próximos compromissos")


def test_compromisso_de_hoje_nao_se_repete_em_proximos(dash):
    html = render_html(dash)
    assert html.count("Reunião") == 1
    assert html.count("Audiência de instrução") == 1


def test_prazo_que_vence_hoje_entra_na_agenda_do_dia_com_ressalva():
    d = Dashboard(
        data=date(2026, 9, 28),
        resumo="Prazo estimado vencendo.",
        itens=[Item(urgencia="vermelho", titulo="Redesignação de audiência",
                    processo="0801774-18.2026.8.10.0050",
                    providencia="Protocolar pedido.",
                    vencimento_estimado="2026-09-28")],
    )
    assert [i.titulo for i in d.vencimentos_do_dia()] == ["Redesignação de audiência"]
    for saida in (render_html(d), render_texto(d)):
        assert "Vencimento estimado para hoje" in saida
        assert "CONFERIR NO SISTEMA" in saida


def test_prazo_de_outro_dia_nao_aparece_na_agenda_do_dia(dash):
    """O único vencimento é 28/09, e o dashboard é de 14/09."""
    assert dash.vencimentos_do_dia() == []
    assert "Vencimento estimado para hoje" not in render_html(dash)


def test_compromisso_sem_data_nao_e_presumido_de_hoje():
    d = Dashboard(
        data=date(2026, 9, 14),
        resumo="Agenda incompleta.",
        agenda=[Compromisso(quando="Hoje, 09:00", titulo="Reunião sem data na fonte")],
    )
    assert d.agenda_do_dia() == []
    assert len(d.agenda_adiante()) == 1
    for saida in (render_html(d), render_texto(d)):
        assert "Nenhum compromisso nem prazo estimado para hoje" in saida
        assert "sem data confirmada na fonte" in saida


def test_agenda_do_dia_aparece_nas_tres_saidas(dash):
    for saida in (render_html(dash), render_pagina(dash)):
        assert "Agenda do dia" in saida
    assert "AGENDA DO DIA" in render_texto(dash)


# --- Conteúdo e integridade -----------------------------------------------


def test_placar_conta_por_urgencia(dash):
    assert dash.contagem() == {"vermelho": 1, "amarelo": 1, "verde": 1}


def test_urgencia_invalida_e_rejeitada():
    with pytest.raises(ValueError, match="Urgência inválida"):
        Item(urgencia="roxo", titulo="x")


def test_conteudo_e_escapado():
    d = Dashboard(
        data=date(2026, 9, 14),
        resumo="Cliente <script>alert(1)</script> & Cia",
        itens=[Item(urgencia="verde", titulo='Aspas " e < sinais >')],
    )
    html = render_html(d)
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html


def test_dashboard_vazio_mostra_zeros_e_nao_inventa_secao():
    """O placar exibe os três níveis mesmo zerados; seções sem item somem."""
    d = Dashboard(data=date(2026, 9, 14), resumo="Nada hoje.")
    html = render_html(d)
    assert d.contagem() == {"vermelho": 0, "amarelo": 0, "verde": 0}
    # O rótulo aparece no placar, mas nenhum cartão de item foi renderizado.
    assert html.count("AÇÃO IMEDIATA") == 1
    assert "Nenhum compromisso" in html
    assert "Pendentes de conferência" not in html


def test_secao_com_item_ganha_titulo_alem_do_placar(dash):
    html = render_html(dash)
    assert html.count("AÇÃO IMEDIATA") == 2  # placar + título da seção


def test_pagina_e_documento_completo(dash):
    pagina = render_pagina(dash)
    assert pagina.startswith("<!doctype html>")
    assert '<html lang="pt-BR">' in pagina
    assert "<title>" in pagina
    assert 'charset="utf-8"' in pagina


def test_texto_puro_serve_de_alternativa(dash):
    txt = render_texto(dash)
    assert "<" not in txt.replace("<", "", 0) or "<table" not in txt
    assert "DASHBOARD JURÍDICO DIÁRIO" in txt
    assert "Conflito de audiências" in txt
    assert "CONFERIR NO SISTEMA" in txt


def test_data_por_extenso_em_portugues():
    assert data_por_extenso(date(2026, 9, 14)) == "segunda-feira, 14 de setembro de 2026"
    assert data_por_extenso(date(2026, 3, 1)) == "domingo, 1 de março de 2026"


def test_html_e_balanceado(dash):
    """Contagem grosseira de tabelas abertas e fechadas."""
    html = render_html(dash)
    assert len(re.findall(r"<table", html)) == len(re.findall(r"</table>", html))
    assert len(re.findall(r"<td", html)) == len(re.findall(r"</td>", html))
    assert len(re.findall(r"<tr", html)) == len(re.findall(r"</tr>", html))


def test_planilha_e_dashboard_partilham_a_identidade():
    """As cores não podem divergir entre um artefato e outro."""
    from core import planilha

    assert planilha.AZUL_MARINHO == identidade.AZUL_MARINHO.lstrip("#").upper()
    assert planilha.DOURADO == identidade.DOURADO.lstrip("#").upper()
    for nivel in identidade.URGENCIA:
        assert planilha.CORES_URGENCIA[nivel] == \
            identidade.URGENCIA[nivel]["fundo"].lstrip("#").upper()
