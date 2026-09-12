---
name: tnadv-organizacao-probatoria-lote
description: Organização probatória em lote de anexos de petições. Recebe uma pasta de documentos, renomeia com padrão forense, ordena, monta índice e matriz de correspondência entre documento e fundamento, e produz PDF unificado paginado pronto para protocolo eletrônico no PJe. Use quando houver pasta de anexos a organizar, preparação de protocolo, ou pedido de índice de documentos.
---

# Organização probatória em lote

Pega uma pasta bruta de anexos e devolve um conjunto probatório que o juiz
consegue conferir sem esforço. Documento que o julgador não encontra é documento
que não produz prova.

## Entrada

- a petição (ou minuta) que cita os documentos
- a pasta com os arquivos, em qualquer estado de desorganização

## Fluxo

### 1. Inventário

Liste todo arquivo da pasta com nome original, tipo, tamanho e número de páginas.
Sinalize desde já: arquivo corrompido, duplicata (compare por conteúdo, não por
nome), documento ilegível, imagem sem OCR.

### 2. Leitura e identificação

Para cada arquivo, identifique natureza, data, autoria e o que ele prova. Em
PDF digitalizado sem camada de texto, rode OCR pela skill `pdf` antes de
prosseguir: documento não pesquisável atrapalha a conferência.

### 3. Correspondência com a peça

Percorra a petição e localize cada menção a documento. Monte a matriz:

| Doc. | Arquivo original | Descrição | Fundamento que o invoca | Item da peça |
|---|---|---|---|---|
| 01 | IMG_2938.jpg | Contrato de prestação de serviços, 12/03/2024 | Existência do vínculo contratual | § 8 da síntese fática |

Duas checagens obrigatórias em sentido contrário:

- **Documento citado e ausente na pasta** → `[DOCUMENTO FALTANTE]`, reportado ao
  advogado antes de qualquer protocolo.
- **Documento na pasta e não citado na peça** → ou é irrelevante e sai, ou a peça
  esqueceu de invocá-lo. Pergunte, não decida sozinho.

### 4. Renomeação e ordenação

Padrão: `DOC-NN - Descrição sintética - AAAA-MM-DD.ext`

```
DOC-01 - Contrato de prestacao de servicos - 2024-03-12.pdf
DOC-02 - Notificacao extrajudicial - 2024-07-05.pdf
DOC-03 - Comprovante de pagamento - 2024-08-01.pdf
```

Numeração na ordem em que os documentos aparecem na peça, não na ordem
cronológica nem na ordem em que estavam na pasta. Sem acento nem caractere
especial no nome do arquivo, porque parte dos sistemas de protocolo rejeita.

### 5. Índice

Gere `DOC-00 - Indice de documentos.pdf`, com número, descrição, data, páginas e
o fundamento correspondente. É a primeira coisa que o julgador abre.

### 6. PDF unificado

Pela skill `pdf`, produza volume único com paginação contínua e marcadores
(*bookmarks*) por documento. Mantenha também os arquivos separados: alguns
sistemas exigem anexo individual por tipo.

### 7. Checklist de protocolo

```
[ ] Todos os documentos citados na peça estão presentes
[ ] Nenhum documento sem citação ficou no conjunto sem decisão
[ ] Numeração da matriz confere com a numeração dos arquivos
[ ] PDFs pesquisáveis (OCR aplicado onde necessário)
[ ] Tamanho de cada arquivo dentro do limite do sistema
[ ] Documento sigiloso separado, para juntada em segredo de justiça
[ ] Índice gerado e conferido
```

## Regras invioláveis

1. **Não altere o conteúdo de documento nenhum.** Renomear, ordenar, aplicar OCR
   e unificar é o limite. Recortar, editar ou corrigir documento é adulteração.
2. **Não descarte arquivo.** O que sair do conjunto vai para subpasta
   `nao-utilizados/`, com a razão registrada.
3. **Preserve os originais** em `originais/`, intocados.
4. Documento sigiloso ou com dado pessoal sensível recebe tratamento apartado, e
   isso é sinalizado ao advogado (LGPD, art. 11).
5. O protocolo é ato do advogado.
