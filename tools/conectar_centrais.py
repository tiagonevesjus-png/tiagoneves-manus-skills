#!/usr/bin/env python3
"""Liga o sistema às centrais HTML do kit do notebook.

Procura a pasta do kit (ou usa a indicada em --kit), e em cada uma:

1. grava `tnadv_ponte/` com o script da ponte, o estilo e `tnadv_dados.js`
   (calendários forenses do sistema e, havendo acervo, agenda e prazos);
2. grava `PAINEL_TNADV.html`, ponto de entrada comum;
3. liga cada central com um bloco de quatro linhas antes de </body>, depois de
   guardar a cópia original em `*.antes-da-ponte.html`.

Rodar de novo só atualiza os dados. --desconectar tira o bloco das centrais.
Nada é apagado, e pasta temporária (como a que o Windows cria ao abrir arquivo
de dentro de um .zip) é recusada.

Exemplos:
    python tools/conectar_centrais.py
    python tools/conectar_centrais.py --kit "C:\\Users\\usuario\\OneDrive\\Desktop\\Kit_Completo_Automacao_Notebook_TNADV_v2_Multi_IA"
    python tools/conectar_centrais.py --simular
    python tools/conectar_centrais.py --desconectar
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core import ponte  # noqa: E402
from core.acervo import ARQUIVO_PADRAO, Acervo  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--kit", action="append", type=Path,
                    help="pasta do kit (pode repetir). Sem ela, procura nos lugares de costume.")
    ap.add_argument("--acervo", type=Path, default=ARQUIVO_PADRAO,
                    help="acervo do sistema (padrão: data/acervo.json)")
    ap.add_argument("--completo", action="store_true",
                    help="inclui nome do cliente, local e observações da audiência nos dados "
                         "das centrais. Sem esta opção vai só número, órgão, data e providência.")
    ap.add_argument("--planilha", action="store_true",
                    help="gera a planilha de controle (traz nome de cliente) e põe link no painel")
    ap.add_argument("--desconectar", action="store_true", help="tira a ponte das centrais")
    ap.add_argument("--simular", action="store_true", help="mostra o que faria, sem gravar nada")
    ap.add_argument("--abrir", action="store_true", help="abre o painel no navegador ao final")
    args = ap.parse_args(argv)

    # Quem arrasta a própria central para --kit quer dizer a pasta dela.
    kits = [k.parent if k.is_file() else k for k in (args.kit or ponte.kits_padrao())]
    if not kits:
        print(
            "Nenhuma pasta do kit encontrada nos lugares de costume (Área de Trabalho, "
            "com ou sem OneDrive, e Documentos\\TNADV_Automacao).\n"
            "Indique a pasta com --kit \"caminho\\da\\pasta\".",
            file=sys.stderr,
        )
        return 1

    if args.desconectar:
        for kit in kits:
            print("\n".join(ponte.desconectar_kit(kit, simular=args.simular)))
        return 0

    hoje = date.today()
    acervo = Acervo.carregar(args.acervo)
    dados = ponte.montar_dados(hoje, acervo, completo=args.completo)

    planilha_gerada: Path | None = None
    if args.planilha:
        if not acervo.processos:
            print("Acervo vazio: planilha não gerada.")
        elif not args.simular:
            from core import planilha  # openpyxl só é exigido aqui

            destino = ponte.RAIZ / "saida" / f"Controle Processual - {hoje:%Y-%m-%d}.xlsx"
            planilha_gerada = planilha.gerar(acervo, destino, hoje=hoje)

    codigo = 0
    for kit in kits:
        try:
            linhas = ponte.conectar_kit(
                kit, dados, simular=args.simular, planilha=planilha_gerada,
            )
        except (ValueError, OSError) as erro:
            print(f"{kit}: {erro}", file=sys.stderr)
            codigo = 1
            continue
        print("\n".join(linhas))
        painel = Path(kit) / ponte.PAINEL
        if args.abrir and not args.simular and painel.exists():
            webbrowser.open(painel.resolve().as_uri())

    a = dados["acervo"]
    print(
        f"\nDados: {len(dados['calendarios'])} calendários; acervo com {a['processos']} "
        f"processo(s), {len(a['prazos'])} prazo(s) em aberto e {len(a['agenda'])} "
        f"audiência(s) nos próximos {a['janela_dias']} dias."
    )
    if not a["disponivel"]:
        print(f"Acervo vazio ou ausente em {args.acervo}: as centrais mostram só os calendários.")
    return codigo


if __name__ == "__main__":
    raise SystemExit(main())
