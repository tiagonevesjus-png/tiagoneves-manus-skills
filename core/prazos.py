"""Motor de contagem de prazos processuais.

Premissa inegociável do projeto: este motor produz ESTIMATIVA, nunca data
definitiva. Toda saída carrega `requer_conferencia=True`, a base legal aplicada
e a lista de avisos. A conferência no sistema do tribunal continua sendo ato
privativo do advogado.

Base legal literal conferida em planalto.gov.br e transcrita em
`docs/BASE-LEGAL-PRAZOS.md`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from .feriados import Calendario


class Regime(str, Enum):
    """Regime de contagem aplicável ao prazo."""

    CPC_DIAS_UTEIS = "cpc_dias_uteis"
    CLT_DIAS_UTEIS = "clt_dias_uteis"
    JEC_DIAS_UTEIS = "jec_dias_uteis"
    DIAS_CORRIDOS = "dias_corridos"


BASE_LEGAL_REGIME: dict[Regime, tuple[str, ...]] = {
    Regime.CPC_DIAS_UTEIS: (
        "CPC/2015, art. 219: \"Na contagem de prazo em dias, estabelecido por lei ou "
        "pelo juiz, computar-se-ão somente os dias úteis.\"",
        "CPC/2015, art. 219, parágrafo único: \"O disposto neste artigo aplica-se "
        "somente aos prazos processuais.\"",
        "CPC/2015, art. 224: \"Salvo disposição em contrário, os prazos serão contados "
        "excluindo o dia do começo e incluindo o dia do vencimento.\"",
    ),
    Regime.CLT_DIAS_UTEIS: (
        "CLT, art. 775 (red. Lei 13.467/2017): \"Os prazos estabelecidos neste Título "
        "serão contados em dias úteis, com exclusão do dia do começo e inclusão do dia "
        "do vencimento.\"",
    ),
    Regime.JEC_DIAS_UTEIS: (
        "Lei 9.099/1995, art. 12-A (incluído pela Lei 13.728/2018): \"Na contagem de "
        "prazo em dias, estabelecido por lei ou pelo juiz, para a prática de qualquer "
        "ato processual, inclusive para a interposição de recursos, computar-se-ão "
        "somente os dias úteis.\"",
    ),
    Regime.DIAS_CORRIDOS: (
        "Contagem em dias corridos: aplicável a prazos de direito material e às "
        "hipóteses em que a lei afasta expressamente o art. 219 do CPC. Confirme o "
        "enquadramento antes de usar este regime.",
    ),
}


class TermoInicial(str, Enum):
    """Marco inicial, conforme art. 231 do CPC e legislação correlata."""

    DJE_DISPONIBILIZACAO = "dje_disponibilizacao"
    PUBLICACAO = "publicacao"
    CONSULTA_ELETRONICA = "consulta_eletronica"
    DECURSO_PRAZO_CONSULTA = "decurso_prazo_consulta"
    JUNTADA_AR = "juntada_ar"
    JUNTADA_MANDADO = "juntada_mandado"
    ATO_DO_ESCRIVAO = "ato_do_escrivao"
    CARGA = "carga"
    CIENCIA_EXPRESSA = "ciencia_expressa"


BASE_LEGAL_TERMO: dict[TermoInicial, tuple[str, ...]] = {
    TermoInicial.DJE_DISPONIBILIZACAO: (
        "Lei 11.419/2006, art. 4º, § 3º: \"Considera-se como data da publicação o "
        "primeiro dia útil seguinte ao da disponibilização da informação no Diário da "
        "Justiça eletrônico.\"",
        "Lei 11.419/2006, art. 4º, § 4º: \"Os prazos processuais terão início no "
        "primeiro dia útil que seguir ao considerado como data da publicação.\"",
        "CPC/2015, art. 224, §§ 2º e 3º.",
    ),
    TermoInicial.PUBLICACAO: (
        "CPC/2015, art. 231, VII: \"a data de publicação, quando a intimação se der "
        "pelo Diário da Justiça impresso ou eletrônico\".",
        "CPC/2015, art. 224, § 3º: \"A contagem do prazo terá início no primeiro dia "
        "útil que seguir ao da publicação.\"",
    ),
    TermoInicial.CONSULTA_ELETRONICA: (
        "CPC/2015, art. 231, V: \"o dia útil seguinte à consulta ao teor da citação ou "
        "da intimação ou ao término do prazo para que a consulta se dê, quando a "
        "citação ou a intimação for eletrônica\".",
        "Lei 11.419/2006, art. 5º, § 1º: \"Considerar-se-á realizada a intimação no dia "
        "em que o intimando efetivar a consulta eletrônica ao teor da intimação, "
        "certificando-se nos autos a sua realização.\"",
        "Lei 11.419/2006, art. 5º, § 2º: consulta em dia não útil desloca a intimação "
        "para o primeiro dia útil seguinte.",
    ),
    TermoInicial.DECURSO_PRAZO_CONSULTA: (
        "Lei 11.419/2006, art. 5º, § 3º: \"A consulta referida nos §§ 1º e 2º deste "
        "artigo deverá ser feita em até 10 (dez) dias corridos contados da data do "
        "envio da intimação, sob pena de considerar-se a intimação automaticamente "
        "realizada na data do término desse prazo.\"",
        "CPC/2015, art. 231, V (parte final).",
    ),
    TermoInicial.JUNTADA_AR: (
        "CPC/2015, art. 231, I: \"a data de juntada aos autos do aviso de recebimento, "
        "quando a citação ou a intimação for pelo correio\".",
    ),
    TermoInicial.JUNTADA_MANDADO: (
        "CPC/2015, art. 231, II: \"a data de juntada aos autos do mandado cumprido, "
        "quando a citação ou a intimação for por oficial de justiça\".",
    ),
    TermoInicial.ATO_DO_ESCRIVAO: (
        "CPC/2015, art. 231, III: \"a data de ocorrência da citação ou da intimação, "
        "quando ela se der por ato do escrivão ou do chefe de secretaria\".",
    ),
    TermoInicial.CARGA: (
        "CPC/2015, art. 231, VIII: \"o dia da carga, quando a intimação se der por meio "
        "da retirada dos autos, em carga, do cartório ou da secretaria\".",
    ),
    TermoInicial.CIENCIA_EXPRESSA: (
        "CPC/2015, art. 231, § 3º: ato a ser praticado diretamente pela parte, o dia do "
        "começo corresponde à data da comunicação.",
    ),
}

# Prerrogativas de prazo em dobro, com base legal conferida.
PRERROGATIVAS_DOBRO: dict[str, str] = {
    "fazenda_publica": (
        "CPC/2015, art. 183: \"A União, os Estados, o Distrito Federal, os Municípios e "
        "suas respectivas autarquias e fundações de direito público gozarão de prazo em "
        "dobro para todas as suas manifestações processuais, cuja contagem terá início "
        "a partir da intimação pessoal.\""
    ),
    "ministerio_publico": (
        "CPC/2015, art. 180: prazo em dobro para manifestar-se nos autos, com início a "
        "partir da intimação pessoal."
    ),
    "defensoria_publica": (
        "CPC/2015, art. 186: \"A Defensoria Pública gozará de prazo em dobro para todas "
        "as suas manifestações processuais.\""
    ),
    "litisconsortes_autos_fisicos": (
        "CPC/2015, art. 229: litisconsortes com procuradores de escritórios distintos "
        "têm prazo em dobro; o § 2º afasta o benefício nos processos em autos "
        "eletrônicos."
    ),
}


@dataclass
class DiaContado:
    data: date
    util: bool
    motivo: str | None
    ordinal: int | None  # posição do dia no prazo, quando computado


@dataclass
class ResultadoPrazo:
    """Resultado sempre estimado, nunca definitivo."""

    evento: date
    descricao_evento: str
    regime: Regime
    dias_prazo: int
    dias_efetivos: int
    intimacao_considerada: date
    inicio_contagem: date
    vencimento: date
    base_legal: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    trilha: list[DiaContado] = field(default_factory=list)
    requer_conferencia: bool = True

    def resumo(self) -> str:
        linhas = [
            f"Evento ({self.descricao_evento}): {self.evento:%d/%m/%Y}",
            f"Intimação/publicação considerada: {self.intimacao_considerada:%d/%m/%Y}",
            f"Início da contagem: {self.inicio_contagem:%d/%m/%Y}",
            f"Prazo: {self.dias_prazo} dias"
            + (f" (em dobro: {self.dias_efetivos} dias)" if self.dias_efetivos != self.dias_prazo else ""),
            f"Regime: {self.regime.value}",
            f"VENCIMENTO ESTIMADO: {self.vencimento:%d/%m/%Y} ({DIAS_SEMANA[self.vencimento.weekday()]})",
            "",
            "ESTIMATIVA SUJEITA A CONFERÊNCIA OBRIGATÓRIA NO SISTEMA DO TRIBUNAL.",
        ]
        if self.avisos:
            linhas += ["", "Avisos:"] + [f"  - {a}" for a in self.avisos]
        linhas += ["", "Base legal aplicada:"] + [f"  - {b}" for b in self.base_legal]
        return "\n".join(linhas)


DIAS_SEMANA = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]


def _resolver_inicio(
    evento: date,
    termo: TermoInicial,
    cal: Calendario,
    avisos: list[str],
) -> tuple[date, date]:
    """Devolve (data considerada da intimação/publicação, primeiro dia da contagem)."""
    if termo == TermoInicial.DJE_DISPONIBILIZACAO:
        publicacao = cal.proximo_util(evento + timedelta(days=1))
        return publicacao, cal.proximo_util(
            publicacao + timedelta(days=1), exigir_expediente_pleno=True
        )

    if termo == TermoInicial.PUBLICACAO:
        return evento, cal.proximo_util(
            evento + timedelta(days=1), exigir_expediente_pleno=True
        )

    if termo == TermoInicial.CONSULTA_ELETRONICA:
        # Lei 11.419/2006, art. 5º, § 2º: consulta em dia não útil desloca a
        # intimação para o primeiro dia útil seguinte.
        intimacao = cal.proximo_util(evento)
        if intimacao != evento:
            avisos.append(
                f"Consulta feita em {evento:%d/%m/%Y}, dia não útil "
                f"({cal.motivo_nao_util(evento)}). Intimação considerada realizada em "
                f"{intimacao:%d/%m/%Y} (Lei 11.419/2006, art. 5º, § 2º)."
            )
        return intimacao, cal.proximo_util(
            intimacao + timedelta(days=1), exigir_expediente_pleno=True
        )

    if termo == TermoInicial.DECURSO_PRAZO_CONSULTA:
        # § 3º: 10 dias CORRIDOS a contar do envio; findo o prazo sem consulta,
        # a intimação se considera automaticamente realizada nesse termo final.
        termo_final = evento + timedelta(days=10)
        avisos.append(
            f"Envio da intimação em {evento:%d/%m/%Y}; prazo de 10 dias corridos para "
            f"consulta encerra em {termo_final:%d/%m/%Y} (Lei 11.419/2006, art. 5º, § 3º). "
            "Se houve consulta antes desse termo, recalcule com "
            "TermoInicial.CONSULTA_ELETRONICA usando a data real da consulta."
        )
        return termo_final, cal.proximo_util(
            termo_final + timedelta(days=1), exigir_expediente_pleno=True
        )

    # Demais incisos do art. 231: o dia do evento é o dia do começo, excluído da
    # contagem (art. 224), que se inicia no dia útil seguinte.
    return evento, cal.proximo_util(
        evento + timedelta(days=1), exigir_expediente_pleno=True
    )


def contar_prazo(
    evento: date,
    dias: int,
    *,
    regime: Regime = Regime.CPC_DIAS_UTEIS,
    termo: TermoInicial = TermoInicial.DJE_DISPONIBILIZACAO,
    calendario: Calendario | str = "padrao-justica-estadual",
    prerrogativa_dobro: str | None = None,
    descricao_evento: str = "disponibilização no DJe",
) -> ResultadoPrazo:
    """Calcula o vencimento estimado de um prazo processual.

    Args:
        evento: data do fato que deflagra o termo inicial (disponibilização,
            consulta, juntada, carga etc.).
        dias: prazo legal em dias, na forma simples (sem dobra).
        regime: dias úteis (CPC/CLT/JEC) ou dias corridos.
        termo: marco inicial conforme o art. 231 do CPC.
        calendario: chave de `core/calendarios/` ou instância de `Calendario`.
        prerrogativa_dobro: chave de `PRERROGATIVAS_DOBRO`, quando aplicável.
        descricao_evento: texto livre que aparece no resumo.
    """
    if dias <= 0:
        raise ValueError("O prazo em dias deve ser positivo.")

    cal = Calendario.carregar(calendario) if isinstance(calendario, str) else calendario
    avisos: list[str] = list(cal.avisos(ano=evento.year))
    base_legal: list[str] = list(BASE_LEGAL_REGIME[regime]) + list(BASE_LEGAL_TERMO[termo])

    dias_efetivos = dias
    if prerrogativa_dobro:
        if prerrogativa_dobro not in PRERROGATIVAS_DOBRO:
            raise ValueError(
                f"Prerrogativa desconhecida: {prerrogativa_dobro}. "
                f"Use uma de {sorted(PRERROGATIVAS_DOBRO)}."
            )
        dias_efetivos = dias * 2
        base_legal.append(PRERROGATIVAS_DOBRO[prerrogativa_dobro])
        if prerrogativa_dobro == "litisconsortes_autos_fisicos":
            avisos.append(
                "Prazo em dobro do art. 229 do CPC não se aplica a autos eletrônicos "
                "(art. 229, § 2º). Confirme que o processo tramita em autos físicos."
            )

    marco, inicio = _resolver_inicio(evento, termo, cal, avisos)

    trilha: list[DiaContado] = []
    contados = 0
    atual = inicio

    if regime == Regime.DIAS_CORRIDOS:
        vencimento = inicio + timedelta(days=dias_efetivos - 1)
        d = inicio
        while d <= vencimento:
            trilha.append(DiaContado(d, cal.e_util(d), cal.motivo_nao_util(d), (d - inicio).days + 1))
            d += timedelta(days=1)
        # CPC, art. 224, § 1º: vencimento em dia sem expediente, ou com
        # expediente encerrado antes ou iniciado depois da hora normal, é protraído.
        if not cal.expediente_pleno(vencimento):
            original = vencimento
            motivo = cal.motivo_nao_util(original) or cal.motivo_expediente_reduzido(original)
            vencimento = cal.proximo_util(vencimento, exigir_expediente_pleno=True)
            avisos.append(
                f"Vencimento recairia em {original:%d/%m/%Y} "
                f"({motivo}); prorrogado para {vencimento:%d/%m/%Y} "
                "(CPC, art. 224, § 1º)."
            )
    else:
        limite = 0
        while contados < dias_efetivos:
            limite += 1
            if limite > 3000:
                raise RuntimeError("Contagem não convergiu; verifique o calendário.")
            motivo = cal.motivo_nao_util(atual)
            if motivo is None:
                contados += 1
                trilha.append(DiaContado(atual, True, None, contados))
            else:
                trilha.append(DiaContado(atual, False, motivo, None))
            if contados == dias_efetivos:
                break
            atual += timedelta(days=1)
        vencimento = atual

        # CPC, art. 224, § 1º: o dia do vencimento é protraído quando o
        # expediente for encerrado antes ou iniciado depois da hora normal.
        reduzido = cal.motivo_expediente_reduzido(vencimento)
        if reduzido:
            original = vencimento
            vencimento = cal.proximo_util(
                vencimento + timedelta(days=1), exigir_expediente_pleno=True
            )
            avisos.append(
                f"O {dias_efetivos}º dia útil recai em {original:%d/%m/%Y}, de expediente "
                f"reduzido ({reduzido}); vencimento prorrogado para "
                f"{vencimento:%d/%m/%Y} (CPC, art. 224, § 1º)."
            )

    if vencimento.year != evento.year and vencimento.year not in cal.anos_cobertos():
        avisos.append(
            f"O prazo termina em {vencimento.year}, ano sem feriado local cadastrado no "
            f"calendário '{cal.nome}'. A contagem atravessa a virada do ano com os "
            "feriados locais incompletos. Regenere o calendário antes de agendar."
        )

    if any(d.motivo and "recesso" in d.motivo for d in trilha):
        avisos.append(
            "O prazo atravessa o recesso de 20/12 a 20/01 (CPC, art. 220; CLT, art. "
            "775-A). Confirme o ato de suspensão do tribunal para o ano em questão."
        )

    avisos.append(
        "Resultado é ESTIMATIVA. Confira o prazo no sistema do tribunal antes de "
        "agendar providência ou informar o cliente."
    )

    return ResultadoPrazo(
        evento=evento,
        descricao_evento=descricao_evento,
        regime=regime,
        dias_prazo=dias,
        dias_efetivos=dias_efetivos,
        intimacao_considerada=marco,
        inicio_contagem=inicio,
        vencimento=vencimento,
        base_legal=base_legal,
        avisos=avisos,
        trilha=trilha,
    )
