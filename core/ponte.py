"""Ponte entre o sistema e as centrais HTML do kit do notebook.

As duas centrais do kit (`central_automacao_tnadv.html` e
`central_multi_ia_mobile_tnadv.html`) são páginas soltas, abertas do disco
(endereço file://). Página aberta assim não consegue ler um arquivo JSON vizinho,
porque o navegador bloqueia, mas carrega normalmente um <script src> local. Por
isso a ponte entrega os dados do sistema como um arquivo .js que define
`window.TNADV_DADOS`, e cada central ganha um bloco de quatro linhas antes de
</body>, delimitado por marcadores, que liga a página ao sistema.

O que passa pela ponte:

- os calendários forenses do sistema (`core/calendarios`), para que a
  calculadora da central de automação conte com os feriados conferidos do juízo
  certo, e não com uma lista fixa de um só tribunal e de um só ano;
- agenda e prazos do acervo (`data/acervo.json`), quando houver acervo;
- os caminhos entre as páginas, para a barra de navegação comum.

Sigilo: nada aqui grava dado de cliente no repositório. O arquivo de dados é
escrito só na pasta do kit, no computador do advogado. Por padrão vai o mínimo
(número CNJ, órgão, datas, providência); nome de cliente, local e observações
da audiência só entram com `completo=True`, por decisão expressa.
"""

from __future__ import annotations

import codecs
import json
import os
import re
import shutil
import tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

from .acervo import Acervo, classificar_urgencia
from .feriados import CALENDARIOS_DIR, Calendario
from .identidade import AVISO_ESTIMATIVA, ESCRITORIO
from .prazos import rotulo_regime

RAIZ = Path(__file__).resolve().parent.parent
ASSETS = RAIZ / "centrais"

PAGINAS = {
    "automacao": "central_automacao_tnadv.html",
    "multi_ia": "central_multi_ia_mobile_tnadv.html",
}
PASTA_PONTE = "tnadv_ponte"
ARQUIVO_DADOS = "tnadv_dados.js"
ARQUIVOS_FIXOS = ("tnadv_ponte.js", "tnadv_ponte.css")
PAINEL = "PAINEL_TNADV.html"
SUFIXO_BACKUP = ".antes-da-ponte.html"

MARCA_INICIO = "<!-- TNADV-PONTE:INICIO"
MARCA_FIM = "<!-- TNADV-PONTE:FIM -->"
_BLOCO = re.compile(re.escape(MARCA_INICIO) + r".*?" + re.escape(MARCA_FIM) + r"\r?\n?", re.S)

VERSAO_DADOS = 1


# --- Dados ----------------------------------------------------------------


def _dias_do_ano(ano: int):
    d = date(ano, 1, 1)
    while d.year == ano:
        yield d
        d += timedelta(days=1)


def calendarios_para_ponte(hoje: date, anos: tuple[int, ...] | None = None) -> list[dict]:
    """Dias úteis perdidos (de segunda a sexta) de cada calendário do sistema.

    Fim de semana fica de fora: toda calculadora já o descarta. Entra o motivo
    de cada dia, com a base que o próprio motor de prazos registra, e entram os
    avisos do calendário, inclusive o de ano sem feriado local cadastrado.
    """
    anos = anos or (hoje.year, hoje.year + 1)
    saida = []
    for arquivo in sorted(CALENDARIOS_DIR.glob("*.json")):
        if arquivo.stem.startswith("MODELO"):
            continue
        cal = Calendario.carregar(arquivo.stem)
        nao_uteis: dict[str, str] = {}
        reduzidos: dict[str, str] = {}
        for ano in anos:
            for dia in _dias_do_ano(ano):
                if dia.weekday() >= 5:
                    continue
                motivo = cal.motivo_nao_util(dia)
                if motivo:
                    nao_uteis[dia.isoformat()] = motivo
                    continue
                reduzido = cal.motivo_expediente_reduzido(dia)
                if reduzido:
                    reduzidos[dia.isoformat()] = reduzido
        avisos: list[str] = []
        for ano in anos:
            for aviso in cal.avisos(ano):
                if aviso not in avisos:
                    avisos.append(aviso)
        # Alerta é o que muda a confiança no cálculo (não confirmado, ano sem
        # feriado local). Fonte e observações são consulta: a central as mostra
        # recolhidas, para não empurrar o formulário para baixo no celular.
        alertas = [a for a in avisos
                   if not a.startswith("Fonte do calendário") and a != cal.observacoes]
        saida.append({
            "chave": arquivo.stem,
            "nome": cal.nome,
            "confirmado": cal.confirmado,
            "fonte": cal.fonte,
            "consultado_em": cal.consultado_em,
            "observacoes": cal.observacoes,
            "anos": list(anos),
            "anos_cobertos": sorted(cal.anos_cobertos()),
            "nao_uteis": nao_uteis,
            "expediente_reduzido": reduzidos,
            "avisos": avisos,
            "alertas": alertas,
        })
    # Confirmados primeiro: são os que devem ser escolhidos na calculadora.
    saida.sort(key=lambda c: (not c["confirmado"], c["nome"]))
    return saida


def acervo_para_ponte(
    acervo: Acervo,
    hoje: date,
    completo: bool = False,
    janela_dias: int = 60,
) -> dict:
    """Agenda e prazos em aberto do acervo, no formato que as páginas leem."""
    limite = hoje + timedelta(days=janela_dias)
    agenda = []
    for proc, aud in acervo.audiencias_ate(limite, hoje=hoje):
        linha = {
            "data": aud.data,
            "hora": aud.hora,
            "cnj": proc.numero,
            "orgao": proc.orgao,
            "tipo": aud.tipo,
            "modalidade": aud.modalidade,
            "confirmada": aud.confirmada_por_humano,
        }
        if completo:
            linha.update(cliente=proc.cliente, local=aud.local, observacoes=aud.observacoes)
        agenda.append(linha)

    prazos = []
    contagem = {"vermelho": 0, "amarelo": 0, "verde": 0}
    # Vencido também aparece: prazo vencido e não baixado é o que mais importa.
    for proc, prz in acervo.prazos_ate(limite):
        urgencia = classificar_urgencia(prz.vencimento_estimado, hoje)
        contagem[urgencia] += 1
        linha = {
            "vencimento": prz.vencimento_estimado,
            "dias_restantes": (date.fromisoformat(prz.vencimento_estimado) - hoje).days,
            "urgencia": urgencia,
            "cnj": proc.numero,
            "orgao": proc.orgao,
            "providencia": prz.descricao,
            "regime": rotulo_regime(prz.regime),
            "conferido": prz.conferido_por_humano,
        }
        if completo:
            linha["cliente"] = proc.cliente
        prazos.append(linha)

    return {
        # Ausente (arquivo não existe onde o conector rodou) é diferente de
        # vazio (existe, sem processos). A central diz qual dos dois.
        "encontrado": acervo.encontrado,
        "disponivel": bool(acervo.processos),
        "atualizado_em": acervo.atualizado_em,
        "processos": len(acervo.processos),
        "janela_dias": janela_dias,
        "agenda": agenda,
        "prazos": prazos,
        "contagem": contagem,
        "nao_conferidos": len(acervo.nao_conferidos()),
        "completo": completo,
    }


def montar_dados(
    hoje: date,
    acervo: Acervo | None = None,
    completo: bool = False,
    paginas: dict[str, str] | None = None,
    planilha: str | None = None,
    agora: datetime | None = None,
) -> dict:
    """Conteúdo completo de `tnadv_dados.js`.

    `paginas` e `planilha` são caminhos relativos à pasta do kit, com barra
    normal, prontos para virar link.
    """
    momento = agora or datetime.now()
    return {
        "versao": VERSAO_DADOS,
        "gerado_em": momento.isoformat(timespec="seconds"),
        "hoje": hoje.isoformat(),
        "aviso_estimativa": AVISO_ESTIMATIVA,
        "escritorio": {
            "nome": ESCRITORIO.nome,
            "advogado": ESCRITORIO.advogado,
            "oab": ESCRITORIO.oab,
        },
        "paginas": dict(paginas or {}),
        "planilha": planilha,
        "calendarios": calendarios_para_ponte(hoje),
        "acervo": acervo_para_ponte(acervo or Acervo(), hoje, completo=completo),
    }


def dados_para_js(dados: dict) -> str:
    """Serializa os dados como script que define `window.TNADV_DADOS`.

    "</" vira "<\\/" para que nenhum texto do acervo feche a tag <script>, e os
    separadores de linha U+2028 e U+2029 vão escapados, porque navegador antigo
    os recusa dentro de string JavaScript.
    """
    payload = json.dumps(dados, ensure_ascii=False, indent=1, sort_keys=True)
    payload = (
        payload.replace("</", "<\\/")
        .replace(" ", "\\u2028")
        .replace(" ", "\\u2029")
    )
    return (
        "/* Gerado por tools/conectar_centrais.py em "
        f"{dados.get('gerado_em', '')}. Não edite: rode o conector de novo. */\n"
        f"window.TNADV_DADOS = {payload};\n"
    )


# --- Ligação nas páginas ---------------------------------------------------


def bloco_ponte(prefixo: str, pagina: str, quebra: str = "\n") -> str:
    """Bloco inserido antes de </body>.

    `prefixo` é o caminho da página até a pasta do kit ("" ou "../"), com barra
    normal, que é o que o navegador entende em endereço file://.
    """
    base = f"{prefixo}{PASTA_PONTE}/"
    linhas = [
        f"{MARCA_INICIO} ligado por tools/conectar_centrais.py. Para desligar, "
        f"apague deste marcador até TNADV-PONTE:FIM, ou rode o conector com "
        f"--desconectar. -->",
        f'<link rel="stylesheet" href="{base}tnadv_ponte.css">',
        f'<script src="{base}{ARQUIVO_DADOS}"></script>',
        f'<script src="{base}tnadv_ponte.js" data-pagina="{pagina}" '
        f'data-raiz="{prefixo}"></script>',
        MARCA_FIM,
    ]
    return quebra.join(linhas) + quebra


def remover_ponte(html: str) -> str:
    """Tira o bloco da ponte, devolvendo a página como era antes."""
    return _BLOCO.sub("", html)


def inserir_ponte(html: str, prefixo: str, pagina: str) -> str:
    """Liga a página ao sistema. Rodar duas vezes dá o mesmo resultado."""
    limpo = remover_ponte(html)
    posicao = limpo.lower().rfind("</body>")
    if posicao == -1:
        raise ValueError("Página sem </body>: não há onde ligar a ponte.")
    quebra = "\r\n" if "\r\n" in limpo else "\n"
    return limpo[:posicao] + bloco_ponte(prefixo, pagina, quebra) + limpo[posicao:]


def esta_ligada(html: str) -> bool:
    return bool(_BLOCO.search(html))


# --- Pastas ----------------------------------------------------------------


def em_pasta_temporaria(caminho: Path) -> bool:
    """Pasta que o Windows apaga sozinho não serve de destino.

    Inclui a pasta temporária do sistema e as pastas que o Explorador cria ao
    abrir um arquivo de dentro de um .zip sem extrair (nome terminado em
    ".zip" seguido de sufixo, como "Kit.zip.ec6").
    """
    alvo = caminho.resolve()
    temp = Path(tempfile.gettempdir()).resolve()
    if alvo == temp or temp in alvo.parents:
        return True
    partes = [p.lower() for p in alvo.parts]
    if "appdata" in partes and "temp" in partes:
        return True
    return any(re.search(r"\.zip(\.[^\\/]*)?$", p) for p in partes)


def localizar_centrais(kit: Path, profundidade: int = 3) -> dict[str, Path]:
    """As centrais encontradas na pasta do kit, a mais rasa de cada tipo.

    Busca nível a nível e para em `profundidade`, para não varrer a Área de
    Trabalho inteira se a pasta indicada for grande.
    """
    nomes = {nome: chave for chave, nome in PAGINAS.items()}
    achadas: dict[str, Path] = {}
    nivel = [Path(kit)]
    for _ in range(profundidade):
        proximo: list[Path] = []
        for pasta in nivel:
            try:
                itens = sorted(pasta.iterdir())
            except OSError:
                continue
            for item in itens:
                if item.is_dir():
                    if item.name != PASTA_PONTE and not item.name.startswith("."):
                        proximo.append(item)
                elif item.name in nomes and nomes[item.name] not in achadas:
                    achadas[nomes[item.name]] = item
        nivel = proximo
    return achadas


def prefixo_ate_o_kit(pagina: Path, kit: Path) -> str:
    """Caminho relativo, com barra normal, da pasta da página até a do kit."""
    profundidade = len(pagina.parent.relative_to(kit).parts)
    return "../" * profundidade


def caminho_relativo(arquivo: Path, kit: Path) -> str:
    return "/".join(arquivo.relative_to(kit).parts)


NOMES_KIT = (
    "Kit_Completo_Automacao_Notebook_TNADV_v2_Multi_IA",
    "Kit_Completo_Automacao_Notebook_TNADV",
)


def kits_padrao(home: Path | None = None, ambiente: dict | None = None) -> list[Path]:
    """Pastas do kit nos lugares em que o instalador e o advogado as deixaram.

    Área de Trabalho (com ou sem OneDrive) para o kit extraído, e
    Documentos/TNADV_Automacao, destino do INSTALAR_TUDO_NO_NOTEBOOK_TNADV.bat.
    Só volta pasta que existe e tem ao menos uma central dentro.
    """
    home = home or Path.home()
    amb = os.environ if ambiente is None else ambiente
    bases = [Path(amb[v]) for v in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial")
             if amb.get(v)]
    bases += [home / "OneDrive", home]
    candidatos = []
    for base in bases:
        for area in ("Desktop", "Área de Trabalho"):
            candidatos += [base / area / nome for nome in NOMES_KIT]
        for docs in ("Documents", "Documentos"):
            candidatos.append(base / docs / "TNADV_Automacao")
    vistos: set[Path] = set()
    saida: list[Path] = []
    for pasta in candidatos:
        if not pasta.is_dir():
            continue
        real = pasta.resolve()
        if real in vistos:
            continue
        vistos.add(real)
        if localizar_centrais(pasta):
            saida.append(pasta)
    return saida


def _ler_html(pagina: Path) -> tuple[str, bool]:
    bruto = pagina.read_bytes()
    return bruto.decode("utf-8-sig"), bruto.startswith(codecs.BOM_UTF8)


def _gravar_html(pagina: Path, html: str, bom: bool) -> None:
    pagina.write_bytes((codecs.BOM_UTF8 if bom else b"") + html.encode("utf-8"))


def conectar_kit(
    kit: Path,
    dados: dict,
    *,
    simular: bool = False,
    checar_temporaria: bool = True,
    planilha: Path | None = None,
) -> list[str]:
    """Liga as centrais de uma pasta do kit ao sistema e devolve o relatório.

    Grava, dentro do kit: a pasta `tnadv_ponte/` (script, estilo e dados), o
    `PAINEL_TNADV.html` e o bloco da ponte em cada central. Antes da primeira
    alteração de cada central, guarda uma cópia `*.antes-da-ponte.html`. Não
    apaga nada. `planilha`, se informada, é copiada para `tnadv_ponte/` e ganha
    link no painel.
    """
    kit = Path(kit)
    if checar_temporaria and em_pasta_temporaria(kit):
        raise ValueError(
            f"{kit} é pasta temporária (o Windows a apaga sozinho, e é onde ele "
            "abre arquivo de dentro de .zip sem extrair). Extraia o kit para uma "
            "pasta fixa e rode de novo apontando para ela."
        )
    centrais = localizar_centrais(kit)
    if not centrais:
        return [f"{kit}: nenhuma central encontrada; nada feito."]

    pasta = kit / PASTA_PONTE
    paginas = {chave: caminho_relativo(p, kit) for chave, p in centrais.items()}
    paginas["painel"] = PAINEL
    rel_planilha = f"{PASTA_PONTE}/{planilha.name}" if planilha else dados.get("planilha")
    dados_kit = dict(dados, paginas=paginas, planilha=rel_planilha)

    relatorio = [f"{kit}:"]
    acao = "gravaria" if simular else "gravou"
    if not simular:
        pasta.mkdir(exist_ok=True)
        for nome in ARQUIVOS_FIXOS:
            shutil.copyfile(ASSETS / nome, pasta / nome)
        (pasta / ARQUIVO_DADOS).write_text(dados_para_js(dados_kit), encoding="utf-8")
        shutil.copyfile(ASSETS / PAINEL, kit / PAINEL)
        if planilha:
            shutil.copyfile(planilha, pasta / planilha.name)
    relatorio.append(f"  {acao} {PASTA_PONTE}/ (ponte e dados) e {PAINEL}")
    if planilha:
        relatorio.append(f"  {acao} {rel_planilha}")

    for chave, pagina in sorted(centrais.items()):
        nome = caminho_relativo(pagina, kit)
        try:
            html, bom = _ler_html(pagina)
        except UnicodeDecodeError:
            relatorio.append(f"  {nome}: não está em UTF-8; não foi alterada.")
            continue
        novo = inserir_ponte(html, prefixo_ate_o_kit(pagina, kit), chave)
        if novo == html:
            relatorio.append(f"  {nome}: já estava ligada; dados atualizados.")
            continue
        backup = pagina.with_name(pagina.stem + SUFIXO_BACKUP)
        if not simular:
            if not backup.exists():
                shutil.copyfile(pagina, backup)
            _gravar_html(pagina, novo, bom)
        relatorio.append(
            f"  {nome}: {'ligaria' if simular else 'ligada'} "
            f"(cópia original em {backup.name})"
        )
    return relatorio


def desconectar_kit(kit: Path, *, simular: bool = False) -> list[str]:
    """Tira o bloco da ponte das centrais. Não apaga arquivo nenhum."""
    kit = Path(kit)
    relatorio = [f"{kit}:"]
    for chave, pagina in sorted(localizar_centrais(kit).items()):
        nome = caminho_relativo(pagina, kit)
        try:
            html, bom = _ler_html(pagina)
        except UnicodeDecodeError:
            relatorio.append(f"  {nome}: não está em UTF-8; não foi alterada.")
            continue
        if not esta_ligada(html):
            relatorio.append(f"  {nome}: não estava ligada.")
            continue
        if not simular:
            _gravar_html(pagina, remover_ponte(html), bom)
        relatorio.append(f"  {nome}: {'desligaria' if simular else 'desligada'}.")
    relatorio.append(
        f"  {PASTA_PONTE}/ e {PAINEL} ficam onde estão; apague à mão se quiser."
    )
    return relatorio
