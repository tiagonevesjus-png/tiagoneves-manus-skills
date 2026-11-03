# Centrais do kit ligadas ao sistema

Situação verificada em 03/11/2026. O kit do notebook tem duas páginas soltas,
abertas direto do disco:

- `central_automacao_tnadv.html` (calculadora de tempestividade, revisor de
  texto, auditor CNJ, montador de peças);
- `Pacote_Multi_IA_Claude_ChatGPT_TNADV/central_multi_ia_mobile_tnadv.html`
  (cartões de audiência, pauta, prompts, nota pós-audiência).

Até aqui elas não conversavam com o sistema nem entre si. A ponte resolve isso
sem copiar as páginas, nem dado de cliente, para este repositório.

## Viabilidade dos dois locais

| Local | Serve? | Por quê |
|---|---|---|
| `C:\Users\...\AppData\Local\Temp\<código>_Kit_Completo_Automacao_Notebook_TNADV.zip.ec6\central_automacao_tnadv.html` | **Não** | É a pasta temporária que o Windows cria ao abrir um arquivo de dentro do `.zip` sem extrair. Ela some quando o Windows limpa a pasta temporária, e o que for ligado ali some junto. O conector recusa esse tipo de pasta. |
| `C:\Users\...\OneDrive\Desktop\Kit_Completo_Automacao_Notebook_TNADV_v2_Multi_IA\...` | **Sim** | Pasta fixa. A `central_automacao_tnadv.html` da raiz dela é idêntica, byte a byte, à que vem dentro do `Kit_Completo_Automacao_Notebook_TNADV.zip` (SHA-256 conferido em 03/11/2026 nas cópias do zip e da pasta guardadas no Google Drive). |

Se o instalador do kit (`INSTALAR_TUDO_NO_NOTEBOOK_TNADV.bat`) já rodou, existe
uma terceira cópia em `Documentos\TNADV_Automacao`, que é para onde aponta o
atalho "2. Central de Automacao Forense TNADV" da Área de Trabalho. O conector
liga essa também.

## Como ligar

No notebook, com o repositório baixado e Python instalado:

1. Dê dois cliques em `CONECTAR_CENTRAIS_TNADV.bat`, na raiz do repositório.
2. Ele procura a pasta do kit na Área de Trabalho (com ou sem OneDrive) e em
   `Documentos\TNADV_Automacao`, liga o que encontrar e abre o
   `PAINEL_TNADV.html`.

Pasta em outro lugar:

```bat
CONECTAR_CENTRAIS_TNADV.bat --kit "D:\caminho\da\pasta\do\kit"
```

Para ver o que seria feito sem gravar nada, acrescente `--simular`.

## O que o conector grava, e onde

Tudo dentro da pasta do kit, nada no repositório:

| Arquivo | Conteúdo |
|---|---|
| `tnadv_ponte/tnadv_dados.js` | calendários forenses do sistema e, havendo acervo, agenda e prazos |
| `tnadv_ponte/tnadv_ponte.js` e `.css` | o script e o estilo da ponte (cópia de `centrais/`) |
| `PAINEL_TNADV.html` | ponto de entrada comum |
| bloco de quatro linhas antes de `</body>` em cada central | liga a página à ponte, entre os marcadores `TNADV-PONTE:INICIO` e `TNADV-PONTE:FIM` |
| `*.antes-da-ponte.html` | cópia da central como estava, guardada antes da primeira alteração |

Rodar de novo só atualiza os dados. Nada é apagado.

## O que muda em cada página

**Todas.** Barra no topo com Painel, Automação, Multi-IA e Planilha, e a data em
que os dados do sistema foram gerados. Passadas 24 horas, a barra avisa que
estão desatualizados.

**Central de Automação.**

- A calculadora ganha a escolha do calendário do juízo. Escolhido, a lista de
  feriados passa a vir do sistema (`core/calendarios`), com os avisos do próprio
  calendário, inclusive o de ano sem feriado local cadastrado. A escolha fica
  guardada no navegador.
- O cálculo abre na data de hoje. A página prometia isso no comentário, mas
  fixava 23/10/2026.
- A opção escolhida nos campos de seleção aparece inteira embaixo deles.
- Correções de layout: cabeçalho deixa de grudar no topo no celular, abas que
  não cabem esmaecem na borda, e a tabela do auditor CNJ volta a alinhar (havia
  `display:flex` numa célula de tabela) e vira cartões no celular.

**Central Multi-IA.**

- Bloco "Sistema TNADV" no topo, com placar, prazos em aberto e audiências do
  acervo. Aberto no notebook, recolhido no celular.
- Todo número CNJ escrito na página tem o dígito verificador conferido. O que não
  confere ganha alerta ao lado, e a barra do topo leva até ele.
- Correções de layout: as cinco abas numa linha só (a quinta caía sozinha numa
  segunda linha), cabeçalho que não gruda no celular, indicadores em duas
  colunas, número do processo que não parte no meio e pauta em cartões no
  celular.

## Por que a calculadora precisava do calendário do sistema

A lista fixa da central serve a um tribunal e a um ano. Comparando a lógica da
página com o motor do sistema (`core/prazos.py`), em cada dia útil de
disponibilização de 21/01 a 30/11/2026, contagem a partir do DJEN:

| Cenário | Datas comparadas | Central mais tarde | Central mais cedo | Iguais |
|---|---|---|---|---|
| TRT16 São Luís, 8 dias (CLT) | 224 | 4 | 49 | 171 |
| TJMA São Luís, 15 dias (CPC) | 224 | 0 | 52 | 172 |

Exemplo: disponibilização em 27/07/2026, 8 dias, TRT16 São Luís. A lista fixa dá
10/08/2026; com o calendário do TRT16 do sistema, 07/08/2026. A diferença vem
das transferências de feriado do TRT16 em 2026 (27/07, 10/08, 30/10), que a lista
fixa trata nas datas do TJMA (28/07, 11/08, 28/10). O motor do sistema e o
calendário do TRT16 são a referência aqui pelo que já está documentado em
`docs/IMPLANTACAO.md`; continua valendo a conferência no sistema do tribunal.

## Desligar

```bat
CONECTAR_CENTRAIS_TNADV.bat --desconectar
```

Tira o bloco das centrais e as devolve exatamente como eram. A pasta
`tnadv_ponte` e o painel ficam; apague à mão se quiser.

## Sigilo

Por padrão, `tnadv_dados.js` leva só número CNJ, órgão, datas, tipo de ato e
providência. Nome de cliente, local e observações da audiência (onde costuma
estar link com senha) só entram com `--completo`. A planilha, que traz nome de
cliente, só é gerada e ligada com `--planilha`.

Atenção: a pasta do kit fica na Área de Trabalho, que o OneDrive sincroniza e o
Google Drive também copia. O que for gravado ali sai do notebook. As próprias
centrais já trazem dado de cliente; a ponte não acrescenta nome nenhum sem
`--completo`.

## Limites conhecidos

- A calculadora da central conta dia de expediente reduzido como dia útil
  comum. O motor do sistema trata esse caso; a central avisa quando o
  calendário escolhido tem dia assim.
- As correções de layout se prendem às classes atuais das páginas. Se uma
  central for refeita com outra marcação, a barra, os dados e a conferência de
  CNJ continuam funcionando, mas parte das correções de layout pode deixar de se
  aplicar.
- No celular, a ponte só funciona se o navegador do aparelho enxergar a pasta do
  kit inteira. Aberta isolada (anexo, visualizador do Drive), a central funciona
  como antes, sem a ponte.
