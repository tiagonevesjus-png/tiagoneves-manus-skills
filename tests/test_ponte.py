"""Testes da ponte entre o sistema e as centrais HTML do kit.

A ponte altera arquivo que não é deste repositório (as centrais, na pasta do
kit). Por isso os testes travam: que a alteração é um bloco delimitado,
reversível sem resto; que rodar duas vezes não duplica nada; que a cópia
original é guardada; que pasta temporária é recusada; e que dado de cliente só
vai para as centrais por decisão expressa.
"""

import json
import re
import shutil
import subprocess
from datetime import date, datetime
from pathlib import Path

import pytest

from core import cnj, identidade, ponte
from core.acervo import Acervo, Audiencia, Prazo
from core.feriados import Calendario

HOJE = date(2026, 11, 3)

PAGINA = """<!DOCTYPE html>
<html lang="pt-BR">
<head><meta charset="UTF-8"><title>Central</title></head>
<body>
<main><p>Processo 0000001-21.2026.8.10.0001</p></main>
<script>var x = 1;</script>
</body>
</html>
"""


def _numero(seq: str, j: str = "8", tr: str = "10") -> str:
    return f"{seq}-{cnj.gerar_digito(seq, '2026', j, tr, '0001')}.2026.{j}.{tr}.0001"


@pytest.fixture
def kit(tmp_path: Path) -> Path:
    """Pasta do kit como está no notebook: uma central na raiz, outra no pacote."""
    raiz = tmp_path / "Kit_Completo_Automacao_Notebook_TNADV_v2_Multi_IA"
    pacote = raiz / "Pacote_Multi_IA_Claude_ChatGPT_TNADV"
    pacote.mkdir(parents=True)
    (raiz / ponte.PAGINAS["automacao"]).write_text(PAGINA, encoding="utf-8")
    (pacote / ponte.PAGINAS["multi_ia"]).write_text(PAGINA, encoding="utf-8")
    return raiz


@pytest.fixture
def acervo() -> Acervo:
    a = Acervo()
    proc = a.obter_ou_criar(_numero("0000001"), cliente="Cliente Sigiloso LTDA",
                            orgao="1º Juizado Cível")
    proc.registrar_prazo(Prazo(
        descricao="Contestação", vencimento_estimado="2026-11-05", evento="2026-10-20",
        termo_inicial="dje_disponibilizacao", regime="cpc_dias_uteis", dias=15,
    ))
    proc.registrar_prazo(Prazo(
        descricao="Manifestação vencida", vencimento_estimado="2026-11-01",
        evento="2026-10-10", termo_inicial="publicacao", regime="cpc_dias_uteis", dias=5,
    ))
    proc.registrar_audiencia(Audiencia(
        data="2026-11-10", hora="09:00", tipo="una", modalidade="telepresencial",
        local="https://exemplo.invalid/sala?pwd=segredo", observacoes="Levar preposto",
    ))
    return a


# --- Bloco na página -------------------------------------------------------


def test_inserir_e_remover_devolve_a_pagina_identica():
    ligada = ponte.inserir_ponte(PAGINA, "../", "multi_ia")
    assert ponte.esta_ligada(ligada)
    assert ponte.remover_ponte(ligada) == PAGINA


def test_inserir_duas_vezes_nao_duplica():
    uma = ponte.inserir_ponte(PAGINA, "", "automacao")
    duas = ponte.inserir_ponte(uma, "", "automacao")
    assert uma == duas
    assert duas.count(ponte.MARCA_INICIO) == 1


def test_bloco_fica_antes_de_body_e_depois_dos_scripts_da_pagina():
    ligada = ponte.inserir_ponte(PAGINA, "", "automacao")
    assert ligada.index("var x = 1;") < ligada.index(ponte.MARCA_INICIO) < ligada.index("</body>")


def test_caminhos_do_bloco_partem_da_pasta_da_pagina():
    bloco = ponte.bloco_ponte("../", "multi_ia")
    assert 'href="../tnadv_ponte/tnadv_ponte.css"' in bloco
    assert 'src="../tnadv_ponte/tnadv_dados.js"' in bloco
    assert 'data-pagina="multi_ia" data-raiz="../"' in bloco


def test_quebra_de_linha_windows_e_preservada():
    crlf = PAGINA.replace("\n", "\r\n")
    ligada = ponte.inserir_ponte(crlf, "", "automacao")
    assert "\n" not in ligada.replace("\r\n", "")
    assert ponte.remover_ponte(ligada) == crlf


def test_pagina_sem_body_e_recusada():
    with pytest.raises(ValueError):
        ponte.inserir_ponte("<html><p>sem corpo</p></html>", "", "automacao")


# --- Pastas ----------------------------------------------------------------


@pytest.mark.parametrize("caminho", [
    "C:/Users/usuario/AppData/Local/Temp/1a2b3c4d_Kit_Completo_Automacao_Notebook_TNADV.zip.ec6",
    "C:/Users/usuario/Downloads/Kit_Completo_Automacao_Notebook_TNADV.zip",
])
def test_pasta_temporaria_e_reconhecida(caminho):
    assert ponte.em_pasta_temporaria(Path(caminho))


def test_area_de_trabalho_nao_e_pasta_temporaria():
    pasta = Path("C:/Users/usuario/OneDrive/Desktop/Kit_Completo_Automacao_Notebook_TNADV_v2_Multi_IA")
    assert not ponte.em_pasta_temporaria(pasta)


def test_conectar_recusa_pasta_temporaria(tmp_path):
    # tmp_path fica dentro da pasta temporária do sistema.
    with pytest.raises(ValueError, match="temporária"):
        ponte.conectar_kit(tmp_path, ponte.montar_dados(HOJE))


def test_localiza_as_duas_centrais_e_calcula_o_prefixo(kit):
    achadas = ponte.localizar_centrais(kit)
    assert set(achadas) == {"automacao", "multi_ia"}
    assert ponte.prefixo_ate_o_kit(achadas["automacao"], kit) == ""
    assert ponte.prefixo_ate_o_kit(achadas["multi_ia"], kit) == "../"


def test_kits_padrao_acha_desktop_do_onedrive_e_pasta_do_instalador(tmp_path, kit):
    home = kit.parent
    destino = home / "OneDrive" / "Desktop" / kit.name
    destino.parent.mkdir(parents=True)
    shutil.move(str(kit), destino)
    instalado = home / "Documents" / "TNADV_Automacao"
    instalado.mkdir(parents=True)
    (instalado / ponte.PAGINAS["automacao"]).write_text(PAGINA, encoding="utf-8")
    vazio = home / "Desktop" / ponte.NOMES_KIT[1]
    vazio.mkdir(parents=True)  # pasta do kit sem central: fica de fora
    achados = ponte.kits_padrao(home=home, ambiente={})
    assert achados == [destino, instalado]


# --- Dados -----------------------------------------------------------------


def test_calendarios_passam_os_dias_parados_do_motor():
    cals = {c["chave"]: c for c in ponte.calendarios_para_ponte(HOJE)}
    for chave in ("TJMA-sao-luis", "TRT16-sao-luis"):
        cal = Calendario.carregar(chave)
        dados = cals[chave]
        assert dados["anos"] == [2026, 2027]
        for iso, motivo in dados["nao_uteis"].items():
            dia = date.fromisoformat(iso)
            assert dia.weekday() < 5
            assert cal.motivo_nao_util(dia) == motivo
    # A divergência entre tribunais chega intacta à calculadora da central.
    assert "2026-07-28" in cals["TJMA-sao-luis"]["nao_uteis"]
    assert "2026-07-28" not in cals["TRT16-sao-luis"]["nao_uteis"]
    assert "2026-07-27" in cals["TRT16-sao-luis"]["nao_uteis"]


def test_calendario_sem_ano_seguinte_leva_o_aviso():
    cals = {c["chave"]: c for c in ponte.calendarios_para_ponte(HOJE)}
    assert any("2027" in a and "não cobre" in a for a in cals["TJMA-sao-luis"]["avisos"])


def test_calendarios_confirmados_vem_primeiro():
    cals = ponte.calendarios_para_ponte(HOJE)
    estados = [c["confirmado"] for c in cals]
    assert estados == sorted(estados, reverse=True)
    assert not any(c["chave"].startswith("MODELO") for c in cals)


def test_por_padrao_nao_vai_nome_de_cliente_nem_local_da_audiencia(acervo):
    dados = ponte.acervo_para_ponte(acervo, HOJE)
    texto = json.dumps(dados, ensure_ascii=False)
    assert "Cliente Sigiloso" not in texto
    assert "segredo" not in texto
    assert "preposto" not in texto
    assert dados["agenda"][0]["cnj"] == _numero("0000001")


def test_completo_inclui_cliente_local_e_observacoes(acervo):
    dados = ponte.acervo_para_ponte(acervo, HOJE, completo=True)
    assert dados["prazos"][0]["cliente"] == "Cliente Sigiloso LTDA"
    assert dados["agenda"][0]["local"].endswith("pwd=segredo")
    assert dados["agenda"][0]["observacoes"] == "Levar preposto"


def test_prazo_vencido_aparece_com_dias_negativos(acervo):
    dados = ponte.acervo_para_ponte(acervo, HOJE)
    prazos = {p["providencia"]: p for p in dados["prazos"]}
    assert prazos["Manifestação vencida"]["dias_restantes"] == -2
    assert prazos["Contestação"]["dias_restantes"] == 2
    assert prazos["Contestação"]["regime"] == "CPC, dias úteis"
    assert dados["contagem"] == {"vermelho": 2, "amarelo": 0, "verde": 0}
    assert dados["nao_conferidos"] == 2


def test_acervo_vazio_e_declarado():
    dados = ponte.acervo_para_ponte(Acervo(), HOJE)
    assert dados["disponivel"] is False
    assert dados["prazos"] == [] and dados["agenda"] == []


def test_script_de_dados_nao_fecha_a_tag_script(acervo):
    proc = next(iter(acervo.processos.values()))
    proc.cliente = "</script><script>alert(1)</script>\u2028"
    dados = ponte.montar_dados(HOJE, acervo, completo=True, agora=datetime(2026, 11, 3, 8, 0))
    js = ponte.dados_para_js(dados)
    assert "</script" not in js
    assert "\u2028" not in js
    corpo = js[js.index("window.TNADV_DADOS = ") + len("window.TNADV_DADOS = "):].rstrip().rstrip(";")
    assert json.loads(corpo)["acervo"]["prazos"][0]["cliente"].startswith("</script>")


# --- Ponta a ponta numa pasta de kit -----------------------------------------


def test_conectar_grava_ponte_painel_e_liga_as_duas_centrais(kit, acervo):
    dados = ponte.montar_dados(HOJE, acervo)
    relatorio = ponte.conectar_kit(kit, dados, checar_temporaria=False)
    assert (kit / ponte.PAINEL).exists()
    for nome in (*ponte.ARQUIVOS_FIXOS, ponte.ARQUIVO_DADOS):
        assert (kit / ponte.PASTA_PONTE / nome).exists()
    js = (kit / ponte.PASTA_PONTE / ponte.ARQUIVO_DADOS).read_text(encoding="utf-8")
    assert '"multi_ia": "Pacote_Multi_IA_Claude_ChatGPT_TNADV/central_multi_ia_mobile_tnadv.html"' in js
    for chave, pagina in ponte.localizar_centrais(kit).items():
        html = pagina.read_text(encoding="utf-8")
        assert ponte.esta_ligada(html), chave
        backup = pagina.with_name(pagina.stem + ponte.SUFIXO_BACKUP)
        assert backup.read_text(encoding="utf-8") == PAGINA
    assert any("ligada" in linha for linha in relatorio)


def test_rodar_de_novo_so_atualiza_os_dados(kit, acervo):
    ponte.conectar_kit(kit, ponte.montar_dados(HOJE), checar_temporaria=False)
    pagina = kit / ponte.PAGINAS["automacao"]
    primeira = pagina.read_text(encoding="utf-8")
    relatorio = ponte.conectar_kit(kit, ponte.montar_dados(HOJE, acervo), checar_temporaria=False)
    assert pagina.read_text(encoding="utf-8") == primeira
    assert any("já estava ligada" in linha for linha in relatorio)
    backup = pagina.with_name(pagina.stem + ponte.SUFIXO_BACKUP)
    assert backup.read_text(encoding="utf-8") == PAGINA


def test_desconectar_devolve_as_centrais_e_nao_apaga_nada(kit):
    ponte.conectar_kit(kit, ponte.montar_dados(HOJE), checar_temporaria=False)
    ponte.desconectar_kit(kit)
    for pagina in ponte.localizar_centrais(kit).values():
        assert pagina.read_text(encoding="utf-8") == PAGINA
    assert (kit / ponte.PASTA_PONTE / ponte.ARQUIVO_DADOS).exists()
    assert (kit / ponte.PAINEL).exists()


def test_simular_nao_grava_nada(kit):
    antes = sorted(p.relative_to(kit) for p in kit.rglob("*"))
    relatorio = ponte.conectar_kit(kit, ponte.montar_dados(HOJE), simular=True,
                                   checar_temporaria=False)
    assert sorted(p.relative_to(kit) for p in kit.rglob("*")) == antes
    assert any("ligaria" in linha for linha in relatorio)


def test_bom_utf8_da_pagina_e_preservado(kit):
    pagina = kit / ponte.PAGINAS["automacao"]
    pagina.write_bytes(b"\xef\xbb\xbf" + PAGINA.encode("utf-8"))
    ponte.conectar_kit(kit, ponte.montar_dados(HOJE), checar_temporaria=False)
    assert pagina.read_bytes().startswith(b"\xef\xbb\xbf")


def test_ferramenta_de_linha_de_comando(kit, monkeypatch, capsys):
    import importlib.util

    caminho = Path(__file__).resolve().parent.parent / "tools" / "conectar_centrais.py"
    spec = importlib.util.spec_from_file_location("conectar_centrais", caminho)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(ponte, "em_pasta_temporaria", lambda _: False)
    assert modulo.main(["--kit", str(kit), "--acervo", str(kit / "nao-existe.json")]) == 0
    saida = capsys.readouterr().out
    # Arquivo inexistente é "não encontrado", não "vazio": a central diz qual dos dois.
    assert "Acervo não encontrado" in saida
    assert ponte.esta_ligada((kit / ponte.PAGINAS["automacao"]).read_text(encoding="utf-8"))


# --- Arquivos de navegador ---------------------------------------------------


def test_estilo_da_ponte_usa_as_cores_do_escritorio():
    css = (ponte.ASSETS / "tnadv_ponte.css").read_text(encoding="utf-8").upper()
    for cor in (identidade.AZUL_MARINHO, identidade.AZUL_ESCURO, identidade.DOURADO,
                identidade.DOURADO_CLARO, identidade.PAPEL, identidade.CINZA_BORDA):
        assert cor.upper() in css, cor
    for nivel in identidade.URGENCIA.values():
        for chave in ("faixa", "fundo", "texto"):
            assert nivel[chave].upper() in css


def test_arquivos_de_navegador_nao_carregam_nada_de_fora():
    for nome in (*ponte.ARQUIVOS_FIXOS, ponte.PAINEL):
        texto = (ponte.ASSETS / nome).read_text(encoding="utf-8")
        assert not re.search(r"https?://", texto), nome
        assert "fetch(" not in texto and "XMLHttpRequest" not in texto, nome


@pytest.mark.skipif(shutil.which("node") is None, reason="node não instalado")
def test_digito_verificador_do_navegador_bate_com_o_do_sistema(tmp_path):
    # Números fictícios, escolhidos para cobrir extremos de cada campo.
    numeros = [
        ("0000001", "2026", "8", "10", "0001"), ("1234567", "2026", "5", "16", "0003"),
        ("9999999", "1999", "4", "01", "9999"), ("0800123", "2025", "8", "10", "0040"),
        ("0000000", "2000", "1", "00", "0000"),
    ]
    roteiro = tmp_path / "roda.js"
    roteiro.write_text(
        "global.window = {};\n"
        "global.document = { currentScript: null, readyState: 'loading',"
        " addEventListener: function () {} };\n"
        f"require({json.dumps(str(ponte.ASSETS / 'tnadv_ponte.js'))});\n"
        f"var casos = {json.dumps(numeros)};\n"
        "console.log(JSON.stringify(casos.map(function (c) {"
        " return window.TNADV_PONTE.dvEsperado.apply(null, c); })));\n",
        encoding="utf-8",
    )
    saida = subprocess.run(["node", str(roteiro)], capture_output=True, text=True, check=True)
    calculados = json.loads(saida.stdout)
    assert calculados == [cnj.gerar_digito(*c) for c in numeros]
