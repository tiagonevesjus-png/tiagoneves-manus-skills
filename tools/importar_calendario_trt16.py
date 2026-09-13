#!/usr/bin/env python3
"""Importa o calendário institucional do TRT da 16ª Região e gera o arquivo de
calendário forense usado pelo motor de prazos.

Fonte oficial: https://www.trt16.jus.br/site/conteudo/calendario/cieEvtExportaIcs.php
O tribunal publica o ano inteiro em iCal, com abrangência por município. Este
utilitário lê essa fonte, filtra o que se aplica ao município escolhido e grava
`core/calendarios/TRT16-<municipio>.json`.

Regenerar a cada início de ano judiciário. O arquivo gerado registra a URL e a
data da consulta, para que a origem de cada data seja auditável.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ICS_URL = "https://www.trt16.jus.br/site/conteudo/calendario/cieEvtExportaIcs.php"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"

# Eventos que NÃO retiram o expediente: são avisos de escala, não fechamento.
IGNORAR = re.compile(r"plant[ãa]o|data tem evento", re.I)


def sem_acento(texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn"
    ).upper()


def baixar_ics(ano: int) -> str:
    resultado = subprocess.run(
        ["curl", "-sS", "-L", "-A", UA, "-m", "60", f"{ICS_URL}?ano={ano}"],
        capture_output=True,
        text=True,
        check=True,
    )
    if "BEGIN:VCALENDAR" not in resultado.stdout:
        raise RuntimeError(
            "Resposta do TRT16 não parece um iCal. Confira a URL e a conectividade."
        )
    return resultado.stdout


def parsear(ics: str) -> list[tuple[date, date, str, str]]:
    ics = re.sub(r"\r?\n[ \t]", "", ics)  # desdobra linhas continuadas (RFC 5545)
    eventos = []
    for bloco in re.findall(r"BEGIN:VEVENT(.*?)END:VEVENT", ics, re.S):

        def campo(nome: str) -> str:
            m = re.search(rf"^{nome}[^:]*:(.*)$", bloco, re.M)
            return m.group(1).strip() if m else ""

        d1, d2 = campo("DTSTART"), campo("DTEND")
        if not d1:
            continue
        # O tribunal grava 00h local como 03h UTC. Somar 3h devolve a data local.
        ini = (datetime.strptime(d1[:8], "%Y%m%d") + timedelta(hours=3)).date()
        fim = (
            (datetime.strptime(d2[:8], "%Y%m%d") + timedelta(hours=3)).date()
            if d2
            else ini
        )
        eventos.append((ini, fim, campo("SUMMARY"), campo("LOCATION")))
    return eventos


def aplicavel(local: str, municipio: str) -> bool:
    alvo = sem_acento(local)
    return "TODA A 16" in alvo or sem_acento(municipio) in alvo


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ano", type=int, default=date.today().year)
    ap.add_argument("--municipio", default="São Luís")
    ap.add_argument("--saida", default=None)
    args = ap.parse_args()

    ics = baixar_ics(args.ano)
    eventos = parsear(ics)
    if not eventos:
        print("Nenhum evento no iCal. Nada gerado.", file=sys.stderr)
        return 1

    locais: dict[str, str] = {}
    for ini, fim, resumo, local in eventos:
        if IGNORAR.search(resumo) or not aplicavel(local, args.municipio):
            continue
        # DTEND no iCal é exclusivo: o último dia do evento é fim - 1.
        ultimo = max(ini, fim - timedelta(days=1))
        dia = ini
        while dia <= ultimo:
            if dia.year == args.ano:
                escopo = "" if "TODA A 16" in sem_acento(local) else f" [{local}]"
                locais[dia.isoformat()] = f"{resumo}{escopo}"
            dia += timedelta(days=1)

    chave = f"TRT16-{sem_acento(args.municipio).lower().replace(' ', '-')}"
    destino = Path(args.saida or RAIZ / "core" / "calendarios" / f"{chave}.json")

    conteudo = {
        "_comentario": (
            f"GERADO por tools/importar_calendario_trt16.py em "
            f"{date.today():%d/%m/%Y}. Não edite à mão: regenere."
        ),
        "_fonte": f"{ICS_URL}?ano={args.ano}",
        "_consultado_em": date.today().isoformat(),
        "nome": f"TRT da 16ª Região — {args.municipio} ({args.ano})",
        "justica_federal": False,
        "aplicar_recesso": True,
        # O iCal do TRT16 já traz carnaval, Semana Santa e Corpus Christi com as
        # datas que o próprio tribunal adota. Não somar as móveis genéricas, sob
        # pena de duplicar ou divergir da fonte.
        "considerar_moveis": [],
        "locais": dict(sorted(locais.items())),
        "confirmado": True,
        "observacoes": (
            f"Importado do calendário institucional oficial do TRT16 para {args.ano}, "
            f"filtrado por abrangência regional e pelo município de {args.municipio}. "
            "Plantões judiciais foram excluídos por não retirarem expediente. "
            "Ponto facultativo e inspeção judicial constam como dias sem expediente, "
            "conforme o próprio tribunal publica. Regenere a cada ano judiciário."
        ),
    }
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(
        json.dumps(conteudo, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Calendário gerado: {destino}")
    print(f"Ano {args.ano} | município {args.municipio} | {len(locais)} dias sem expediente\n")
    for iso, desc in sorted(locais.items()):
        d = date.fromisoformat(iso)
        print(f"  {d:%d/%m} ({['seg','ter','qua','qui','sex','sáb','dom'][d.weekday()]})  {desc[:70]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
