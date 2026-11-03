/*
 * TNADV · ponte entre o sistema e as centrais do kit do notebook.
 *
 * Origem: repositório tiagoneves-manus-skills, pasta centrais/. O conector
 * (tools/conectar_centrais.py) copia este arquivo para a pasta do kit: altere
 * no repositório, não na cópia.
 *
 * Lê window.TNADV_DADOS (tnadv_dados.js, gerado pelo conector) e:
 *  - põe no topo de cada página a mesma barra de navegação;
 *  - na Central de Automação, oferece à calculadora os calendários forenses do
 *    sistema e abre o cálculo na data de hoje;
 *  - na Central Multi-IA, mostra agenda e prazos do acervo e confere o dígito
 *    verificador de todo número CNJ escrito na página;
 *  - no Painel, monta a página inteira.
 *
 * Nada aqui envia dado para fora do computador. A única memória local é a
 * escolha do calendário, guardada no próprio navegador.
 */
(function () {
  'use strict';

  var script = document.currentScript;
  var PAGINA = (script && script.getAttribute('data-pagina')) || 'desconhecida';
  var RAIZ = (script && script.getAttribute('data-raiz')) || '';
  var D = window.TNADV_DADOS || null;

  var NOMES = { painel: 'Painel', automacao: 'Central de Automação', multi_ia: 'Central Multi-IA' };
  // Na barra, nome curto: os três cabem numa linha de celular.
  var CURTOS = { painel: 'Painel', automacao: 'Automação', multi_ia: 'Multi-IA' };
  var ROTULOS = { vermelho: 'Ação imediata', amarelo: 'Esta semana', verde: 'Acompanhamento' };

  // ------------------------------------------------------------ utilidades

  function el(tag, attrs, filhos) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === 'texto') n.textContent = attrs[k];
      else if (k === 'classe') n.className = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (filhos || []).forEach(function (f) {
      if (f !== null && f !== undefined && f !== '') {
        n.appendChild(typeof f === 'string' ? document.createTextNode(f) : f);
      }
    });
    return n;
  }

  function dois(n) { return String(n).padStart(2, '0'); }

  function dataBr(iso) {
    var p = String(iso || '').slice(0, 10).split('-');
    return p.length === 3 ? p[2] + '/' + p[1] + '/' + p[0] : String(iso || '');
  }

  function dataHoraBr(iso) {
    var d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso || '');
    return dois(d.getDate()) + '/' + dois(d.getMonth() + 1) + '/' + d.getFullYear() +
      ' às ' + dois(d.getHours()) + 'h' + dois(d.getMinutes());
  }

  function hojeIso() {
    var d = new Date();
    return d.getFullYear() + '-' + dois(d.getMonth() + 1) + '-' + dois(d.getDate());
  }

  // Caminho relativo à pasta do kit, com "/", vira endereço relativo à página.
  function endereco(relativo) {
    return RAIZ + String(relativo).split('/').map(encodeURIComponent).join('/');
  }

  function guardar(chave, valor) {
    try { window.localStorage.setItem('tnadv.' + chave, valor); } catch (e) { /* sem memória local */ }
  }

  function lembrar(chave) {
    try { return window.localStorage.getItem('tnadv.' + chave); } catch (e) { return null; }
  }

  // ------------------------------------------------------------ número CNJ

  var RE_CNJ = /\b(\d{7})-(\d{2})\.(\d{4})\.(\d)\.(\d{2})\.(\d{4})\b/g;

  // Mesmo cálculo de core/cnj.py (módulo 97), feito em três etapas para não
  // passar da precisão inteira de um número JavaScript.
  function dvEsperado(n, ano, j, tr, origem) {
    var r1 = parseInt(n, 10) % 97;
    var r2 = parseInt(dois(r1) + ano + j + tr, 10) % 97;
    var r3 = parseInt(dois(r2) + origem + '00', 10) % 97;
    return dois(98 - r3);
  }

  function spanCnj(numero) {
    RE_CNJ.lastIndex = 0;
    var m = RE_CNJ.exec(numero);
    if (!m) return el('span', { texto: numero });
    var esperado = dvEsperado(m[1], m[3], m[4], m[5], m[6]);
    var ok = esperado === m[2];
    var span = el('span', {
      classe: 'tnadv-cnj' + (ok ? '' : ' tnadv-cnj-invalido'),
      title: ok ? 'Dígito verificador confere (módulo 97).'
        : 'Dígito verificador NÃO confere: informado ' + m[2] + ', o cálculo dá ' +
          esperado + '. Confira o número no sistema do tribunal.',
      texto: m[0]
    });
    if (ok) return span;
    var frag = document.createDocumentFragment();
    frag.appendChild(span);
    frag.appendChild(el('span', { classe: 'tnadv-cnj-alerta', texto: 'DV não confere: esperado ' + esperado }));
    return frag;
  }

  // Envolve os números CNJ do texto da página: não quebram mais no hífen, e o
  // que tiver dígito verificador errado ganha alerta ao lado.
  function marcarCnjs(raiz) {
    var aceitos = [];
    var walker = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT, {
      acceptNode: function (no) {
        var pai = no.parentNode;
        if (!pai || /^(SCRIPT|STYLE|TEXTAREA|INPUT|SELECT|OPTION|NOSCRIPT)$/.test(pai.nodeName)) {
          return NodeFilter.FILTER_REJECT;
        }
        if (pai.closest && pai.closest('.tnadv-cnj, .tnadv-barra, .tnadv-sistema, [contenteditable="true"]')) {
          return NodeFilter.FILTER_REJECT;
        }
        RE_CNJ.lastIndex = 0;
        return RE_CNJ.test(no.nodeValue) ? NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_SKIP;
      }
    });
    while (walker.nextNode()) aceitos.push(walker.currentNode);
    var invalidos = [];
    aceitos.forEach(function (no) {
      var texto = no.nodeValue;
      var frag = document.createDocumentFragment();
      var ultimo = 0;
      var m;
      RE_CNJ.lastIndex = 0;
      while ((m = RE_CNJ.exec(texto)) !== null) {
        frag.appendChild(document.createTextNode(texto.slice(ultimo, m.index)));
        var marcado = spanCnj(m[0]);
        var alvo = marcado.nodeType === 11 ? marcado.firstChild : marcado;
        if (alvo.classList.contains('tnadv-cnj-invalido')) invalidos.push(alvo);
        frag.appendChild(marcado);
        ultimo = m.index + m[0].length;
      }
      frag.appendChild(document.createTextNode(texto.slice(ultimo)));
      no.parentNode.replaceChild(frag, no);
    });
    return invalidos;
  }

  // ------------------------------------------------------------ barra comum

  function statusDados() {
    if (!D) {
      return el('span', {
        classe: 'tnadv-status tnadv-status-alerta',
        texto: 'Sem dados do sistema: rode CONECTAR_CENTRAIS_TNADV.bat'
      });
    }
    var horas = (Date.now() - new Date(D.gerado_em).getTime()) / 36e5;
    var velho = !isFinite(horas) || horas > 24;
    return el('span', {
      classe: 'tnadv-status' + (velho ? ' tnadv-status-alerta' : ''),
      title: 'Gerado por tools/conectar_centrais.py. Rode de novo depois de atualizar o acervo.',
      texto: 'Dados do sistema de ' + dataHoraBr(D.gerado_em) + (velho ? ' · desatualizados' : '')
    });
  }

  function montarBarra() {
    var paginas = (D && D.paginas) || {};
    var links = el('div', { classe: 'tnadv-links' });
    ['painel', 'automacao', 'multi_ia'].forEach(function (k) {
      if (!paginas[k]) return;
      var a = el('a', { href: endereco(paginas[k]), title: NOMES[k], texto: CURTOS[k] });
      if (k === PAGINA) a.setAttribute('aria-current', 'page');
      links.appendChild(a);
    });
    if (D && D.planilha) {
      links.appendChild(el('a', { href: endereco(D.planilha), title: 'Planilha de controle', texto: 'Planilha' }));
    }
    var barra = el('nav', { classe: 'tnadv-barra', 'aria-label': 'Sistema TNADV' }, [
      el('span', { classe: 'tnadv-marca', texto: 'TNADV' }), links, statusDados()
    ]);
    document.body.insertBefore(barra, document.body.firstChild);
    return barra;
  }

  function avisarCnjsInvalidos(barra, invalidos) {
    if (!invalidos.length) return;
    var plural = invalidos.length > 1;
    var botao = el('button', {
      type: 'button',
      classe: 'tnadv-status tnadv-status-erro',
      texto: invalidos.length + (plural ? ' números CNJ' : ' número CNJ') + ' desta página com dígito que não confere'
    });
    botao.addEventListener('click', function () {
      var alvo = invalidos[0];
      var painel = alvo.closest('.tab-panel');
      if (painel && !painel.classList.contains('active') && painel.id) {
        var aba = document.querySelector('[onclick*="' + painel.id + '"]');
        if (aba) aba.click();
      }
      alvo.scrollIntoView({ block: 'center' });
      alvo.classList.add('tnadv-piscar');
      setTimeout(function () { alvo.classList.remove('tnadv-piscar'); }, 2400);
    });
    barra.appendChild(botao);
  }

  // ------------------------------------------------------ agenda e prazos

  function painelSistema() {
    var A = D && D.acervo;
    var caixa = el('section', { classe: 'tnadv-sistema' });
    if (!D) {
      caixa.appendChild(el('p', {
        classe: 'tnadv-vazio',
        texto: 'Os dados do sistema não foram encontrados (tnadv_ponte/tnadv_dados.js). ' +
          'Rode CONECTAR_CENTRAIS_TNADV.bat na pasta do sistema.'
      }));
      return caixa;
    }
    if (!A || !A.disponivel) {
      caixa.appendChild(el('p', {
        classe: 'tnadv-vazio',
        texto: 'O acervo do sistema (data/acervo.json) está vazio neste computador. Quando ' +
          'houver processos cadastrados, audiências e prazos aparecem aqui a cada execução do conector.'
      }));
      return caixa;
    }

    var placar = el('div', { classe: 'tnadv-placar' });
    ['vermelho', 'amarelo', 'verde'].forEach(function (nivel) {
      placar.appendChild(el('div', { classe: 'tnadv-placar-caixa tnadv-' + nivel }, [
        el('strong', { texto: String(A.contagem[nivel] || 0) }),
        el('span', { texto: ROTULOS[nivel] })
      ]));
    });
    caixa.appendChild(placar);

    var prazos = el('div', { classe: 'tnadv-bloco' }, [el('h3', { texto: 'Prazos em aberto' })]);
    if (!A.prazos.length) {
      prazos.appendChild(el('p', { classe: 'tnadv-vazio', texto: 'Nenhum prazo em aberto na janela de ' + A.janela_dias + ' dias.' }));
    } else {
      var lp = el('ul', { classe: 'tnadv-lista' });
      A.prazos.forEach(function (p) {
        var faltam = p.dias_restantes < 0 ? 'vencido há ' + (-p.dias_restantes) + ' dia(s)'
          : p.dias_restantes === 0 ? 'vence hoje' : 'faltam ' + p.dias_restantes + ' dia(s)';
        lp.appendChild(el('li', { classe: 'tnadv-' + p.urgencia }, [
          el('span', { classe: 'tnadv-quando', texto: dataBr(p.vencimento) }),
          el('span', { classe: 'tnadv-o-que' }, [
            el('strong', { texto: p.providencia || 'Prazo' }), ' · ', spanCnj(p.cnj),
            p.cliente ? ' · ' + p.cliente : '',
            el('small', { texto: [faltam, p.regime, p.orgao].filter(Boolean).join(' · ') }),
            p.conferido ? null : el('em', { classe: 'tnadv-pendente', texto: 'estimativa não conferida' })
          ])
        ]));
      });
      prazos.appendChild(lp);
    }
    caixa.appendChild(prazos);

    var agenda = el('div', { classe: 'tnadv-bloco' }, [el('h3', { texto: 'Audiências designadas' })]);
    if (!A.agenda.length) {
      agenda.appendChild(el('p', { classe: 'tnadv-vazio', texto: 'Nenhuma audiência no acervo para os próximos ' + A.janela_dias + ' dias.' }));
    } else {
      var la = el('ul', { classe: 'tnadv-lista' });
      A.agenda.forEach(function (a) {
        la.appendChild(el('li', null, [
          el('span', { classe: 'tnadv-quando', texto: dataBr(a.data) + (a.hora ? ' ' + a.hora : '') }),
          el('span', { classe: 'tnadv-o-que' }, [
            el('strong', { texto: a.tipo ? 'Audiência ' + a.tipo : 'Audiência' }), ' · ', spanCnj(a.cnj),
            a.cliente ? ' · ' + a.cliente : '',
            el('small', { texto: [a.modalidade, a.orgao, a.local].filter(Boolean).join(' · ') }),
            a.confirmada ? null : el('em', { classe: 'tnadv-pendente', texto: 'não confirmada' })
          ])
        ]));
      });
      agenda.appendChild(la);
    }
    caixa.appendChild(agenda);

    caixa.appendChild(el('p', { classe: 'tnadv-aviso', texto: D.aviso_estimativa }));
    return caixa;
  }

  function resumoAcervo() {
    var A = D && D.acervo;
    if (!A || !A.disponivel) return 'acervo vazio';
    return A.prazos.length + ' prazo(s) em aberto · ' + A.agenda.length + ' audiência(s) · ' +
      A.nao_conferidos + ' não conferido(s)';
  }

  // ------------------------------------------------- Central de Automação

  function ligarCalendarios() {
    var ta = document.getElementById('inputFeriadosExtras');
    if (!ta || !D || !D.calendarios || !D.calendarios.length) return;
    var id = 'tnadvCalendario';
    var sel = el('select', { id: id });
    sel.appendChild(el('option', { value: '', texto: 'Lista digitada abaixo (não conferida pelo sistema)' }));
    D.calendarios.forEach(function (c) {
      sel.appendChild(el('option', {
        value: c.chave,
        texto: c.nome + (c.confirmado ? '' : ' · NÃO CONFIRMADO')
      }));
    });
    var avisos = el('div', { classe: 'tnadv-avisos' });
    var bloco = el('div', { classe: 'tnadv-calendario' }, [
      el('label', { 'for': id, texto: 'Calendário do juízo (feriados do sistema TNADV)' }), sel, avisos
    ]);
    var contem = ta.parentNode;
    contem.parentNode.insertBefore(bloco, contem);

    // Rótulo e legenda da página descrevem a lista fixa ("São Luís/MA já
    // pré-carregados"). Com calendário escolhido, passam a dizer de onde veio
    // a lista; com a lista digitada, voltam ao texto original.
    var rotulo = contem.querySelector('label[for="inputFeriadosExtras"]');
    var legenda = ta.nextElementSibling && ta.nextElementSibling.tagName === 'P' ? ta.nextElementSibling : null;
    var rotuloOriginal = rotulo ? rotulo.textContent : '';
    var legendaOriginal = legenda ? legenda.textContent : '';

    function aplicar(chave, recalcular) {
      avisos.textContent = '';
      var cal = D.calendarios.filter(function (c) { return c.chave === chave; })[0];
      if (!cal) {
        if (rotulo) rotulo.textContent = rotuloOriginal;
        if (legenda) legenda.textContent = legendaOriginal;
        avisos.appendChild(el('p', {
          classe: 'tnadv-nota-alerta',
          texto: 'A lista abaixo é fixa: vale para um só tribunal e um só ano. TJMA e TRT16, por ' +
            'exemplo, não param nos mesmos dias. Escolha o calendário do juízo do processo.'
        }));
        guardar('calendario', '');
        return;
      }
      ta.value = Object.keys(cal.nao_uteis).sort().join(', ');
      if (rotulo) rotulo.textContent = 'Dias úteis sem expediente (seg. a sex.) do calendário escolhido';
      if (legenda) {
        legenda.textContent = Object.keys(cal.nao_uteis).length + ' dias de ' + cal.anos.join(' e ') +
          ', vindos do sistema TNADV (' + cal.nome + '). Recesso e feriados nacionais incluídos. ' +
          'Acrescente à mão só suspensão que o calendário ainda não tenha.';
      }
      var reduzidos = Object.keys(cal.expediente_reduzido || {}).sort();
      if (reduzidos.length) {
        avisos.appendChild(el('p', {
          classe: 'tnadv-nota-alerta',
          texto: 'Dia de expediente reduzido neste calendário: ' + reduzidos.map(dataBr).join(', ') +
            '. Esta calculadora o conta como dia útil comum; o motor do sistema (core/prazos.py) ' +
            'trata o caso. Se o prazo começar ou terminar nele, confira pelo sistema.'
        }));
      }
      (cal.alertas || []).forEach(function (a) {
        avisos.appendChild(el('p', { classe: 'tnadv-nota-alerta', texto: a }));
      });
      var consulta = [];
      if (cal.fonte) {
        consulta.push(el('p', {
          classe: 'tnadv-nota',
          texto: 'Fonte: ' + cal.fonte + (cal.consultado_em ? ' (consultada em ' + dataBr(cal.consultado_em) + ')' : '')
        }));
      }
      if (cal.observacoes) consulta.push(el('p', { classe: 'tnadv-nota', texto: cal.observacoes }));
      if (consulta.length) {
        avisos.appendChild(el('details', { classe: 'tnadv-consulta' },
          [el('summary', { texto: 'Fonte e observações do calendário' })].concat(consulta)));
      }
      guardar('calendario', chave);
      if (recalcular && typeof window.calcularTempestividade === 'function') window.calcularTempestividade();
    }

    sel.addEventListener('change', function () { aplicar(sel.value, true); });
    var salvo = lembrar('calendario');
    var existe = D.calendarios.some(function (c) { return c.chave === salvo; });
    sel.value = existe ? salvo : '';
    aplicar(sel.value, false);
  }

  // O comentário da página diz "inicializa com a data de hoje", mas o código
  // fixava 23/10/2026. A ponte cumpre o que o comentário promete.
  function abrirNaDataDeHoje() {
    var campo = document.getElementById('inputDataDisp');
    if (!campo) return;
    campo.value = hojeIso();
    if (typeof window.calcularTempestividade === 'function') window.calcularTempestividade();
  }

  // ------------------------------------------------------- ajustes comuns

  // Select estreito corta a opção escolhida ("Publicação no DJEN (Publica no
  // 1º dia útil seguinte; inicia no pr..."). A linha de baixo mostra inteira.
  function mostrarOpcaoInteira() {
    Array.prototype.forEach.call(document.querySelectorAll('select'), function (s) {
      if (s.id === 'tnadvCalendario') return;
      var maior = Array.prototype.reduce.call(s.options, function (m, o) { return Math.max(m, o.text.length); }, 0);
      if (maior < 40) return;
      var nota = el('div', { classe: 'tnadv-opcao' });
      s.parentNode.insertBefore(nota, s.nextSibling);
      var atualizar = function () {
        var o = s.options[s.selectedIndex];
        nota.textContent = o ? o.text : '';
      };
      s.addEventListener('change', atualizar);
      atualizar();
    });
  }

  // Abas que não cabem na tela rolam de lado; a borda esmaecida avisa que há mais.
  function dicaDeRolagem(conteiner) {
    if (!conteiner) return;
    conteiner.classList.add('tnadv-rolavel');
    var avaliar = function () {
      var resta = conteiner.scrollWidth - conteiner.clientWidth - conteiner.scrollLeft;
      conteiner.classList.toggle('tnadv-tem-mais', resta > 4);
    };
    conteiner.addEventListener('scroll', avaliar);
    window.addEventListener('resize', avaliar);
    conteiner.addEventListener('click', function (e) {
      var botao = e.target.closest ? e.target.closest('button') : null;
      if (botao && botao.scrollIntoView) botao.scrollIntoView({ block: 'nearest', inline: 'nearest' });
      setTimeout(avaliar, 300);
    });
    avaliar();
  }

  // Tabela larga no celular vira lista de cartões: cada célula ganha o nome da
  // coluna (data-rotulo), que o estilo exibe acima do valor.
  function tabelasEmCartoes(seletor) {
    Array.prototype.forEach.call(document.querySelectorAll(seletor), function (tabela) {
      var titulos = Array.prototype.map.call(tabela.querySelectorAll('thead th'), function (th) {
        return th.textContent.trim();
      });
      if (!titulos.length) return;
      tabela.classList.add('tnadv-tabela-cartoes');
      Array.prototype.forEach.call(tabela.querySelectorAll('tbody tr'), function (tr) {
        Array.prototype.forEach.call(tr.children, function (td, i) {
          if (titulos[i]) td.setAttribute('data-rotulo', titulos[i]);
        });
      });
    });
  }

  // ------------------------------------------------------------ Painel

  function montarPainel() {
    var raiz = document.getElementById('tnadv-painel');
    if (!raiz) return;
    var instrucoes = document.getElementById('tnadv-sem-dados');
    if (D && instrucoes) instrucoes.hidden = true;
    if (!D) return;

    var titulo = document.getElementById('tnadv-escritorio');
    if (titulo && D.escritorio) titulo.textContent = D.escritorio.nome + ' · ' + D.escritorio.oab;

    var atalhos = el('section', { classe: 'tnadv-atalhos' });
    var descricoes = {
      automacao: 'Calculadora de tempestividade com os calendários do sistema, revisor de texto, auditor CNJ e montador de peças.',
      multi_ia: 'Cartões de audiência, pauta, prompts para Claude, ChatGPT e Gemini, e nota pós-audiência.'
    };
    ['automacao', 'multi_ia'].forEach(function (k) {
      if (!D.paginas[k]) return;
      atalhos.appendChild(el('a', { classe: 'tnadv-cartao', href: endereco(D.paginas[k]) }, [
        el('strong', { texto: NOMES[k] }), el('span', { texto: descricoes[k] })
      ]));
    });
    if (D.planilha) {
      atalhos.appendChild(el('a', { classe: 'tnadv-cartao', href: endereco(D.planilha) }, [
        el('strong', { texto: 'Planilha de controle' }),
        el('span', { texto: 'Acervo, prazos, audiências, movimentações e conferência, com filtro em cada aba.' })
      ]));
    }
    raiz.appendChild(atalhos);

    raiz.appendChild(el('h2', { texto: 'Agenda e prazos do sistema' }));
    raiz.appendChild(painelSistema());

    raiz.appendChild(el('h2', { texto: 'Calendários forenses do sistema' }));
    var tabela = el('table', { classe: 'tnadv-tabela' });
    tabela.appendChild(el('thead', null, [el('tr', null, [
      el('th', { texto: 'Calendário' }), el('th', { texto: 'Situação' }),
      el('th', { texto: 'Feriados locais cadastrados' }), el('th', { texto: 'Dias úteis parados (seg. a sex.)' })
    ])]));
    var corpo = el('tbody');
    D.calendarios.forEach(function (c) {
      corpo.appendChild(el('tr', null, [
        el('td', { texto: c.nome }),
        el('td', { classe: c.confirmado ? 'tnadv-ok' : 'tnadv-nao', texto: c.confirmado ? 'confirmado' : 'não confirmado' }),
        el('td', { texto: c.anos_cobertos.length ? c.anos_cobertos.join(', ') : 'nenhum' }),
        el('td', { texto: String(Object.keys(c.nao_uteis).length) + ' em ' + c.anos.join(' e ') })
      ]));
    });
    tabela.appendChild(corpo);
    raiz.appendChild(el('div', { classe: 'tnadv-rolagem' }, [tabela]));
    raiz.appendChild(el('p', {
      classe: 'tnadv-nota',
      texto: 'Calendário não confirmado ou ano sem feriado local cadastrado: a calculadora avisa, ' +
        'e a data continua sendo estimativa até a conferência no sistema do tribunal.'
    }));
  }

  // ------------------------------------------------------------ início

  function iniciar() {
    document.documentElement.setAttribute('data-tnadv-pagina', PAGINA);
    var barra = montarBarra();

    if (PAGINA === 'automacao') {
      ligarCalendarios();
      abrirNaDataDeHoje();
      mostrarOpcaoInteira();
      var aba = document.querySelector('.tab-btn');
      dicaDeRolagem(aba ? aba.parentNode : null);
    } else if (PAGINA === 'multi_ia') {
      var principal = document.querySelector('main') || document.body;
      var recolhivel = el('details', { classe: 'tnadv-recolhivel' }, [
        el('summary', null, [el('strong', { texto: 'Sistema TNADV' }), ' · ' + resumoAcervo()]),
        painelSistema()
      ]);
      recolhivel.open = !!(window.matchMedia && window.matchMedia('(min-width: 700px)').matches);
      principal.insertBefore(recolhivel, principal.firstChild);
      avisarCnjsInvalidos(barra, marcarCnjs(principal));
      mostrarOpcaoInteira();
      tabelasEmCartoes('.table-wrap table');
      dicaDeRolagem(document.querySelector('.tabs-bar'));
    } else if (PAGINA === 'painel') {
      montarPainel();
    }
  }

  // Exposto para teste e para depuração no console do navegador.
  window.TNADV_PONTE = { dvEsperado: dvEsperado, dataBr: dataBr, versao: 1 };

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', iniciar);
  else iniciar();
})();
