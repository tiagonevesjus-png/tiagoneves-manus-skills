---
name: tnadv-triagem-gmail
description: Triagem, classificação e reorganização da caixa de e-mail jurídica do escritório Tiago Neves. Aplica a taxonomia TNADV de rótulos, separa intimação de propaganda, identifica processos e providências, e faz varredura de recuperação no acervo de mensagens não lidas. Use quando o usuário pedir para organizar, classificar, triar ou limpar o Gmail, ou quando a Routine de triagem disparar.
---

# Triagem e reorganização do Gmail

A caixa do escritório acumulou milhares de mensagens não lidas e uma taxonomia
herdada de migração IMAP, com pastas do tipo `[Gmail]/Lixeira/PENDENTES` que já
não significam nada. Esta skill separa o que exige providência do que virou
histórico, sem apagar nada.

## Taxonomia TNADV

Rótulos oficiais, criados na implantação:

| Rótulo | Uso |
|---|---|
| `TNADV/Intimações` | Comunicações de tribunal: DJe, DJEN, PJe, portais, oficial de justiça |
| `TNADV/Prazos` | Mensagens de que decorre providência com data |
| `TNADV/Audiências` | Designação, remarcação, links de sessão telepresencial |
| `TNADV/Clientes` | Comunicação direta com cliente |
| `TNADV/Financeiro` | Honorários, RPV, precatório, alvará, cobrança, nota fiscal |
| `TNADV/Gestão Pública` | Órgãos públicos assessorados, processos administrativos, ofícios |
| `TNADV/Administrativo` | OAB, certidões, fornecedores, rotina do escritório |
| `TNADV/Arquivo` | Encerrado, apenas histórico |
| `TNADV/Triagem/Processado` | Já passou pela triagem automática |
| `TNADV/Triagem/Revisar` | Automação não teve confiança suficiente; exige olho humano |

Os rótulos antigos herdados do IMAP não são apagados. Eles permanecem como
histórico; a taxonomia nova convive com eles.

## Como classificar

Leia o teor, não só o assunto. A ordem de decisão é esta:

1. **É comunicação oficial de tribunal?** Remetente institucional, número CNJ
   válido no corpo, referência a ato processual. Vai para `TNADV/Intimações`.
   Se dela decorre providência com data, receba **também** `TNADV/Prazos` e
   acione a skill `tnadv-radar-intimacoes`.

2. **É audiência?** Designação, redesignação, link de sessão. `TNADV/Audiências`,
   e verifique se já existe evento correspondente na agenda.

3. **É cliente falando?** Endereço pessoal, assunto sobre caso próprio.
   `TNADV/Clientes`.

4. **Tem conteúdo financeiro?** `TNADV/Financeiro`.

5. **É órgão público assessorado?** `TNADV/Gestão Pública`.

6. **Sobrou?** `TNADV/Administrativo`, ou `TNADV/Arquivo` se claramente histórico.

Ao final, aplique `TNADV/Triagem/Processado`. Quando a classificação ficar
abaixo de confiança razoável, aplique `TNADV/Triagem/Revisar` **em vez de**
chutar uma categoria.

### Armadilhas conhecidas

- Newsletter jurídica e boletim de escritório usam as mesmas palavras de uma
  intimação. Verifique remetente e presença de número CNJ válido.
- Notificação de sistema ("houve movimentação no processo X") não é intimação:
  é aviso. O termo inicial vem do DJe ou do portal, nunca do e-mail.
- Uma thread pode mudar de natureza. Classifique pela mensagem mais recente.

## Varredura de recuperação

Para o passivo de mensagens não lidas, trabalhe em lotes e do mais recente para
o mais antigo, porque o valor decai com o tempo:

```
is:unread newer_than:30d
is:unread older_than:30d newer_than:90d
is:unread older_than:90d newer_than:1y
is:unread older_than:1y
```

Em cada lote: classifique, rotule, e produza um relatório do que foi encontrado.
Mensagens com mais de um ano e sem número CNJ vão para `TNADV/Arquivo`.

Processe no máximo 100 mensagens por execução e informe onde parou, para que a
execução seguinte continue do ponto certo.

## Regras invioláveis

1. **Nunca apague, mova para lixeira ou marque como spam.** Esta skill só rotula.
   Exclusão é decisão do advogado, tomada mensagem a mensagem.
2. **Nunca marque como lida** uma mensagem classificada como `TNADV/Intimações`
   ou `TNADV/Prazos`. O não lido é a última barreira contra perda de prazo.
3. **Nunca responda e-mail** a partir da triagem.
4. Ao encontrar número CNJ, valide com `core.cnj.validar` antes de usar.
5. Em caso de dúvida entre duas categorias, aplique as duas e mande para
   `TNADV/Triagem/Revisar`. Erro de classificação silencioso é pior que ruído.

## Relatório de execução

Ao final, informe: total examinado, distribuição por rótulo, quantos foram para
`Revisar` e por quê, números CNJ novos detectados, e o ponto de parada.
