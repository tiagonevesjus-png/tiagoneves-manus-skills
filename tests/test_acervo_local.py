"""O acervo mora no notebook, junto do sistema (decisão de 03/11/2026).

Estes testes travam o que sustenta a decisão: gravar o acervo padrão fora do
notebook falha com aviso, em vez de sumir em silêncio; acervo ausente não se
confunde com acervo vazio; a gravação não deixa o arquivo pela metade e guarda a
versão anterior; e pasta copiada para a nuvem é reconhecida para aviso.
"""

import json
from pathlib import Path

import pytest

from core import acervo as modulo
from core.acervo import Acervo, AcervoForaDoNotebook, Prazo, ambiente_temporario, pasta_sincronizada

MARCAS = ("CLAUDE_CODE_CONTAINER_ID", "CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE", "GITHUB_ACTIONS")


@pytest.fixture
def no_notebook(monkeypatch, tmp_path):
    """Ambiente sem marca de nuvem, com o acervo padrão numa pasta de teste."""
    for marca in MARCAS:
        monkeypatch.delenv(marca, raising=False)
    padrao = tmp_path / "sistema" / "data" / "acervo.json"
    monkeypatch.setattr(modulo, "ARQUIVO_PADRAO", padrao)
    return padrao


def _com_um_prazo() -> Acervo:
    a = Acervo()
    a.obter_ou_criar("0000001-21.2026.8.10.0001").registrar_prazo(Prazo(
        descricao="Contestação", vencimento_estimado="2026-11-20", evento="2026-11-03",
        termo_inicial="dje_disponibilizacao", regime="cpc_dias_uteis", dias=15,
    ))
    return a


# --- Onde roda ---------------------------------------------------------------


def test_sessao_na_nuvem_e_reconhecida():
    assert ambiente_temporario({"CLAUDE_CODE_CONTAINER_ID": "container_x"})
    assert ambiente_temporario({"CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE": "cloud_default"})
    assert ambiente_temporario({"GITHUB_ACTIONS": "true"})


def test_notebook_nao_tem_marca_de_ambiente_temporario():
    assert ambiente_temporario({}) is None
    # Sessão remota ligada ao notebook roda os comandos lá, sem contêiner.
    assert ambiente_temporario({"CLAUDE_CODE_REMOTE": "true"}) is None


def test_gravar_acervo_padrao_na_nuvem_falha_sem_gravar(no_notebook, monkeypatch):
    monkeypatch.setenv("CLAUDE_CODE_CONTAINER_ID", "container_teste")
    with pytest.raises(AcervoForaDoNotebook, match="mora no notebook"):
        _com_um_prazo().salvar()
    assert not no_notebook.exists()
    assert not no_notebook.parent.exists() or not any(no_notebook.parent.iterdir())


def test_na_nuvem_outro_caminho_continua_gravando(no_notebook, monkeypatch, tmp_path):
    """Teste, simulação e exportação gravam fora do acervo padrão, e podem."""
    monkeypatch.setenv("CLAUDE_CODE_CONTAINER_ID", "container_teste")
    destino = _com_um_prazo().salvar(tmp_path / "copia.json")
    assert destino.exists()


def test_permissao_expressa_libera_a_gravacao(no_notebook, monkeypatch):
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    _com_um_prazo().salvar(permitir_ambiente_temporario=True)
    assert no_notebook.exists()


def test_no_notebook_grava_no_lugar_padrao(no_notebook):
    caminho = _com_um_prazo().salvar()
    assert caminho == no_notebook
    assert Acervo.carregar().processos


# --- Ausente não é vazio -------------------------------------------------------


def test_acervo_ausente_e_declarado(no_notebook):
    a = Acervo.carregar()
    assert a.encontrado is False
    assert a.origem == str(no_notebook)
    assert not a.processos


def test_acervo_existente_sem_processo_e_encontrado(no_notebook):
    Acervo().salvar()
    a = Acervo.carregar()
    assert a.encontrado is True and not a.processos


def test_ponte_leva_a_diferenca_para_as_centrais(no_notebook):
    from datetime import date

    from core import ponte

    ausente = ponte.acervo_para_ponte(Acervo.carregar(), date(2026, 11, 3))
    assert ausente["encontrado"] is False and ausente["disponivel"] is False
    Acervo().salvar()
    vazio = ponte.acervo_para_ponte(Acervo.carregar(), date(2026, 11, 3))
    assert vazio["encontrado"] is True and vazio["disponivel"] is False


# --- Gravação segura -------------------------------------------------------------


def test_gravacao_guarda_a_versao_anterior_e_nao_deixa_provisorio(no_notebook):
    primeiro = _com_um_prazo()
    primeiro.salvar()
    conteudo_antigo = no_notebook.read_text(encoding="utf-8")
    segundo = Acervo.carregar()
    segundo.obter_ou_criar("0000002-87.2026.5.16.0001")
    segundo.salvar()
    anterior = no_notebook.with_name("acervo.anterior.json")
    assert anterior.read_text(encoding="utf-8") == conteudo_antigo
    assert len(json.loads(no_notebook.read_text(encoding="utf-8"))["processos"]) == 2
    assert not list(no_notebook.parent.glob("*.gravando"))


def test_primeira_gravacao_nao_cria_versao_anterior(no_notebook):
    _com_um_prazo().salvar()
    assert not no_notebook.with_name("acervo.anterior.json").exists()


# --- Pasta copiada para a nuvem ----------------------------------------------------


@pytest.mark.parametrize("caminho, esperado", [
    ("C:/Users/usuario/OneDrive/Desktop/sistema/data", "OneDrive"),
    ("C:/Users/usuario/OneDrive - Escritorio/sistema/data", "OneDrive"),
    ("G:/Meu Drive/sistema/data", "Google Drive"),
    ("C:/Users/usuario/Dropbox/sistema/data", "Dropbox"),
])
def test_pasta_sincronizada_pelo_nome(caminho, esperado):
    assert pasta_sincronizada(Path(caminho), home=Path("C:/Users/usuario"), ambiente={}) == esperado


def test_pasta_sincronizada_pela_variavel_do_onedrive(tmp_path):
    base = tmp_path / "Nuvem Pessoal"
    assert pasta_sincronizada(base / "sistema", home=tmp_path / "casa",
                              ambiente={"OneDrive": str(base)}) == "OneDrive"


def test_area_de_trabalho_e_documentos_geram_aviso(tmp_path):
    for nome in ("Desktop", "Documents", "Documentos"):
        aviso = pasta_sincronizada(tmp_path / nome / "sistema", home=tmp_path, ambiente={})
        assert aviso and nome in aviso


def test_pasta_sugerida_para_o_sistema_nao_gera_aviso(tmp_path):
    assert pasta_sincronizada(tmp_path / "TNADV" / "sistema" / "data",
                              home=tmp_path, ambiente={}) is None
