"""Planilha viva de controle processual.

Gera um .xlsx a partir do acervo, com cinco abas: Acervo, Prazos, Audiências,
Movimentações e Conferência. A aba Conferência isola justamente o que ainda não
foi validado por humano, para que nenhuma estimativa passe despercebida.

Feita para ser manuseada, não só lida: datas gravadas como data (ordenam e
filtram como data, em qualquer aba), filtro ligado em todo cabeçalho, número do
processo congelado à esquerda e impressão em paisagem numa página de largura.

Identidade visual: azul-marinho e dourado do escritório Tiago Neves.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from openpyxl.worksheet.properties import PageSetupProperties
from openpyxl.worksheet.worksheet import Worksheet

from .acervo import Acervo, classificar_urgencia
from .prazos import rotulo_regime, rotulo_termo
from . import identidade

# openpyxl quer a cor sem o "#". A identidade do escritório vive em
# core/identidade.py; aqui só se converte o formato.
def _hex(cor: str) -> str:
    return cor.lstrip("#").upper()


AZUL_MARINHO = _hex(identidade.AZUL_MARINHO)
DOURADO = _hex(identidade.DOURADO)
BRANCO = _hex(identidade.BRANCO)
CINZA_CLARO = _hex(identidade.PAPEL)

CORES_URGENCIA = {
    nivel: _hex(cores["fundo"]) for nivel, cores in identidade.URGENCIA.items()
}

BORDA = Border(*(Side(style="thin", color="D0D5DD"),) * 4)

# Código de formato do Excel, que o Google Planilhas também entende. Com a data
# gravada como data, a coluna ordena em ordem cronológica e aceita filtro por
# período. Gravada como texto, "01/12/2026" vinha antes de "10/11/2026".
FORMATO_DATA = "DD/MM/YYYY"


def _data(iso: str) -> date | str:
    """Converte AAAA-MM-DD em data. Valor fora do padrão segue como texto,
    visível, em vez de derrubar a geração da planilha inteira."""
    try:
        return date.fromisoformat(iso)
    except (TypeError, ValueError):
        return iso or ""


def _formatar_datas(ws: Worksheet, colunas: tuple[int, ...]) -> None:
    """Aplica o formato de data à última linha escrita, nas colunas indicadas."""
    for col in colunas:
        celula = ws.cell(row=ws.max_row, column=col)
        if isinstance(celula.value, date):
            celula.number_format = FORMATO_DATA


def _cabecalho(ws: Worksheet, colunas: list[str], larguras: list[int]) -> None:
    ws.append(colunas)
    for idx, (titulo, largura) in enumerate(zip(colunas, larguras), start=1):
        celula = ws.cell(row=1, column=idx)
        celula.font = Font(name="Calibri", size=11, bold=True, color=BRANCO)
        celula.fill = PatternFill("solid", fgColor=AZUL_MARINHO)
        celula.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        celula.border = BORDA
        ws.column_dimensions[get_column_letter(idx)].width = largura
    ws.row_dimensions[1].height = 30


def _estilizar_corpo(ws: Worksheet, primeira_linha: int = 2) -> None:
    for linha in ws.iter_rows(min_row=primeira_linha):
        for celula in linha:
            celula.border = BORDA
            celula.alignment = Alignment(vertical="top", wrap_text=True)


def _preparar_manuseio(
    ws: Worksheet,
    linha_cabecalho: int,
    congelar: str,
    ultima_coluna: int,
) -> None:
    """Filtro no cabeçalho, painéis congelados e impressão legível.

    `congelar` é a primeira célula que rola: "E2" mantém fixas a linha do
    cabeçalho e as quatro primeiras colunas, entre elas o número do processo.
    """
    ultima_linha = max(ws.max_row, linha_cabecalho + 1)
    letra = get_column_letter(ultima_coluna)
    ws.auto_filter.ref = f"A{linha_cabecalho}:{letra}{ultima_linha}"
    ws.freeze_panes = congelar
    ws.page_setup.orientation = "landscape"
    ws.page_setup.paperSize = ws.PAPERSIZE_A4
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr = PageSetupProperties(fitToPage=True)
    ws.print_title_rows = f"{linha_cabecalho}:{linha_cabecalho}"


def _aba_acervo(wb: Workbook, acervo: Acervo, hoje: date) -> None:
    ws = wb.active
    ws.title = "Acervo"
    colunas = ["Nº CNJ", "Cliente", "Polo", "Parte contrária", "Órgão", "Classe",
               "Assunto", "Situação", "Prazos abertos", "Próximo vencimento"]
    _cabecalho(ws, colunas, [24, 26, 10, 26, 30, 22, 30, 12, 14, 18])
    for proc in sorted(acervo.processos.values(), key=lambda p: p.numero):
        prox = proc.proximo_vencimento()
        ws.append([
            proc.numero, proc.cliente, proc.polo, proc.parte_contraria, proc.orgao,
            proc.classe, proc.assunto, proc.situacao, len(proc.prazos_abertos()),
            _data(prox) if prox else "",
        ])
        _formatar_datas(ws, (10,))
        if prox:
            cor = CORES_URGENCIA[classificar_urgencia(prox, hoje)]
            ws.cell(row=ws.max_row, column=10).fill = PatternFill("solid", fgColor=cor)
    _estilizar_corpo(ws)
    _preparar_manuseio(ws, 1, "B2", len(colunas))


def _aba_prazos(wb: Workbook, acervo: Acervo, hoje: date) -> None:
    ws = wb.create_sheet("Prazos")
    # A contagem de dias é fotografia do dia da geração. O cabeçalho diz de que
    # dia, para que a planilha aberta dias depois não engane.
    colunas = ["Urgência", "Vencimento estimado", f"Dias restantes (em {hoje:%d/%m/%Y})",
               "Nº CNJ", "Cliente", "Providência", "Evento", "Termo inicial", "Regime",
               "Dias", "Conferido?", "Avisos"]
    _cabecalho(ws, colunas, [12, 18, 16, 24, 24, 34, 14, 24, 18, 8, 12, 46])
    for proc, prz in acervo.prazos_ate(date(hoje.year + 5, 12, 31)):
        urgencia = classificar_urgencia(prz.vencimento_estimado, hoje)
        faltam = (date.fromisoformat(prz.vencimento_estimado) - hoje).days
        ws.append([
            {"vermelho": "VERMELHO", "amarelo": "AMARELO", "verde": "VERDE"}[urgencia],
            _data(prz.vencimento_estimado), faltam, proc.numero, proc.cliente,
            prz.descricao, _data(prz.evento), rotulo_termo(prz.termo_inicial),
            rotulo_regime(prz.regime), prz.dias,
            "SIM" if prz.conferido_por_humano else "NÃO",
            " | ".join(prz.avisos),
        ])
        _formatar_datas(ws, (2, 7))
        fill = PatternFill("solid", fgColor=CORES_URGENCIA[urgencia])
        for col in (1, 2, 3):
            ws.cell(row=ws.max_row, column=col).fill = fill
        if not prz.conferido_por_humano:
            c = ws.cell(row=ws.max_row, column=11)
            c.font = Font(bold=True, color="B42318")
    _estilizar_corpo(ws)
    _preparar_manuseio(ws, 1, "E2", len(colunas))


def _aba_audiencias(wb: Workbook, acervo: Acervo, hoje: date) -> None:
    ws = wb.create_sheet("Audiências")
    colunas = ["Data", "Hora", f"Dias restantes (em {hoje:%d/%m/%Y})", "Nº CNJ",
               "Cliente", "Tipo", "Local", "Modalidade", "Confirmada?", "Observações"]
    _cabecalho(ws, colunas, [13, 9, 16, 24, 26, 20, 40, 15, 13, 34])
    for proc, aud in acervo.audiencias_ate(date(hoje.year + 5, 12, 31), hoje=hoje):
        faltam = (date.fromisoformat(aud.data) - hoje).days
        ws.append([
            _data(aud.data), aud.hora, faltam,
            proc.numero, proc.cliente, aud.tipo, aud.local, aud.modalidade,
            "SIM" if aud.confirmada_por_humano else "NÃO", aud.observacoes,
        ])
        _formatar_datas(ws, (1,))
        cor = CORES_URGENCIA["vermelho" if faltam <= 7 else "amarelo" if faltam <= 30 else "verde"]
        for col in (1, 2, 3):
            ws.cell(row=ws.max_row, column=col).fill = PatternFill("solid", fgColor=cor)
        if not aud.confirmada_por_humano:
            ws.cell(row=ws.max_row, column=9).font = Font(bold=True, color="B42318")
    if ws.max_row == 1:
        ws.cell(row=2, column=1, value="Nenhuma audiência designada no acervo.")
    _estilizar_corpo(ws)
    _preparar_manuseio(ws, 1, "E2", len(colunas))


def _aba_movimentacoes(wb: Workbook, acervo: Acervo) -> None:
    ws = wb.create_sheet("Movimentações")
    colunas = ["Data", "Nº CNJ", "Cliente", "Fonte", "Descrição"]
    _cabecalho(ws, colunas, [14, 24, 24, 12, 70])
    linhas = [
        (m.data, p.numero, p.cliente, m.fonte, m.descricao)
        for p in acervo.processos.values()
        for m in p.movimentos
    ]
    # Ordena pelo texto ISO (cronológico) antes de converter em data.
    for linha in sorted(linhas, reverse=True):
        ws.append([_data(linha[0]), *linha[1:]])
        _formatar_datas(ws, (1,))
    _estilizar_corpo(ws)
    _preparar_manuseio(ws, 1, "C2", len(colunas))


def _aba_conferencia(wb: Workbook, acervo: Acervo) -> None:
    ws = wb.create_sheet("Conferência")
    ws["A1"] = "PRAZOS ESTIMADOS PENDENTES DE CONFERÊNCIA HUMANA"
    ws["A1"].font = Font(name="Calibri", size=13, bold=True, color=AZUL_MARINHO)
    ws["A2"] = (
        "Toda data desta planilha é estimativa produzida por automação. A contagem "
        "definitiva depende de conferência no sistema do tribunal. Enquanto a coluna "
        "\"Conferido?\" estiver como NÃO, o prazo não deve ser tratado como certo."
    )
    ws["A2"].alignment = Alignment(wrap_text=True, vertical="top")
    ws.merge_cells("A2:F2")
    ws.row_dimensions[2].height = 46
    ws["A4"] = "Nº CNJ"
    ws["B4"] = "Cliente"
    ws["C4"] = "Providência"
    ws["D4"] = "Vencimento estimado"
    ws["E4"] = "Base legal aplicada"
    ws["F4"] = "Avisos"
    for col, largura in zip("ABCDEF", [24, 24, 34, 18, 60, 50]):
        c = ws[f"{col}4"]
        c.font = Font(bold=True, color=BRANCO)
        c.fill = PatternFill("solid", fgColor=DOURADO)
        c.alignment = Alignment(horizontal="center", wrap_text=True)
        ws.column_dimensions[col].width = largura
    linha = 5
    for proc, prz in acervo.nao_conferidos():
        ws.cell(row=linha, column=1, value=proc.numero)
        ws.cell(row=linha, column=2, value=proc.cliente)
        ws.cell(row=linha, column=3, value=prz.descricao)
        venc = ws.cell(row=linha, column=4, value=_data(prz.vencimento_estimado))
        if isinstance(venc.value, date):
            venc.number_format = FORMATO_DATA
        ws.cell(row=linha, column=5, value="\n".join(prz.base_legal))
        ws.cell(row=linha, column=6, value="\n".join(prz.avisos))
        linha += 1
    if linha > 5:
        _estilizar_corpo(ws, primeira_linha=5)
    else:
        ws.cell(row=5, column=1, value="Nenhum prazo pendente de conferência.")
    _preparar_manuseio(ws, 4, "B5", 6)


def gerar(
    acervo: Acervo,
    destino: Path | str,
    hoje: date | None = None,
) -> Path:
    """Escreve a planilha de controle processual e devolve o caminho gerado."""
    ref = hoje or date.today()
    wb = Workbook()
    _aba_acervo(wb, acervo, ref)
    _aba_prazos(wb, acervo, ref)
    _aba_audiencias(wb, acervo, ref)
    _aba_movimentacoes(wb, acervo)
    _aba_conferencia(wb, acervo)
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    wb.save(caminho)
    return caminho
