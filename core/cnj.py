"""Numeração única de processos (Resolução CNJ 65/2008).

Formato: NNNNNNN-DD.AAAA.J.TR.OOOO
    NNNNNNN  sequencial por unidade de origem e ano
    DD       dígito verificador (ISO 7064 MOD 97-10)
    AAAA     ano do ajuizamento
    J        segmento do Poder Judiciário
    TR       tribunal
    OOOO     unidade de origem
"""

from __future__ import annotations

import re
from dataclasses import dataclass

PADRAO = re.compile(r"^(\d{7})-?(\d{2})\.?(\d{4})\.?(\d)\.?(\d{2})\.?(\d{4})$")

SEGMENTOS: dict[str, str] = {
    "1": "Supremo Tribunal Federal",
    "2": "Conselho Nacional de Justiça",
    "3": "Superior Tribunal de Justiça",
    "4": "Justiça Federal",
    "5": "Justiça do Trabalho",
    "6": "Justiça Eleitoral",
    "7": "Justiça Militar da União",
    "8": "Justiça Estadual",
    "9": "Justiça Militar Estadual",
}

# Calendário de contagem sugerido por segmento. A escolha final continua sendo
# do advogado: rito e matéria podem alterar o regime.
CALENDARIO_POR_SEGMENTO: dict[str, str] = {
    "1": "justica-federal",
    "3": "justica-federal",
    "4": "justica-federal",
    "5": "justica-do-trabalho",
    "8": "padrao-justica-estadual",
}


@dataclass
class NumeroCNJ:
    sequencial: str
    digito: str
    ano: str
    segmento: str
    tribunal: str
    origem: str

    @property
    def formatado(self) -> str:
        return (
            f"{self.sequencial}-{self.digito}.{self.ano}."
            f"{self.segmento}.{self.tribunal}.{self.origem}"
        )

    @property
    def segmento_nome(self) -> str:
        return SEGMENTOS.get(self.segmento, "segmento desconhecido")

    @property
    def calendario_sugerido(self) -> str:
        return CALENDARIO_POR_SEGMENTO.get(self.segmento, "padrao-justica-estadual")


def _digito_esperado(sequencial: str, ano: str, segmento: str, tribunal: str, origem: str) -> str:
    """Dígito verificador pelo módulo 97 base 10 (ISO 7064), na forma da Res. CNJ 65/2008."""
    base = int(f"{sequencial}{ano}{segmento}{tribunal}{origem}00")
    return f"{98 - (base % 97):02d}"


def validar(numero: str) -> NumeroCNJ:
    """Valida e decompõe um número CNJ. Levanta ValueError quando inválido."""
    limpo = numero.strip()
    m = PADRAO.match(limpo)
    if not m:
        raise ValueError(
            f"Número fora do padrão CNJ (NNNNNNN-DD.AAAA.J.TR.OOOO): {numero!r}"
        )
    sequencial, digito, ano, segmento, tribunal, origem = m.groups()
    esperado = _digito_esperado(sequencial, ano, segmento, tribunal, origem)
    if digito != esperado:
        raise ValueError(
            f"Dígito verificador inválido em {numero!r}: informado {digito}, "
            f"esperado {esperado}. Confira a transcrição do número."
        )
    if segmento not in SEGMENTOS:
        raise ValueError(f"Segmento do Judiciário desconhecido: {segmento}")
    return NumeroCNJ(sequencial, digito, ano, segmento, tribunal, origem)


def e_valido(numero: str) -> bool:
    try:
        validar(numero)
        return True
    except ValueError:
        return False


def gerar_digito(sequencial: str, ano: str, segmento: str, tribunal: str, origem: str) -> str:
    """Calcula o dígito verificador de um número montado a partir das partes."""
    return _digito_esperado(sequencial, ano, segmento, tribunal, origem)


def extrair(texto: str) -> list[str]:
    """Extrai de um texto livre todos os números CNJ válidos, sem repetição."""
    achados = re.findall(r"\d{7}-?\d{2}\.?\d{4}\.?\d\.?\d{2}\.?\d{4}", texto)
    vistos: list[str] = []
    for bruto in achados:
        try:
            fmt = validar(bruto).formatado
        except ValueError:
            continue
        if fmt not in vistos:
            vistos.append(fmt)
    return vistos
