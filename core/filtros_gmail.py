"""Geração de filtros nativos do Gmail para a taxonomia TNADV.

O Gmail importa e exporta filtros em XML (Configurações, Filtros e endereços
bloqueados, Importar filtros). Esse mecanismo é nativo: roda no servidor do
Google, a cada mensagem que chega, sem depender de sessão aberta, de automação
externa ou de qualquer integração de terceiro.

Divisão de trabalho adotada pelo escritório:

- **Filtro nativo** cuida do que é determinístico: remetente conhecido, domínio
  de tribunal, assunto com marcador inequívoco. Roda sozinho, para sempre.
- **Triagem assistida** cuida do que exige leitura e julgamento: distinguir
  intimação de aviso, cliente de fornecedor, conta do escritório de conta
  pessoal. Produz relatório, não rótulo.

Regra de segurança: nenhum filtro gerado aqui arquiva, marca como lido, exclui
ou encaminha. Filtro só rotula.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import quoteattr

CABECALHO = (
    "<?xml version='1.0' encoding='UTF-8'?>\n"
    "<feed xmlns='http://www.w3.org/2005/Atom' "
    "xmlns:apps='http://schemas.google.com/apps/2006'>\n"
    "  <title>Filtros TNADV</title>\n"
)
RODAPE = "</feed>\n"

# Propriedades de filtro que alteram o estado da mensagem além de rotular.
# Nenhuma delas é permitida: a automação não apaga, não arquiva e não lê por
# você (ver CLAUDE.md, regra 5).
PROIBIDAS = {
    "shouldArchive",
    "shouldTrash",
    "shouldMarkAsRead",
    "forwardTo",
    "shouldSpam",
}


@dataclass
class Filtro:
    """Uma regra de rotulação nativa do Gmail."""

    rotulo: str
    descricao: str
    de: str = ""                  # apps:property name='from'
    para: str = ""                # name='to'
    assunto: str = ""             # name='subject'
    contem: str = ""              # name='hasTheWord'
    nao_contem: str = ""          # name='doesNotHaveTheWord'
    nunca_spam: bool = True       # name='shouldNeverSpam'

    def propriedades(self) -> list[tuple[str, str]]:
        props: list[tuple[str, str]] = []
        if self.de:
            props.append(("from", self.de))
        if self.para:
            props.append(("to", self.para))
        if self.assunto:
            props.append(("subject", self.assunto))
        if self.contem:
            props.append(("hasTheWord", self.contem))
        if self.nao_contem:
            props.append(("doesNotHaveTheWord", self.nao_contem))
        if not props:
            raise ValueError(
                f"Filtro '{self.descricao}' não tem critério de correspondência. "
                "Um filtro sem critério casaria com toda a caixa."
            )
        props.append(("label", self.rotulo))
        if self.nunca_spam:
            props.append(("shouldNeverSpam", "true"))
        return props

    def para_xml(self) -> str:
        linhas = [
            "  <entry>",
            "    <category term='filter'></category>",
            f"    <title>{_escapar_texto(self.descricao)}</title>",
            "    <content></content>",
        ]
        for nome, valor in self.propriedades():
            if nome in PROIBIDAS:
                raise ValueError(f"Propriedade proibida em filtro TNADV: {nome}")
            linhas.append(
                f"    <apps:property name={quoteattr(nome)} value={quoteattr(valor)}/>"
            )
        linhas.append("  </entry>")
        return "\n".join(linhas) + "\n"


def _escapar_texto(texto: str) -> str:
    return (
        texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    )


def gerar_xml(filtros: list[Filtro]) -> str:
    if not filtros:
        raise ValueError("Nenhum filtro a gerar.")
    return CABECALHO + "".join(f.para_xml() for f in filtros) + RODAPE


def escrever(filtros: list[Filtro], destino: Path | str) -> Path:
    caminho = Path(destino)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(gerar_xml(filtros), encoding="utf-8")
    return caminho


# ---------------------------------------------------------------------------
# Conjunto de regras do escritório.
#
# Cada remetente abaixo foi observado na caixa em 12/09/2026. Nada aqui é
# suposição: são domínios que efetivamente chegam. Ao acrescentar regra nova,
# confirme antes que o remetente existe na caixa.
# ---------------------------------------------------------------------------

def regras_tnadv() -> list[Filtro]:
    return [
        # --- Tribunais e sistemas processuais -----------------------------
        Filtro(
            rotulo="TNADV/Intimações",
            descricao="Comunicações do TRT da 16ª Região",
            de="trt16.jus.br",
        ),
        Filtro(
            rotulo="TNADV/Intimações",
            descricao="Comunicações de qualquer órgão do Judiciário (.jus.br)",
            de="jus.br",
        ),
        Filtro(
            rotulo="TNADV/Intimações",
            descricao="Comunicações do DJEN e do Comunica PJe",
            de="comunica.pje.jus.br OR djen.csjt.jus.br",
        ),
        Filtro(
            rotulo="TNADV/Intimações",
            descricao="Assunto com marcador de intimação ou publicação",
            assunto="intimação OR intimacao OR \"Diário da Justiça\" OR \"Diario da Justica\"",
        ),
        # --- Audiências ----------------------------------------------------
        Filtro(
            rotulo="TNADV/Audiências",
            descricao="Assunto com designação de audiência",
            assunto="audiência OR audiencia",
        ),
        # --- Ordem dos Advogados -------------------------------------------
        Filtro(
            rotulo="TNADV/Administrativo",
            descricao="Ordem dos Advogados do Brasil",
            de="oab.org.br OR oabma.org.br",
        ),
        # --- Financeiro do escritório ---------------------------------------
        Filtro(
            rotulo="TNADV/Financeiro",
            descricao="Meios de recebimento e conta jurídica do escritório",
            de="asaas.com.br OR pagbank.com.br OR mkt.pagbank.com.br "
               "OR stone.com.br OR cora.com.br",
        ),
        # --- Pessoal ---------------------------------------------------------
        Filtro(
            rotulo="TNADV/Pessoal",
            descricao="Serviços pessoais e notificações de conta",
            de="nubank.com.br OR recargapay.com.br OR mercadolivre.com.br "
               "OR info.mercadolivre.com.br OR googlewallet-noreply@google.com "
               "OR e.drogasil.com.br",
        ),
        Filtro(
            rotulo="TNADV/Pessoal",
            descricao="Avisos de compartilhamento de dados da Conta Google",
            de="noreply-accounts@google.com",
        ),
        # --- Ferramentas e fornecedores --------------------------------------
        Filtro(
            rotulo="TNADV/Administrativo",
            descricao="Ferramentas de trabalho e fornecedores de software",
            de="mail.anthropic.com OR mail.midpage.ai OR marketing.easyjur.com "
               "OR email2.microsoft.com",
        ),
    ]


def validar_regras(filtros: list[Filtro]) -> list[str]:
    """Confere as regras antes de gerar. Devolve lista de problemas."""
    problemas: list[str] = []
    vistos: set[tuple[str, str]] = set()
    for f in filtros:
        try:
            props = dict(f.propriedades())
        except ValueError as e:
            problemas.append(str(e))
            continue
        chave = (props.get("from", ""), props.get("subject", ""), f.rotulo)
        if chave in vistos:
            problemas.append(f"Regra duplicada: {f.descricao}")
        vistos.add(chave)
        if not f.rotulo.startswith("TNADV/"):
            problemas.append(
                f"Rótulo fora da taxonomia TNADV em '{f.descricao}': {f.rotulo}"
            )
        criterio = props.get("from", "") + props.get("subject", "")
        if re.fullmatch(r"\s*", criterio) and not props.get("hasTheWord"):
            problemas.append(f"Critério vazio em '{f.descricao}'")
    return problemas
