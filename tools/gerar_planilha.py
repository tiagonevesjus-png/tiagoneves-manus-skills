#!/usr/bin/env python3
"""Gera a planilha viva de controle processual a partir do acervo."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import planilha  # noqa: E402
from core.acervo import ARQUIVO_PADRAO, Acervo  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--acervo", default=str(ARQUIVO_PADRAO), help="caminho do acervo.json")
    ap.add_argument(
        "--saida",
        default=f"saida/Controle Processual - {date.today():%Y-%m-%d}.xlsx",
        help="caminho do xlsx a gerar",
    )
    args = ap.parse_args()

    acervo = Acervo.carregar(args.acervo)
    if not acervo.processos:
        print(f"Acervo vazio em {args.acervo}. Nada a gerar.", file=sys.stderr)
        return 1

    destino = planilha.gerar(acervo, args.saida)
    pendentes = acervo.nao_conferidos()
    print(f"Planilha gerada: {destino}")
    print(f"Processos: {len(acervo.processos)}")
    print(f"Prazos pendentes de conferência humana: {len(pendentes)}")
    if pendentes:
        print("\nATENÇÃO — os prazos abaixo são estimativas ainda não conferidas:")
        for proc, prz in pendentes[:20]:
            print(f"  {prz.vencimento_estimado}  {proc.numero}  {prz.descricao}")
        if len(pendentes) > 20:
            print(f"  ... e mais {len(pendentes) - 20}. Veja a aba Conferência.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
