# data/

Diretório do acervo processual em execução. **Não é versionado** (ver `.gitignore`).

## Onde mora

No notebook do advogado, dentro da cópia local do sistema (sugestão:
`%USERPROFILE%\TNADV\sistema\data`), fora de pasta sincronizada com nuvem.
Decisão de 03/11/2026. Em sessão na nuvem, `Acervo.salvar()` recusa gravar
aqui, porque o contêiner é apagado ao fim e o registro sumiria sem aviso.

## Conteúdo esperado

- `acervo.json` — processos, movimentos e prazos (ver `core/acervo.py`)
- `acervo.anterior.json` — versão anterior, guardada a cada gravação
- `biblioteca.json` — índice de teses e modelos (ver a skill `tnadv-biblioteca-teses`)

A versão anterior protege contra gravação interrompida, não contra perda do
notebook. Cópia de segurança fora do notebook é decisão do advogado.

Mantenha aqui apenas o mínimo necessário à gestão do prazo. Documentos de
cliente, provas e peças ficam no repositório de arquivos do escritório, sob
controle de acesso, nunca neste diretório.
