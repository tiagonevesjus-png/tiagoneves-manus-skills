"""Acervo processual: modelo de dados e persistência incremental.

O acervo é um arquivo JSON (`data/acervo.json`). Ele é a fonte de verdade das
automações: o radar de intimações escreve nele, a planilha viva lê dele, e o
dashboard diário cruza os dois.

Onde ele mora (decisão do advogado, 03/11/2026): no notebook, em `data/` da
cópia local do sistema, fora de pasta sincronizada com nuvem. Não vai para o
GitHub (o `.gitignore` bloqueia `data/`) nem para sessão na nuvem, cujo
contêiner é apagado ao fim. Por isso `salvar()` recusa gravar o acervo padrão
quando roda num ambiente desses: melhor um erro claro do que um registro que
some sem aviso.

Sobre LGPD: mantenha em `data/` apenas o mínimo necessário à gestão do prazo
(número, órgão, partes, movimento, prazo). Documentos e dados sensíveis de
cliente permanecem no repositório de arquivos do escritório, não aqui.
"""

from __future__ import annotations

import json
import os
import shutil
from collections.abc import Mapping
from dataclasses import asdict, dataclass, field
from datetime import date, datetime
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ARQUIVO_PADRAO = RAIZ / "data" / "acervo.json"


class AcervoForaDoNotebook(RuntimeError):
    """Gravação do acervo padrão num ambiente que não o guarda."""


def ambiente_temporario(ambiente: Mapping[str, str] | None = None) -> str | None:
    """Motivo pelo qual este ambiente não guarda o acervo, ou None.

    Sessão do Claude na nuvem roda num contêiner apagado ao fim; a integração
    contínua do GitHub também. Sessão no notebook (app Claude, ou
    `claude remote-control` na pasta do sistema) não tem nenhuma das marcas.
    """
    amb = os.environ if ambiente is None else ambiente
    if amb.get("CLAUDE_CODE_CONTAINER_ID") or amb.get(
        "CLAUDE_CODE_REMOTE_ENVIRONMENT_TYPE", ""
    ).startswith("cloud"):
        return "uma sessão do Claude na nuvem, cujo contêiner é apagado ao fim da sessão"
    if amb.get("GITHUB_ACTIONS") == "true":
        return "a integração contínua do GitHub"
    return None


def _dentro(alvo: Path, base: Path) -> bool:
    """`alvo` está dentro de `base`? Sem diferenciar maiúscula, como no Windows."""
    a = [p.lower() for p in Path(alvo).absolute().parts]
    b = [p.lower() for p in Path(base).absolute().parts]
    return len(a) >= len(b) and a[: len(b)] == b


def pasta_sincronizada(
    caminho: Path | str,
    home: Path | None = None,
    ambiente: Mapping[str, str] | None = None,
) -> str | None:
    """Serviço de nuvem que provavelmente copia esta pasta, ou None.

    Serve para avisar, não para impedir: o que estiver numa pasta assim sai do
    notebook, ao contrário do que foi decidido para o acervo.
    """
    amb = os.environ if ambiente is None else ambiente
    alvo = Path(caminho)
    for var in ("OneDrive", "OneDriveConsumer", "OneDriveCommercial"):
        if amb.get(var) and _dentro(alvo, Path(amb[var])):
            return "OneDrive"
    partes = [p.lower() for p in alvo.absolute().parts]
    if any(p == "onedrive" or p.startswith("onedrive - ") for p in partes):
        return "OneDrive"
    if any(p in ("meu drive", "my drive", "google drive") for p in partes):
        return "Google Drive"
    if "dropbox" in partes:
        return "Dropbox"
    casa = home or Path.home()
    for nome in ("Desktop", "Área de Trabalho", "Documents", "Documentos"):
        if _dentro(alvo, casa / nome):
            return f"pasta {nome}, que o OneDrive e o Google Drive costumam copiar"
    return None

STATUS_PRAZO = ("aberto", "cumprido", "prorrogado", "perdido", "cancelado")
URGENCIAS = ("vermelho", "amarelo", "verde")


@dataclass
class Movimento:
    data: str                    # AAAA-MM-DD
    descricao: str
    fonte: str                   # "gmail", "datajud", "pje", "manual"
    id_externo: str = ""         # id da mensagem/movimento, para desduplicação
    teor: str = ""

    def chave(self) -> str:
        return self.id_externo or f"{self.data}|{self.descricao[:120]}"


@dataclass
class Prazo:
    descricao: str
    vencimento_estimado: str     # AAAA-MM-DD
    evento: str                  # AAAA-MM-DD, fato deflagrador
    termo_inicial: str
    regime: str
    dias: int
    base_legal: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    status: str = "aberto"
    conferido_por_humano: bool = False
    id_evento_agenda: str = ""

    def __post_init__(self) -> None:
        if self.status not in STATUS_PRAZO:
            raise ValueError(f"Status inválido: {self.status}. Use um de {STATUS_PRAZO}.")


@dataclass
class Audiencia:
    """Audiência designada.

    Não é prazo: tem data e hora certas, definidas pelo juízo, e não se calcula.
    Por isso vive em campo próprio, e não em `Prazo`.
    """

    data: str                    # AAAA-MM-DD
    hora: str = ""               # HH:MM
    tipo: str = ""               # una, instrução, conciliação, justificação
    local: str = ""              # sala, fórum, ou link se telepresencial
    modalidade: str = "presencial"   # presencial, telepresencial, híbrida
    observacoes: str = ""
    id_evento_agenda: str = ""
    confirmada_por_humano: bool = False

    def quando(self) -> str:
        d = date.fromisoformat(self.data)
        return f"{d:%d/%m/%Y}" + (f" às {self.hora}" if self.hora else "")


@dataclass
class Processo:
    numero: str                  # número CNJ formatado
    orgao: str = ""
    classe: str = ""
    assunto: str = ""
    cliente: str = ""
    polo: str = ""               # "ativo", "passivo", "terceiro"
    parte_contraria: str = ""
    valor_causa: str = ""
    calendario: str = "padrao-justica-estadual"
    situacao: str = "ativo"
    movimentos: list[Movimento] = field(default_factory=list)
    prazos: list[Prazo] = field(default_factory=list)
    audiencias: list[Audiencia] = field(default_factory=list)
    atualizado_em: str = ""

    def prazos_abertos(self) -> list[Prazo]:
        return [p for p in self.prazos if p.status == "aberto"]

    def audiencias_futuras(self, hoje: date | None = None) -> list[Audiencia]:
        ref = hoje or date.today()
        return sorted(
            (a for a in self.audiencias if date.fromisoformat(a.data) >= ref),
            key=lambda a: (a.data, a.hora),
        )

    def registrar_audiencia(self, aud: Audiencia) -> bool:
        """Adiciona a audiência se não houver outra na mesma data e hora."""
        if any(a.data == aud.data and a.hora == aud.hora for a in self.audiencias):
            return False
        self.audiencias.append(aud)
        self.audiencias.sort(key=lambda a: (a.data, a.hora))
        self.atualizado_em = datetime.now().isoformat(timespec="seconds")
        return True

    def proximo_vencimento(self) -> str | None:
        abertos = sorted(p.vencimento_estimado for p in self.prazos_abertos())
        return abertos[0] if abertos else None

    def registrar_movimento(self, mov: Movimento) -> bool:
        """Adiciona o movimento se ainda não existir. Devolve True se inseriu."""
        existentes = {m.chave() for m in self.movimentos}
        if mov.chave() in existentes:
            return False
        self.movimentos.append(mov)
        self.movimentos.sort(key=lambda m: m.data)
        self.atualizado_em = datetime.now().isoformat(timespec="seconds")
        return True

    def registrar_prazo(self, prazo: Prazo) -> bool:
        """Adiciona o prazo se não houver outro igual em aberto."""
        for p in self.prazos:
            if (
                p.status == "aberto"
                and p.descricao == prazo.descricao
                and p.evento == prazo.evento
            ):
                return False
        self.prazos.append(prazo)
        self.atualizado_em = datetime.now().isoformat(timespec="seconds")
        return True


@dataclass
class Acervo:
    processos: dict[str, Processo] = field(default_factory=dict)
    atualizado_em: str = ""
    # De onde o acervo foi lido. `encontrado` separa acervo vazio de acervo
    # ausente: numa sessão que não roda no notebook o arquivo não existe, e
    # isso não pode ser lido como "nenhum prazo".
    origem: str = field(default="", compare=False)
    encontrado: bool = field(default=False, compare=False)

    @classmethod
    def carregar(cls, caminho: Path | str | None = None) -> "Acervo":
        p = Path(caminho) if caminho is not None else ARQUIVO_PADRAO
        if not p.exists():
            return cls(origem=str(p), encontrado=False)
        dados = json.loads(p.read_text(encoding="utf-8"))
        processos = {}
        for numero, bruto in dados.get("processos", {}).items():
            movs = [Movimento(**m) for m in bruto.pop("movimentos", [])]
            prazos = [Prazo(**z) for z in bruto.pop("prazos", [])]
            auds = [Audiencia(**a) for a in bruto.pop("audiencias", [])]
            processos[numero] = Processo(
                **bruto, movimentos=movs, prazos=prazos, audiencias=auds
            )
        return cls(
            processos=processos, atualizado_em=dados.get("atualizado_em", ""),
            origem=str(p), encontrado=True,
        )

    def salvar(
        self,
        caminho: Path | str | None = None,
        *,
        permitir_ambiente_temporario: bool = False,
    ) -> Path:
        """Grava o acervo e devolve o caminho.

        Recusa gravar o acervo padrão fora do notebook (ver o início do
        módulo). A gravação passa por arquivo provisório e só então substitui
        o anterior, que fica guardado como `acervo.anterior.json`: queda de
        energia ou sincronização no meio não deixam o acervo pela metade.
        """
        p = Path(caminho) if caminho is not None else ARQUIVO_PADRAO
        motivo = ambiente_temporario()
        if motivo and not permitir_ambiente_temporario and _dentro(p, ARQUIVO_PADRAO):
            raise AcervoForaDoNotebook(
                f"O acervo mora no notebook, em data/{ARQUIVO_PADRAO.name} da "
                f"cópia local do sistema, e esta execução roda em {motivo}: o que "
                "fosse gravado aqui se perderia. Nada foi gravado. Registre pelo "
                "notebook (app Claude, ou claude remote-control na pasta do sistema)."
            )
        p.parent.mkdir(parents=True, exist_ok=True)
        self.atualizado_em = datetime.now().isoformat(timespec="seconds")
        payload = {
            "atualizado_em": self.atualizado_em,
            "processos": {n: asdict(proc) for n, proc in sorted(self.processos.items())},
        }
        provisorio = p.with_name(p.name + ".gravando")
        provisorio.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if p.exists():
            shutil.copy2(p, p.with_name(f"{p.stem}.anterior{p.suffix}"))
        os.replace(provisorio, p)
        self.origem, self.encontrado = str(p), True
        return p

    def obter_ou_criar(self, numero: str, **campos) -> Processo:
        if numero not in self.processos:
            self.processos[numero] = Processo(numero=numero, **campos)
        elif campos:
            proc = self.processos[numero]
            for chave, valor in campos.items():
                if valor and not getattr(proc, chave, ""):
                    setattr(proc, chave, valor)
        return self.processos[numero]

    def prazos_ate(self, limite: date) -> list[tuple[Processo, Prazo]]:
        """Prazos abertos com vencimento estimado até a data indicada, ordenados."""
        saida = [
            (proc, prz)
            for proc in self.processos.values()
            for prz in proc.prazos_abertos()
            if date.fromisoformat(prz.vencimento_estimado) <= limite
        ]
        return sorted(saida, key=lambda t: t[1].vencimento_estimado)

    def audiencias_ate(self, limite: date, hoje: date | None = None) -> list[tuple[Processo, Audiencia]]:
        """Audiências designadas de hoje até a data indicada, ordenadas."""
        ref = hoje or date.today()
        saida = [
            (proc, aud)
            for proc in self.processos.values()
            for aud in proc.audiencias
            if ref <= date.fromisoformat(aud.data) <= limite
        ]
        return sorted(saida, key=lambda t: (t[1].data, t[1].hora))

    def nao_conferidos(self) -> list[tuple[Processo, Prazo]]:
        """Prazos em aberto que ainda não passaram por conferência humana."""
        return [
            (proc, prz)
            for proc in self.processos.values()
            for prz in proc.prazos_abertos()
            if not prz.conferido_por_humano
        ]


def classificar_urgencia(vencimento: str, hoje: date | None = None) -> str:
    """Semáforo do dashboard: vermelho até 3 dias, amarelo até 10, verde acima."""
    ref = hoje or date.today()
    faltam = (date.fromisoformat(vencimento) - ref).days
    if faltam <= 3:
        return "vermelho"
    if faltam <= 10:
        return "amarelo"
    return "verde"
