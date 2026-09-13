#!/usr/bin/env python3
"""Gera o arquivo de filtros do Gmail com a taxonomia TNADV.

O arquivo produzido é importado em Gmail, Configurações, Filtros e endereços
bloqueados, Importar filtros. A partir daí o próprio Google aplica os rótulos
em toda mensagem que chega, sem automação externa.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.filtros_gmail import escrever, regras_tnadv, validar_regras  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--saida",
        default="saida/filtros-tnadv-gmail.xml",
        help="caminho do XML a gerar",
    )
    args = ap.parse_args()

    filtros = regras_tnadv()
    problemas = validar_regras(filtros)
    if problemas:
        print("Regras inválidas; nada foi gerado:", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        return 1

    destino = escrever(filtros, args.saida)
    print(f"Filtros gerados: {destino}")
    print(f"Total: {len(filtros)} regras\n")
    for f in filtros:
        print(f"  {f.rotulo:<24} {f.descricao}")
    print(
        "\nNenhuma regra arquiva, marca como lida, exclui ou encaminha. "
        "Filtro TNADV só rotula.\n"
        "Importe em: Gmail > Configurações > Filtros e endereços bloqueados > "
        "Importar filtros."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
