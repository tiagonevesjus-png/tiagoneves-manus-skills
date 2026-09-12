"""Núcleo compartilhado das automações jurídicas TNADV."""

from .acervo import Acervo, Audiencia, Movimento, Prazo, Processo, classificar_urgencia
from .cnj import NumeroCNJ, e_valido, extrair, validar
from .feriados import Calendario, pascoa
from .prazos import Regime, ResultadoPrazo, TermoInicial, contar_prazo

__all__ = [
    "Acervo", "Audiencia", "Movimento", "Prazo", "Processo", "classificar_urgencia",
    "NumeroCNJ", "e_valido", "extrair", "validar",
    "Calendario", "pascoa",
    "Regime", "ResultadoPrazo", "TermoInicial", "contar_prazo",
]
