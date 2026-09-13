#!/usr/bin/env python3
"""Renderiza um dashboard de exemplo, com dados fictícios.

Serve de referência visual do padrão do escritório e de verificação de que a
cadeia de renderização continua funcionando. Nenhum dado de cliente aparece
aqui, então o arquivo pode ser aberto, impresso e mostrado a terceiros.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.dashboard_html import (  # noqa: E402
    Compromisso,
    Dashboard,
    Item,
    render_html,
    render_pagina,
    render_texto,
)


def exemplo(hoje: date) -> Dashboard:
    return Dashboard(
        data=hoje,
        resumo=(
            "Exemplo com dados fictícios, para referência do padrão visual. "
            "Duas frentes exigem decisão hoje, e uma delas tem prazo curto."
        ),
        itens=[
            Item(
                urgencia="vermelho",
                titulo="Conflito de audiências no mesmo dia",
                processo="0000001-02.2026.8.10.0001",
                cliente="Cliente Exemplo LTDA",
                orgao="Juizado Especial Cível de Exemplo",
                o_que_houve="Duas audiências presenciais em comarcas diferentes.",
                providencia="Pedir redesignação ou constituir audiencista.",
                vencimento_estimado=hoje.isoformat(),
                alerta=(
                    "Lei 9.099/1995, art. 20: não comparecendo o demandado, "
                    "reputar-se-ão verdadeiros os fatos alegados no pedido inicial."
                ),
                fontes=["agenda", "e-mail do cliente"],
            ),
            Item(
                urgencia="amarelo",
                titulo="Recurso admitido sem efeito suspensivo",
                processo="0000002-03.2026.5.16.0001",
                cliente="Outro Cliente LTDA",
                orgao="Vara do Trabalho de Exemplo",
                o_que_houve="Decisão de admissibilidade proferida e intimação expedida.",
                providencia="Conferir no sistema se houve intimação que deflagre prazo.",
                fontes=["PUSH do PJe"],
            ),
            Item(
                urgencia="verde",
                titulo="Despacho de mero expediente",
                processo="0000003-04.2026.8.10.0002",
                o_que_houve="Sem providência imediata.",
                fontes=["PUSH do PJe"],
            ),
        ],
        agenda=[
            Compromisso(
                quando="Hoje, 09:00",
                titulo="Reunião de exemplo",
                detalhe="Pauta registrada em mensagem.",
                alerta="Confirmação de presença pendente.",
                data=hoje,
            ),
            Compromisso(
                quando="Amanhã, 14:30",
                titulo="Audiência de instrução de exemplo",
                detalhe="Comarca de Exemplo, presencial.",
                data=hoje + timedelta(days=1),
            ),
        ],
        pendentes_conferencia=[
            "Nenhum prazo cadastrado no acervo de exemplo.",
        ],
        pendencias_sistema=[
            "Comarca de exemplo sem calendário forense confirmado.",
        ],
        fontes_varredura=[
            "dados fictícios de demonstração",
        ],
    )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--saida", default="saida/exemplo-dashboard.html")
    args = ap.parse_args()

    dash = exemplo(date.today())
    destino = Path(args.saida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(render_pagina(dash), encoding="utf-8")

    # Exercita as três saídas, para que uma quebra apareça aqui e não no e-mail.
    html, texto = render_html(dash), render_texto(dash)

    c = dash.contagem()
    print(f"Exemplo gerado: {destino}")
    print(f"Itens: vermelho {c['vermelho']} | amarelo {c['amarelo']} | verde {c['verde']}")
    print(f"Corpo de e-mail: {len(html)} bytes | texto puro: {len(texto)} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
