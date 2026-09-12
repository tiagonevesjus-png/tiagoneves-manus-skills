"""Calendário forense: feriados nacionais, móveis e suspensões legais.

Todo feriado nacional codificado aqui foi conferido no texto oficial em
planalto.gov.br. A base legal literal está em `docs/BASE-LEGAL-PRAZOS.md`.

Regra de projeto: feriados estaduais e municipais NÃO são presumidos. Eles
entram apenas por arquivo de calendário confirmado pelo advogado
(`core/calendarios/*.json`). Enquanto não confirmados, o motor emite aviso e
marca o resultado como estimativa.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path

CALENDARIOS_DIR = Path(__file__).parent / "calendarios"

# Lei 662/1949, art. 1º, na redação da Lei 10.607/2002; Lei 6.802/1980;
# Lei 14.759/2023. Ver transcrição literal em docs/BASE-LEGAL-PRAZOS.md.
FERIADOS_NACIONAIS_FIXOS: dict[tuple[int, int], tuple[str, str]] = {
    (1, 1): ("Confraternização Universal", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (4, 21): ("Tiradentes", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (5, 1): ("Dia do Trabalho", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (9, 7): ("Independência", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (10, 12): ("Nossa Senhora Aparecida", "Lei 6.802/1980, art. 1º"),
    (11, 2): ("Finados", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (11, 15): ("Proclamação da República", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
    (11, 20): ("Dia Nacional de Zumbi e da Consciência Negra", "Lei 14.759/2023, art. 1º"),
    (12, 25): ("Natal", "Lei 662/1949, art. 1º (red. Lei 10.607/2002)"),
}

# Sexta-feira da Paixão NÃO consta do rol de feriados nacionais civis. A Lei
# 9.093/1995, art. 2º, a classifica como feriado religioso declarado em lei
# municipal. Na prática forense é dia sem expediente na maioria das comarcas,
# mas isso depende de norma local ou de ato do tribunal: entra por calendário,
# não por presunção.


def pascoa(ano: int) -> date:
    """Domingo de Páscoa pelo algoritmo de Meeus/Jones/Butcher (calendário gregoriano)."""
    a = ano % 19
    b, c = divmod(ano, 100)
    d, e = divmod(b, 4)
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i, k = divmod(c, 4)
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes, dia = divmod(h + l - 7 * m + 114, 31)
    return date(ano, mes, dia + 1)


def feriados_moveis(ano: int) -> dict[date, tuple[str, str]]:
    """Datas móveis ancoradas na Páscoa, com a natureza jurídica de cada uma."""
    p = pascoa(ano)
    return {
        p - timedelta(days=48): ("Segunda-feira de Carnaval", "ponto facultativo/ato do tribunal"),
        p - timedelta(days=47): ("Terça-feira de Carnaval", "ponto facultativo/ato do tribunal"),
        p - timedelta(days=46): ("Quarta-feira de Cinzas", "expediente reduzido/ato do tribunal"),
        p - timedelta(days=2): ("Sexta-feira da Paixão", "Lei 9.093/1995, art. 2º (lei municipal)"),
        p + timedelta(days=60): ("Corpus Christi", "ponto facultativo/ato do tribunal"),
    }


def feriados_justica_federal(ano: int) -> dict[date, tuple[str, str]]:
    """Feriados próprios da Justiça Federal e Tribunais Superiores.

    Lei 5.010/1966, art. 62, com a redação do inciso IV dada pela Lei 6.741/1979.
    """
    base = "Lei 5.010/1966, art. 62"
    fer: dict[date, tuple[str, str]] = {}
    for dia in range(20, 32):
        fer[date(ano, 12, dia)] = ("Recesso forense (JF)", f"{base}, I")
    for dia in range(1, 7):
        fer[date(ano, 1, dia)] = ("Recesso forense (JF)", f"{base}, I")
    p = pascoa(ano)
    for delta in (4, 3, 2, 1, 0):  # quarta-feira da Semana Santa ao Domingo de Páscoa
        fer[p - timedelta(days=delta)] = ("Semana Santa (JF)", f"{base}, II")
    fer[p - timedelta(days=48)] = ("Segunda-feira de Carnaval (JF)", f"{base}, III")
    fer[p - timedelta(days=47)] = ("Terça-feira de Carnaval (JF)", f"{base}, III")
    fer[date(ano, 8, 11)] = ("Dia do Advogado (JF)", f"{base}, IV (red. Lei 6.741/1979)")
    fer[date(ano, 11, 1)] = ("1º de novembro (JF)", f"{base}, IV (red. Lei 6.741/1979)")
    fer[date(ano, 12, 8)] = ("8 de dezembro (JF)", f"{base}, IV (red. Lei 6.741/1979)")
    return fer


def em_suspensao_recesso(dia: date) -> bool:
    """Recesso do art. 220 do CPC e do art. 775-A da CLT: 20/12 a 20/01, inclusive."""
    return (dia.month == 12 and dia.day >= 20) or (dia.month == 1 and dia.day <= 20)


@dataclass
class Calendario:
    """Calendário forense aplicável a um juízo específico.

    `confirmado` é falso enquanto o advogado não validar os feriados locais.
    Nesse estado, o motor de prazos devolve resultado marcado como estimativa
    com aviso explícito, e nunca como data definitiva.
    """

    nome: str
    justica_federal: bool = False
    aplicar_recesso: bool = True
    considerar_moveis: tuple[str, ...] = (
        "Segunda-feira de Carnaval",
        "Terça-feira de Carnaval",
        "Sexta-feira da Paixão",
        "Corpus Christi",
    )
    locais: dict[str, str] = field(default_factory=dict)  # "AAAA-MM-DD" -> descrição
    confirmado: bool = False
    observacoes: str = ""

    @classmethod
    def carregar(cls, chave: str) -> "Calendario":
        caminho = CALENDARIOS_DIR / f"{chave}.json"
        if not caminho.exists():
            disponiveis = sorted(p.stem for p in CALENDARIOS_DIR.glob("*.json"))
            raise FileNotFoundError(
                f"Calendário '{chave}' não encontrado. Disponíveis: {disponiveis}"
            )
        dados = json.loads(caminho.read_text(encoding="utf-8"))
        dados.pop("_comentario", None)
        if "considerar_moveis" in dados:
            dados["considerar_moveis"] = tuple(dados["considerar_moveis"])
        return cls(**dados)

    def _mapa_ano(self, ano: int) -> dict[date, tuple[str, str]]:
        mapa: dict[date, tuple[str, str]] = {}
        for (mes, dia), info in FERIADOS_NACIONAIS_FIXOS.items():
            mapa[date(ano, mes, dia)] = info
        for dia_, info in feriados_moveis(ano).items():
            if info[0] in self.considerar_moveis:
                mapa[dia_] = info
        if self.justica_federal:
            mapa.update(feriados_justica_federal(ano))
        for iso, descricao in self.locais.items():
            d = date.fromisoformat(iso)
            if d.year == ano:
                mapa[d] = (descricao, "calendário local confirmado")
        return mapa

    def motivo_nao_util(self, dia: date) -> str | None:
        """Devolve o motivo pelo qual o dia não é útil, ou None se for dia útil."""
        if dia.weekday() >= 5:
            return "sábado" if dia.weekday() == 5 else "domingo"
        if self.aplicar_recesso and em_suspensao_recesso(dia):
            return "recesso forense (CPC, art. 220 / CLT, art. 775-A)"
        info = self._mapa_ano(dia.year).get(dia)
        if info:
            return f"{info[0]} ({info[1]})"
        return None

    def e_util(self, dia: date) -> bool:
        return self.motivo_nao_util(dia) is None

    def proximo_util(self, dia: date, incluir_proprio: bool = True) -> date:
        atual = dia if incluir_proprio else dia + timedelta(days=1)
        for _ in range(400):
            if self.e_util(atual):
                return atual
            atual += timedelta(days=1)
        raise RuntimeError(f"Nenhum dia útil encontrado a partir de {dia}")

    def avisos(self) -> list[str]:
        av: list[str] = []
        if not self.confirmado:
            av.append(
                f"Calendário '{self.nome}' ainda não foi confirmado pelo advogado: "
                "feriados estaduais, municipais e atos de suspensão do tribunal podem "
                "estar ausentes. Confira no portal do tribunal antes de agendar o prazo."
            )
        if not self.locais:
            av.append(
                "Nenhum feriado local cadastrado neste calendário. Feriados estaduais e "
                "municipais não são presumidos pelo sistema."
            )
        if self.observacoes:
            av.append(self.observacoes)
        return av
