# Sigilo profissional e proteção de dados

Automação jurídica movimenta dado de cliente. Este documento fixa o que fica
onde, e por quê.

## Dois deveres sobrepostos

**Sigilo profissional.** O Estatuto da Advocacia (Lei 8.906/1994, art. 34, VII)
trata como infração disciplinar violar sigilo profissional sem justa causa. O
dever é do advogado, e não se transfere ao sistema que ele usa.

**LGPD** (Lei 13.709/2018). O escritório é controlador dos dados que trata. Dado
de processo judicial frequentemente inclui dado pessoal sensível: saúde, filiação
sindical, biometria, convicção religiosa (art. 5º, II), com hipóteses de
tratamento mais restritas (art. 11).

Os dois deveres convergem numa regra prática simples: **o mínimo necessário, no
lugar mais controlado, pelo menor tempo.**

## Classificação adotada

| Nível | Conteúdo | Onde pode ficar |
|---|---|---|
| **Verde** | Número CNJ, órgão, classe, datas de movimento, prazo | `data/acervo.json`, planilha de controle, agenda |
| **Amarelo** | Nome de cliente e parte contrária, objeto do caso | `data/acervo.json` e planilha, sob controle de acesso |
| **Vermelho** | Documentos, provas, laudos, dado sensível, valores, dado bancário | Repositório de arquivos do escritório, **nunca** neste repositório |

O `.gitignore` bloqueia `data/`, `saida/`, `.xlsx`, `.docx` e `.pdf`. A barreira
é técnica, não apenas de conduta.

## O que cada automação pode fazer

| Automação | Lê | Escreve | Não pode |
|---|---|---|---|
| Dashboard diário | Gmail, Agenda, acervo | rascunho no Gmail | enviar e-mail, apagar, arquivar |
| Triagem do Gmail | Gmail | rótulos | apagar, mover para lixeira, responder, marcar intimação como lida |
| Radar de intimações | Gmail | evento na Agenda, acervo | protocolar, marcar prazo como conferido |
| Planilha de controle | acervo | xlsx local | subir planilha a serviço externo |
| Skills da camada 2 | material fornecido | documento local | publicar, enviar, protocolar |

Nenhuma automação envia comunicação a terceiro sem ato do advogado.

## Antes de conectar serviço externo

Toda vez que um dado sair do ambiente do escritório, verifique:

1. **Necessidade.** O serviço precisa mesmo desse campo?
2. **Base legal** do tratamento (LGPD, art. 7º; art. 11 para dado sensível).
3. **Localização.** O projeto Supabase do escritório está na região `sa-east-1`,
   com dado em território nacional. Serviço fora do país exige análise adicional
   (arts. 33 a 36).
4. **Retenção.** Por quanto tempo o serviço guarda, e como se apaga.
5. **Registro.** Anote a decisão. Se houver incidente, o registro é o que
   demonstra diligência.

## Eliminação

Processo encerrado e prazo prescricional decorrido: mova para arquivo frio e
remova do acervo em operação. Acervo inflado é risco sem contrapartida.

## Incidente

Suspeita de acesso indevido ou vazamento: interrompa a automação envolvida,
levante o alcance (quais titulares, quais dados), registre data e hora, e avalie
a comunicação à ANPD e aos titulares (LGPD, art. 48). O prazo do art. 48 corre
da ciência, então o registro do momento em que se soube importa.
