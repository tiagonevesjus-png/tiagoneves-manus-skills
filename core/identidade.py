"""Identidade visual do escritório Tiago Neves Advocacia Empresarial.

Fonte única das cores, da tipografia e dos dados de rodapé. Planilha, dashboard
e qualquer saída visual futura leem daqui, para que a identidade não se
desencontre entre um artefato e outro.

Ao alterar uma cor, altere aqui e em lugar nenhum mais.
"""

from __future__ import annotations

from dataclasses import dataclass

# --- Paleta ---------------------------------------------------------------

AZUL_MARINHO = "#1B2A4A"   # cor institucional primária
AZUL_ESCURO = "#132038"    # variação para faixas e rodapé
DOURADO = "#C6A15B"        # cor de destaque
DOURADO_CLARO = "#E4D2AC"

BRANCO = "#FFFFFF"
PAPEL = "#F7F8FA"          # fundo da página
CINZA_BORDA = "#D8DEE7"
CINZA_TEXTO = "#4A5568"
GRAFITE = "#1F2937"        # corpo de texto

# Semáforo de urgência. Cada nível tem cor de faixa, de fundo e de texto, para
# que o contraste continue legível em tela e no papel.
URGENCIA = {
    "vermelho": {"faixa": "#B42318", "fundo": "#FEF3F2", "texto": "#7A271A", "rotulo": "AÇÃO IMEDIATA"},
    "amarelo": {"faixa": "#B54708", "fundo": "#FFFAEB", "texto": "#7A2E0E", "rotulo": "ESTA SEMANA"},
    "verde": {"faixa": "#067647", "fundo": "#F0FDF4", "texto": "#085D3A", "rotulo": "ACOMPANHAMENTO"},
}

# --- Tipografia -----------------------------------------------------------

# Garamond é a fonte das peças. Em tela e em e-mail, entra com cadeia de
# reserva, porque cliente de e-mail não carrega fonte externa.
SERIFA = "Garamond, 'EB Garamond', 'Times New Roman', Times, serif"
SANS = "'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
MONO = "'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace"


# --- Escritório -----------------------------------------------------------


@dataclass(frozen=True)
class Escritorio:
    """Dados institucionais que aparecem em cabeçalho e rodapé.

    Campos marcados como [DADO PENDENTE] não foram informados. Preencha-os aqui
    quando forem confirmados; nenhum outro arquivo precisa mudar.
    """

    nome: str = "Tiago Neves Advocacia Empresarial"
    advogado: str = "Tiago Luiz Rodrigues Neves"
    oab: str = "OAB/MA n.º 10.042"
    endereco: str = "[DADO PENDENTE]"
    telefone: str = "[DADO PENDENTE]"
    email: str = "tiagoneves.jus@gmail.com"
    site: str = "[DADO PENDENTE]"

    def rodape_contatos(self) -> str:
        """Linha de contatos, omitindo o que ainda não foi informado."""
        partes = [p for p in (self.endereco, self.telefone, self.email, self.site)
                  if p and not p.startswith("[DADO PENDENTE]")]
        return "  ·  ".join(partes)

    def pendencias(self) -> list[str]:
        """Campos institucionais ainda não preenchidos."""
        rotulos = {
            "endereco": "endereço", "telefone": "telefone",
            "email": "e-mail", "site": "site",
        }
        return [
            rotulo for campo, rotulo in rotulos.items()
            if str(getattr(self, campo)).startswith("[DADO PENDENTE]")
        ]


ESCRITORIO = Escritorio()

# Aviso que acompanha toda saída que exiba prazo. Texto único, para que a
# ressalva não se dilua em variações.
AVISO_ESTIMATIVA = (
    "Todas as datas deste documento são ESTIMATIVAS produzidas por automação. "
    "A conferência no sistema do tribunal é ato privativo do advogado."
)
