"""Renderização do Dashboard Jurídico Diário no padrão visual do escritório.

O dashboard é entregue como rascunho no Gmail, e cliente de e-mail não carrega
folha de estilo externa, não entende flexbox nem grid, e descarta boa parte do
CSS moderno. Por isso a saída aqui é deliberadamente conservadora: tabelas,
estilo em linha, largura fixa de 640px e nenhuma fonte remota.

O mesmo HTML abre bem no navegador e imprime de forma limpa, então serve tanto
para o e-mail quanto para arquivo.

Além do HTML, o módulo produz a versão em texto puro, que vai como alternativa
no mesmo e-mail e é o que aparece na pré-visualização da caixa.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from html import escape

from .identidade import (
    AVISO_ESTIMATIVA,
    AZUL_ESCURO,
    AZUL_MARINHO,
    BRANCO,
    CINZA_BORDA,
    CINZA_TEXTO,
    DOURADO,
    DOURADO_CLARO,
    ESCRITORIO,
    GRAFITE,
    PAPEL,
    SANS,
    SERIFA,
    URGENCIA,
    Escritorio,
)

DIAS_SEMANA = [
    "segunda-feira", "terça-feira", "quarta-feira", "quinta-feira",
    "sexta-feira", "sábado", "domingo",
]
MESES = [
    "janeiro", "fevereiro", "março", "abril", "maio", "junho",
    "julho", "agosto", "setembro", "outubro", "novembro", "dezembro",
]

LARGURA = 640


def data_por_extenso(d: date) -> str:
    return f"{DIAS_SEMANA[d.weekday()]}, {d.day} de {MESES[d.month - 1]} de {d.year}"


# --- Modelo ---------------------------------------------------------------


@dataclass
class Item:
    """Uma linha do dashboard: algo que aconteceu e o que fazer a respeito."""

    urgencia: str                      # vermelho, amarelo ou verde
    titulo: str
    processo: str = ""
    cliente: str = ""
    orgao: str = ""
    o_que_houve: str = ""
    providencia: str = ""
    vencimento_estimado: str = ""      # AAAA-MM-DD
    alerta: str = ""                   # destaque em vermelho dentro do cartão
    fontes: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.urgencia not in URGENCIA:
            raise ValueError(
                f"Urgência inválida: {self.urgencia!r}. Use uma de {sorted(URGENCIA)}."
            )


@dataclass
class Compromisso:
    """Um compromisso da agenda.

    `quando` é o que se lê na tela. `data` é o que a máquina usa para separar o
    que é de hoje do que vem depois, e por isso precisa vir preenchida sempre
    que a fonte informar a data. Compromisso sem `data` nunca é presumido de
    hoje: cai na lista adiante e é contado à parte, para que a omissão apareça.
    """

    quando: str
    titulo: str
    detalhe: str = ""
    alerta: str = ""
    data: date | None = None


@dataclass
class Dashboard:
    """Conteúdo completo de um dashboard diário."""

    data: date
    resumo: str
    itens: list[Item] = field(default_factory=list)
    agenda: list[Compromisso] = field(default_factory=list)
    pendentes_conferencia: list[str] = field(default_factory=list)
    pendencias_sistema: list[str] = field(default_factory=list)
    fontes_varredura: list[str] = field(default_factory=list)
    escritorio: Escritorio = ESCRITORIO

    def por_urgencia(self, nivel: str) -> list[Item]:
        return [i for i in self.itens if i.urgencia == nivel]

    def contagem(self) -> dict[str, int]:
        return {n: len(self.por_urgencia(n)) for n in URGENCIA}

    def agenda_do_dia(self) -> list[Compromisso]:
        """Compromissos cuja data é a do dashboard."""
        return [c for c in self.agenda if c.data == self.data]

    def agenda_adiante(self) -> list[Compromisso]:
        """O resto da janela examinada, inclusive o que veio sem data."""
        return [c for c in self.agenda if c.data != self.data]

    def agenda_sem_data(self) -> list[Compromisso]:
        return [c for c in self.agenda if c.data is None]

    def vencimentos_do_dia(self) -> list[Item]:
        """Itens cujo vencimento estimado cai hoje. Continua sendo estimativa."""
        alvo = self.data.isoformat()
        return [i for i in self.itens if i.vencimento_estimado == alvo]


# --- Auxiliares de marcação ------------------------------------------------


def _e(texto: str) -> str:
    return escape(str(texto), quote=True)


def _linha_dado(rotulo: str, valor: str) -> str:
    if not valor:
        return ""
    return (
        f'<tr>'
        f'<td width="96" style="width:96px;padding:2px 10px 2px 0;'
        f'font:400 12px/1.5 {SANS};color:{CINZA_TEXTO};vertical-align:top;">'
        f'{_e(rotulo)}</td>'
        f'<td style="padding:2px 0;font:400 13px/1.5 {SANS};color:{GRAFITE};">'
        f'{_e(valor)}</td>'
        f'</tr>'
    )


def _cartao_item(item: Item) -> str:
    cor = URGENCIA[item.urgencia]
    dados = "".join([
        _linha_dado("Processo", item.processo),
        _linha_dado("Cliente", item.cliente),
        _linha_dado("Órgão", item.orgao),
        _linha_dado("O que houve", item.o_que_houve),
        _linha_dado("Providência", item.providencia),
    ])

    venc = ""
    if item.vencimento_estimado:
        d = date.fromisoformat(item.vencimento_estimado)
        venc = (
            f'<tr><td colspan="2" style="padding:10px 0 0;">'
            f'<table role="presentation" cellpadding="0" cellspacing="0" border="0">'
            f'<tr>'
            f'<td style="background:{cor["fundo"]};border:1px solid {cor["faixa"]};'
            f'border-radius:3px;padding:6px 10px;font:700 12px/1.2 {SANS};'
            f'color:{cor["texto"]};letter-spacing:.02em;">'
            f'VENCIMENTO ESTIMADO {d:%d/%m/%Y}  ·  CONFERIR NO SISTEMA'
            f'</td></tr></table></td></tr>'
        )

    alerta = ""
    if item.alerta:
        alerta = (
            f'<tr><td colspan="2" style="padding:10px 0 0;">'
            f'<div style="background:#FEF3F2;border-left:3px solid #B42318;'
            f'padding:8px 12px;font:600 12px/1.55 {SANS};color:#7A271A;">'
            f'{_e(item.alerta)}</div></td></tr>'
        )

    fontes = ""
    if item.fontes:
        fontes = (
            f'<tr><td colspan="2" style="padding:10px 0 0;'
            f'font:400 11px/1.5 {SANS};color:{CINZA_TEXTO};">'
            f'Fontes: {_e("  ·  ".join(item.fontes))}</td></tr>'
        )

    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;margin:0 0 12px;">'
        f'<tr>'
        f'<td width="4" style="background:{cor["faixa"]};font-size:0;line-height:0;">&nbsp;</td>'
        f'<td style="background:{BRANCO};border:1px solid {CINZA_BORDA};'
        f'border-left:0;padding:14px 16px;">'
        f'<div style="font:700 15px/1.35 {SERIFA};color:{AZUL_MARINHO};'
        f'margin:0 0 8px;">{_e(item.titulo)}</div>'
        f'<table role="presentation" cellpadding="0" cellspacing="0" border="0" '
        f'width="100%" style="border-collapse:collapse;">'
        f'{dados}{venc}{alerta}{fontes}'
        f'</table>'
        f'</td></tr></table>'
    )


def _titulo_secao(texto: str, cor_faixa: str) -> str:
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;margin:24px 0 10px;">'
        f'<tr>'
        f'<td width="28" style="background:{cor_faixa};height:3px;font-size:0;'
        f'line-height:0;">&nbsp;</td>'
        f'<td style="padding-left:10px;font:700 12px/1.2 {SANS};'
        f'letter-spacing:.10em;color:{cor_faixa};text-transform:uppercase;">'
        f'{_e(texto)}</td>'
        f'</tr></table>'
    )


def _bloco_lista(titulo: str, itens: list[str], cor_borda: str, fundo: str) -> str:
    if not itens:
        return ""
    linhas = "".join(
        f'<li style="margin:0 0 6px;font:400 13px/1.55 {SANS};color:{GRAFITE};">'
        f'{_e(i)}</li>'
        for i in itens
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;margin:0 0 12px;">'
        f'<tr><td style="background:{fundo};border:1px solid {cor_borda};'
        f'padding:14px 16px;">'
        f'<div style="font:700 13px/1.3 {SERIFA};color:{AZUL_MARINHO};'
        f'margin:0 0 8px;">{_e(titulo)}</div>'
        f'<ul style="margin:0;padding-left:18px;">{linhas}</ul>'
        f'</td></tr></table>'
    )


def _linha_agenda(
    quando: str,
    titulo: str,
    detalhe: str = "",
    alerta: str = "",
    cor_quando: str = AZUL_MARINHO,
    ultima: bool = False,
) -> str:
    # A régua da última linha encostaria na borda do cartão, virando linha dupla.
    risco = "none" if ultima else f"1px solid {CINZA_BORDA}"
    bloco_detalhe = (
        f'<div style="margin:3px 0 0;font:400 12px/1.5 {SANS};'
        f'color:{CINZA_TEXTO};">{_e(detalhe)}</div>' if detalhe else ""
    )
    bloco_alerta = (
        f'<div style="margin:6px 0 0;font:600 12px/1.5 {SANS};color:#7A271A;">'
        f'{_e(alerta)}</div>' if alerta else ""
    )
    return (
        f'<tr>'
        f'<td width="120" style="padding:10px 12px 10px 0;font:700 12px/1.4 {SANS};'
        f'color:{cor_quando};vertical-align:top;white-space:nowrap;'
        f'border-bottom:{risco};">{_e(quando)}</td>'
        f'<td style="padding:10px 0;border-bottom:{risco};">'
        f'<div style="font:600 13px/1.4 {SANS};color:{GRAFITE};">{_e(titulo)}</div>'
        f'{bloco_detalhe}{bloco_alerta}</td>'
        f'</tr>'
    )


def _vazio(texto: str) -> str:
    return (
        f'<div style="font:400 13px/1.55 {SANS};color:{CINZA_TEXTO};'
        f'padding:4px 0 8px;">{_e(texto)}</div>'
    )


def _bloco_agenda_do_dia(dash: Dashboard) -> str:
    """Bloco de destaque com o que o dia exige, logo abaixo do resumo.

    Reúne duas coisas que o advogado precisa ver antes de qualquer outra: os
    compromissos marcados para hoje e os prazos cuja estimativa vence hoje.
    Prazo entra sempre com a ressalva de conferência, porque continua sendo
    estimativa mesmo quando cai no dia.
    """
    # (quando, título, detalhe, alerta, cor do rótulo)
    entradas: list[tuple[str, str, str, str, str]] = [
        (c.quando, c.titulo, c.detalhe, c.alerta, AZUL_MARINHO)
        for c in dash.agenda_do_dia()
    ]
    for item in dash.vencimentos_do_dia():
        partes = [p for p in (item.processo, item.providencia) if p]
        entradas.append((
            "Prazo estimado",
            item.titulo,
            "  ·  ".join(partes),
            "Vencimento estimado para hoje. CONFERIR NO SISTEMA.",
            URGENCIA["vermelho"]["faixa"],
        ))

    linhas = [
        _linha_agenda(*e, ultima=(n == len(entradas) - 1))
        for n, e in enumerate(entradas)
    ]

    if linhas:
        miolo = (
            f'<table role="presentation" width="100%" cellpadding="0" '
            f'cellspacing="0" border="0" style="border-collapse:collapse;">'
            f'{"".join(linhas)}</table>'
        )
    else:
        miolo = _vazio("Nenhum compromisso nem prazo estimado para hoje.")

    sem_data = len(dash.agenda_sem_data())
    if sem_data:
        plural = "s" if sem_data > 1 else ""
        miolo += (
            f'<div style="margin:8px 0 0;font:400 11px/1.5 {SANS};'
            f'color:{CINZA_TEXTO};">{sem_data} compromisso{plural} sem data '
            f'confirmada na fonte. Aparece{"m" if sem_data > 1 else ""} apenas '
            f'em Próximos compromissos, e não foi presumido de hoje.</div>'
        )

    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;margin:0 0 6px;">'
        f'<tr><td style="background:{AZUL_MARINHO};padding:11px 16px 10px;">'
        f'<div style="font:700 12px/1.2 {SANS};letter-spacing:.14em;'
        f'color:{DOURADO_CLARO};text-transform:uppercase;">Agenda do dia</div>'
        f'<div style="margin:4px 0 0;font:400 12px/1.4 {SANS};color:{BRANCO};">'
        f'{_e(data_por_extenso(dash.data))}</div>'
        f'</td></tr>'
        f'<tr><td style="background:{DOURADO};height:2px;font-size:0;'
        f'line-height:0;">&nbsp;</td></tr>'
        f'<tr><td style="background:{BRANCO};border:1px solid {CINZA_BORDA};'
        f'border-top:0;padding:6px 16px 12px;">{miolo}</td></tr>'
        f'</table>'
    )


def _bloco_agenda(compromissos: list[Compromisso]) -> str:
    if not compromissos:
        return _vazio("Nenhum compromisso na janela examinada.")
    linhas = "".join(
        _linha_agenda(c.quando, c.titulo, c.detalhe, c.alerta,
                      ultima=(n == len(compromissos) - 1))
        for n, c in enumerate(compromissos)
    )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;background:{BRANCO};'
        f'border:1px solid {CINZA_BORDA};padding:0 16px;">'
        f'{linhas}</table>'
    )


def _placar(dash: Dashboard) -> str:
    celulas = []
    for nivel in ("vermelho", "amarelo", "verde"):
        cor = URGENCIA[nivel]
        n = len(dash.por_urgencia(nivel))
        celulas.append(
            f'<td width="33%" style="padding:0 4px;">'
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" style="border-collapse:collapse;background:{cor["fundo"]};'
            f'border:1px solid {cor["faixa"]};">'
            f'<tr><td align="center" style="padding:12px 8px;">'
            f'<div style="font:700 26px/1 {SERIFA};color:{cor["faixa"]};">{n}</div>'
            f'<div style="margin:5px 0 0;font:700 10px/1.3 {SANS};'
            f'letter-spacing:.08em;color:{cor["texto"]};">{cor["rotulo"]}</div>'
            f'</td></tr></table></td>'
        )
    return (
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;margin:0 -4px 18px;">'
        f'<tr>{"".join(celulas)}</tr></table>'
    )


# --- Renderização ----------------------------------------------------------


def render_html(dash: Dashboard) -> str:
    """HTML completo, seguro para cliente de e-mail e para o navegador."""
    esc = dash.escritorio
    corpo: list[str] = []

    # Cabeçalho institucional
    corpo.append(
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;">'
        f'<tr><td style="background:{AZUL_MARINHO};padding:26px 28px 22px;">'
        f'<div style="font:400 11px/1.3 {SANS};letter-spacing:.20em;'
        f'color:{DOURADO_CLARO};text-transform:uppercase;">{_e(esc.nome)}</div>'
        f'<div style="margin:10px 0 0;font:700 25px/1.2 {SERIFA};color:{BRANCO};">'
        f'Dashboard Jurídico Diário</div>'
        f'<div style="margin:6px 0 0;font:400 13px/1.4 {SANS};color:{DOURADO_CLARO};">'
        f'{_e(data_por_extenso(dash.data))}</div>'
        f'</td></tr>'
        f'<tr><td style="background:{DOURADO};height:3px;font-size:0;line-height:0;">'
        f'&nbsp;</td></tr></table>'
    )

    corpo.append('<table role="presentation" width="100%" cellpadding="0" '
                 'cellspacing="0" border="0" style="border-collapse:collapse;">'
                 f'<tr><td style="background:{PAPEL};padding:22px 28px 8px;">')

    corpo.append(_placar(dash))

    if dash.resumo:
        corpo.append(
            f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
            f'border="0" style="border-collapse:collapse;margin:0 0 6px;">'
            f'<tr><td style="background:{BRANCO};border:1px solid {CINZA_BORDA};'
            f'border-top:3px solid {AZUL_MARINHO};padding:16px 18px;'
            f'font:400 14px/1.65 {SERIFA};color:{GRAFITE};">{_e(dash.resumo)}</td>'
            f'</tr></table>'
        )

    # A agenda do dia vem antes dos cartões: é o que decide a manhã.
    corpo.append(_bloco_agenda_do_dia(dash))

    for nivel in ("vermelho", "amarelo", "verde"):
        itens = dash.por_urgencia(nivel)
        if not itens:
            continue
        corpo.append(_titulo_secao(URGENCIA[nivel]["rotulo"], URGENCIA[nivel]["faixa"]))
        corpo.extend(_cartao_item(i) for i in itens)

    corpo.append(_titulo_secao("Próximos compromissos", AZUL_MARINHO))
    corpo.append(_bloco_agenda(dash.agenda_adiante()))

    if dash.pendentes_conferencia:
        corpo.append(_titulo_secao("Pendentes de conferência", DOURADO))
        corpo.append(_bloco_lista(
            "Prazos estimados ainda não validados por humano",
            dash.pendentes_conferencia, DOURADO, "#FDFAF3",
        ))

    if dash.pendencias_sistema:
        corpo.append(_titulo_secao("Pendências do sistema", CINZA_TEXTO))
        corpo.append(_bloco_lista(
            "O que ainda falta para o sistema cobrir o acervo inteiro",
            dash.pendencias_sistema, CINZA_BORDA, BRANCO,
        ))

    corpo.append('</td></tr></table>')

    # Ressalva e rodapé
    contatos = esc.rodape_contatos()
    linha_contatos = (
        f'<div style="margin:8px 0 0;font:400 11px/1.6 {SANS};color:{DOURADO_CLARO};">'
        f'{_e(contatos)}</div>' if contatos else ""
    )
    fontes = (
        f'<div style="margin:10px 0 0;font:400 11px/1.6 {SANS};color:#8A96A8;">'
        f'Fontes desta varredura: {_e("; ".join(dash.fontes_varredura))}.</div>'
        if dash.fontes_varredura else ""
    )
    corpo.append(
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;">'
        f'<tr><td style="background:{PAPEL};padding:6px 28px 22px;">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;">'
        f'<tr><td style="background:#FFFBEB;border:1px solid {DOURADO};'
        f'padding:12px 16px;font:700 12px/1.6 {SANS};color:#7A2E0E;">'
        f'{_e(AVISO_ESTIMATIVA)}</td></tr></table></td></tr>'
        f'<tr><td style="background:{AZUL_ESCURO};padding:18px 28px 22px;">'
        f'<div style="font:700 13px/1.4 {SERIFA};color:{BRANCO};">'
        f'{_e(esc.advogado)}</div>'
        f'<div style="margin:2px 0 0;font:400 12px/1.4 {SANS};color:{DOURADO};">'
        f'{_e(esc.oab)}</div>'
        f'{linha_contatos}{fontes}'
        f'</td></tr></table>'
    )

    interno = "".join(corpo)
    return (
        f'<div style="margin:0;padding:0;background:{PAPEL};">'
        f'<table role="presentation" width="100%" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;background:{PAPEL};">'
        f'<tr><td align="center" style="padding:16px 8px;">'
        f'<table role="presentation" width="{LARGURA}" cellpadding="0" cellspacing="0" '
        f'border="0" style="border-collapse:collapse;width:{LARGURA}px;max-width:100%;'
        f'background:{PAPEL};">'
        f'<tr><td>{interno}</td></tr>'
        f'</table></td></tr></table></div>'
    )


def render_pagina(dash: Dashboard) -> str:
    """Documento HTML completo, para salvar em arquivo ou imprimir."""
    titulo = f"Dashboard Jurídico — {dash.data:%d/%m/%Y}"
    return (
        '<!doctype html>\n<html lang="pt-BR">\n<head>\n'
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_e(titulo)}</title>\n'
        # Só a página autônoma usa media query. O corpo do e-mail não pode,
        # porque cliente de e-mail costuma descartar o bloco <style>.
        '<style>@page{margin:12mm}'
        'body{margin:0}'
        '@media (max-width:680px){table[width="640"]{width:100%!important}}'
        '@media print{body{background:#fff}}</style>\n'
        f'</head>\n<body style="margin:0;background:{PAPEL};">\n'
        f'{render_html(dash)}\n</body>\n</html>\n'
    )


def render_texto(dash: Dashboard) -> str:
    """Versão em texto puro, alternativa do e-mail e pré-visualização da caixa."""
    esc = dash.escritorio
    l: list[str] = [
        f"DASHBOARD JURÍDICO DIÁRIO — {data_por_extenso(dash.data)}",
        esc.nome,
        "",
    ]
    c = dash.contagem()
    l.append(
        f"Ação imediata: {c['vermelho']}  |  Esta semana: {c['amarelo']}  |  "
        f"Acompanhamento: {c['verde']}"
    )
    l += ["", dash.resumo, ""]

    l += ["=" * 62, f"AGENDA DO DIA — {data_por_extenso(dash.data)}", "=" * 62, ""]
    do_dia = dash.agenda_do_dia()
    vencendo = dash.vencimentos_do_dia()
    for comp in do_dia:
        l.append(f"{comp.quando} — {comp.titulo}")
        if comp.detalhe:
            l.append(f"   {comp.detalhe}")
        if comp.alerta:
            l.append(f"   ATENÇÃO: {comp.alerta}")
        l.append("")
    for item in vencendo:
        l.append(f"Prazo estimado — {item.titulo}")
        if item.processo:
            l.append(f"   Processo: {item.processo}")
        if item.providencia:
            l.append(f"   Providência: {item.providencia}")
        l.append("   Vencimento estimado para hoje. CONFERIR NO SISTEMA.")
        l.append("")
    if not do_dia and not vencendo:
        l += ["Nenhum compromisso nem prazo estimado para hoje.", ""]
    sem_data = len(dash.agenda_sem_data())
    if sem_data:
        plural = "s" if sem_data > 1 else ""
        l += [
            f"{sem_data} compromisso{plural} sem data confirmada na fonte, "
            f"listado{plural} apenas em Próximos compromissos.",
            "",
        ]

    for nivel in ("vermelho", "amarelo", "verde"):
        itens = dash.por_urgencia(nivel)
        if not itens:
            continue
        l += ["=" * 62, URGENCIA[nivel]["rotulo"], "=" * 62, ""]
        for item in itens:
            l.append(item.titulo)
            for rotulo, valor in (
                ("Processo", item.processo), ("Cliente", item.cliente),
                ("Órgão", item.orgao), ("O que houve", item.o_que_houve),
                ("Providência", item.providencia),
            ):
                if valor:
                    l.append(f"   {rotulo}: {valor}")
            if item.vencimento_estimado:
                d = date.fromisoformat(item.vencimento_estimado)
                l.append(f"   VENCIMENTO ESTIMADO: {d:%d/%m/%Y} — CONFERIR NO SISTEMA")
            if item.alerta:
                l.append(f"   ATENÇÃO: {item.alerta}")
            if item.fontes:
                l.append(f"   Fontes: {'  ·  '.join(item.fontes)}")
            l.append("")

    l += ["=" * 62, "PRÓXIMOS COMPROMISSOS", "=" * 62, ""]
    adiante = dash.agenda_adiante()
    if adiante:
        for comp in adiante:
            l.append(f"{comp.quando} — {comp.titulo}")
            if comp.detalhe:
                l.append(f"   {comp.detalhe}")
            if comp.alerta:
                l.append(f"   ATENÇÃO: {comp.alerta}")
            l.append("")
    else:
        l += ["Nenhum compromisso na janela examinada.", ""]

    for titulo, itens in (
        ("PENDENTES DE CONFERÊNCIA", dash.pendentes_conferencia),
        ("PENDÊNCIAS DO SISTEMA", dash.pendencias_sistema),
    ):
        if itens:
            l += ["=" * 62, titulo, "=" * 62, ""]
            l += [f"- {i}" for i in itens]
            l.append("")

    l += ["=" * 62, "", AVISO_ESTIMATIVA, "", f"{esc.advogado}", esc.oab]
    contatos = esc.rodape_contatos()
    if contatos:
        l.append(contatos)
    if dash.fontes_varredura:
        l += ["", f"Fontes desta varredura: {'; '.join(dash.fontes_varredura)}."]
    return "\n".join(l)
