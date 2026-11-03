/* Tela de Rescisões do painel: lista, detalhe, formulário, PDF e e-mail.
 *
 * Fica num arquivo próprio para não mexer no dashboard.js. Usa as rotas /rescisoes da API.
 * As funções "puras" (sem tela: cálculo, validação e montagem do JSON) ficam no começo do arquivo.
 */
(function () {
  "use strict";

  const STATUS_TEXTO = {
    PENDENTE: "Pendente",
    EM_CONFERENCIA: "Em conferência",
    GERADO: "Gerado",
    ENVIADO: "Enviado",
    ERRO_GERACAO: "Erro ao gerar",
    ERRO_ENVIO: "Erro no envio",
  };
  const TIPO_TEXTO = {
    PROVENTO: "Proventos",
    DESCONTO: "Descontos",
    INFORMATIVO: "Informativos (aparecem no documento, não entram no líquido)",
  };
  const TIPO_DOC_TEXTO = { RESCISAO: "Rescisão" }; // outros tipos de documento aparecem como vêm da API
  const CODIGOS_SUGERIDOS = [30, 31, 35, 36, 42]; // verbas que o botão "Sugerir valores" preenche
  const PODE_GERAR = ["EM_CONFERENCIA", "ERRO_GERACAO"];
  const PODE_BAIXAR_E_ENVIAR = ["GERADO", "ENVIADO", "ERRO_ENVIO"];

  // ================== funções puras (sem tela) ==================

  function esc(valor) {
    return String(valor === null || valor === undefined ? "" : valor).replace(/[&<>"']/g, (c) => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
    }[c]));
  }

  // "1900.50" -> 190050 (centavos). Vazio -> null. Inválido ou negativo -> NaN.
  function centavos(texto) {
    const t = String(texto === null || texto === undefined ? "" : texto).trim().replace(",", ".");
    if (t === "") return null;
    const n = Number(t);
    if (!Number.isFinite(n) || n < 0) return NaN;
    return Math.round(n * 100);
  }

  function centavosParaTexto(c) {
    return (c / 100).toFixed(2);
  }

  function moeda(c) {
    return (c / 100).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
  }

  function moedaTexto(valor) {
    const c = centavos(valor);
    return c === null || Number.isNaN(c) ? "—" : moeda(c);
  }

  function dataBR(iso) {
    if (!iso) return "—";
    const [a, m, d] = String(iso).slice(0, 10).split("-");
    return d && m && a ? `${d}/${m}/${a}` : String(iso);
  }

  // linhas: [{tipo, centavos}] (ignora vazio e inválido)
  function calcularTotais(linhas) {
    let proventos = 0;
    let descontos = 0;
    linhas.forEach((l) => {
      if (l.centavos === null || Number.isNaN(l.centavos)) return;
      if (l.tipo === "PROVENTO") proventos += l.centavos;
      if (l.tipo === "DESCONTO") descontos += l.centavos;
    });
    return { proventos, descontos, liquido: proventos - descontos };
  }

  // mesmo formato que o servidor exige: texto@dominio.xx (sem espaços, com ponto no domínio)
  function emailValido(texto) {
    return /^[A-Za-z0-9._%+\-]+@[A-Za-z0-9\-]+(?:\.[A-Za-z0-9\-]+)*\.[A-Za-z]{2,}$/.test(String(texto === null || texto === undefined ? "" : texto).trim());
  }

  // {busca, tipo, status} -> "?busca=...&tipo=...&status=..." (só o que foi preenchido)
  function montarConsulta(filtros) {
    const partes = [];
    [["busca", filtros.busca], ["tipo", filtros.tipo], ["status", filtros.status]].forEach(([chave, valor]) => {
      const v = String(valor === null || valor === undefined ? "" : valor).trim();
      if (v) partes.push(`${chave}=${encodeURIComponent(v)}`);
    });
    return partes.length ? `?${partes.join("&")}` : "";
  }

  // "rescisao-3" (referência gravada no histórico) -> 3. Qualquer outra coisa -> null.
  function idRescisaoDaReferencia(referencia) {
    const m = /^rescisao-(\d+)$/.exec(String(referencia === null || referencia === undefined ? "" : referencia));
    return m ? Number(m[1]) : null;
  }

  function traduzirErro(detalhe) {
    if (!detalhe) return "";
    if (typeof detalhe === "string") return detalhe;
    if (Array.isArray(detalhe)) return detalhe.map((d) => d.msg || JSON.stringify(d)).join("; ");
    return JSON.stringify(detalhe);
  }

  // Valida o que foi digitado e monta o JSON da API. Devolve {erro} ou {payload}.
  function montarPayload(campos, linhas) {
    if (!campos.colaboradorId) return { erro: "Selecione o colaborador." };
    if (!campos.dataDesligamento) return { erro: "Informe a data de desligamento." };
    if (!campos.causa) return { erro: "Selecione a causa do afastamento." };

    const itens = [];
    for (const linha of linhas) {
      const c = centavos(linha.valor);
      if (c === null) continue; // linha sem valor: não entra
      if (Number.isNaN(c)) return { erro: `Valor inválido na verba ${linha.codigo}.` };
      const referencia = String(linha.referencia || "").trim();
      itens.push({ codigo: linha.codigo, valor: centavosParaTexto(c), referencia: referencia || null });
    }
    if (!itens.length) return { erro: "Preencha o valor de pelo menos uma verba." };

    const remuneracao = centavos(campos.remuneracao);
    if (Number.isNaN(remuneracao)) return { erro: "Remuneração inválida." };

    return {
      payload: {
        colaborador_id: Number(campos.colaboradorId),
        data_desligamento: campos.dataDesligamento,
        data_aviso_previo: campos.dataAvisoPrevio || null,
        causa_afastamento: campos.causa,
        codigo_afastamento: String(campos.codigoAfastamento || "").trim() || null,
        categoria_trabalhador: "01 - Empregado",
        remuneracao: remuneracao === null ? null : centavosParaTexto(remuneracao),
        observacoes: String(campos.observacoes || "").trim() || null,
        itens,
      },
    };
  }

  // ================== tela ==================

  const $ = (id) => document.getElementById(id);
  const estado = { colaboradores: [], empresas: [], motivos: [], rubricas: [], rescisoes: [], editandoId: null, atual: null, origem: "lista", emailSimulado: false };

  async function api(url, opcoes) {
    const resposta = await fetch(url, opcoes);
    if (!resposta.ok) {
      let texto = `Erro ${resposta.status}`;
      try {
        const corpo = await resposta.json();
        texto = traduzirErro(corpo.detail) || texto;
      } catch (_) { /* sem corpo JSON */ }
      throw new Error(texto);
    }
    return resposta.status === 204 ? null : resposta.json();
  }

  function mensagem(texto, tipo) {
    const el = $("resc-mensagem");
    if (!el) return;
    if (!texto) {
      el.className = "resc-msg resc-oculto";
      el.textContent = "";
      return;
    }
    el.textContent = texto;
    el.className = `resc-msg ${tipo || "ok"}`;
  }

  function mostrar(qual) {
    $("resc-lista-card").classList.toggle("resc-oculto", qual !== "lista");
    $("resc-detalhe-card").classList.toggle("resc-oculto", qual !== "detalhe");
    $("resc-form-card").classList.toggle("resc-oculto", qual !== "form");
    $("resc-barra").classList.toggle("resc-oculto", qual !== "lista");
  }

  async function carregarBase() {
    const [colaboradores, empresas, motivos, rubricas] = await Promise.all([
      api("/colaboradores/"), api("/empresas"), api("/rescisoes/motivos"), api("/rescisoes/verbas-sugeridas"),
    ]);
    Object.assign(estado, { colaboradores, empresas, motivos, rubricas });
  }

  const nomeColaborador = (id) => (estado.colaboradores.find((c) => c.id === id) || {}).nome || `Colaborador #${id}`;
  const nomeEmpresa = (id) => {
    const e = estado.empresas.find((x) => x.id === id);
    return e ? e.nome_fantasia || e.razao_social : `Empresa #${id}`;
  };
  const situacaoColaborador = (id) => {
    const c = estado.colaboradores.find((x) => x.id === id);
    return c && c.situacao === "DESLIGADO" ? "Desligado" : "Ativo";
  };
  const badge = (status) => `<span class="resc-badge ${esc(status)}">${esc(STATUS_TEXTO[status] || status)}</span>`;

  // ---------- lista ----------
  function desenharLista() {
    const alvo = $("resc-lista");
    const incluirEnviadas = $("resc-mostrar-enviadas").checked;
    const enviadas = estado.rescisoes.filter((r) => r.status === "ENVIADO").length;
    const visiveis = estado.rescisoes.filter((r) => incluirEnviadas || r.status !== "ENVIADO");
    const aviso = enviadas && !incluirEnviadas
      ? `<p class="resc-dica">Rescisões já enviadas (${enviadas}) ficam no Histórico. Para vê-las aqui, marque “Mostrar também as já enviadas”.</p>`
      : "";
    if (!visiveis.length) {
      alvo.innerHTML = `<p>Nenhuma rescisão em andamento. Use o botão “Nova rescisão”.</p>${aviso}`;
      return;
    }
    const linhas = visiveis.slice().reverse().map((r) => `
      <tr class="resc-linha" data-id="${r.id}" tabindex="0">
        <td>#${r.id}</td>
        <td>${esc(nomeColaborador(r.colaborador_id))}</td>
        <td>${esc(dataBR(r.data_desligamento))}</td>
        <td>${esc(r.causa_afastamento)}</td>
        <td class="resc-valor">${esc(moedaTexto(r.total_liquido))}</td>
        <td>${badge(r.status)}</td>
      </tr>`).join("");
    alvo.innerHTML = `
      <table class="resc-tabela">
        <thead><tr><th>Nº</th><th>Colaborador</th><th>Desligamento</th><th>Causa</th><th class="resc-valor">Líquido</th><th>Status</th></tr></thead>
        <tbody>${linhas}</tbody>
      </table>
      <p class="resc-dica">Clique em uma rescisão para abrir.</p>${aviso}`;
  }

  async function carregarLista() {
    const alvo = $("resc-lista");
    if (!alvo) return;
    estado.origem = "lista";
    mensagem("");
    mostrar("lista");
    alvo.innerHTML = "<p>Carregando...</p>";
    try {
      await carregarBase();
      estado.rescisoes = await api("/rescisoes");
      desenharLista();
    } catch (erro) {
      alvo.innerHTML = `<p>Não foi possível carregar: ${esc(erro.message)}</p>`;
    }
  }

  // ---------- histórico: abre a mesma tela de detalhe ----------
  function filtrosDoHistorico() {
    return { busca: $("resc-h-busca").value, tipo: $("resc-h-tipo").value, status: $("resc-h-status").value };
  }

  async function carregarHistoricoDocumentos() {
    const alvo = $("resc-historico");
    if (!alvo) return;
    const filtros = filtrosDoHistorico();
    const comFiltro = montarConsulta(filtros) !== "";
    const numero = (estado.consultaHistorico = (estado.consultaHistorico || 0) + 1); // ignora respostas atrasadas
    alvo.innerHTML = "<p>Carregando...</p>";
    try {
      const registros = await api("/historico" + montarConsulta(filtros));
      if (numero !== estado.consultaHistorico) return;
      $("resc-h-contagem").textContent = registros.length === 1 ? "1 documento" : `${registros.length} documentos`;
      if (!registros.length) {
        alvo.innerHTML = comFiltro
          ? "<p>Nenhum documento encontrado com esses filtros. Use “Limpar filtros” para ver tudo.</p>"
          : "<p>Nenhum registro encontrado.</p>";
        return;
      }
      const linhas = registros.map((h) => {
        const id = idRescisaoDaReferencia(h.referencia);
        const abrivel = h.tipo === "RESCISAO" && id !== null;
        return `
          <tr${abrivel ? ` class="resc-linha" data-rescisao="${id}" tabindex="0"` : ""}>
            <td>${esc(TIPO_DOC_TEXTO[h.tipo] || h.tipo)}</td>
            <td>${esc(h.colaborador_nome)}</td>
            <td>${esc(h.empresa)}</td>
            <td>${badge(h.status)}</td>
            <td>${esc(dataBR(h.data_geracao))}</td>
            <td>${esc(dataBR(h.data_envio))}</td>
            <td class="resc-abrir">${abrivel ? "Abrir ›" : ""}</td>
          </tr>`;
      }).join("");
      alvo.innerHTML = `
        <table class="resc-tabela">
          <thead><tr><th>Tipo</th><th>Colaborador</th><th>Empresa</th><th>Status</th><th>Gerado em</th><th>Enviado em</th><th></th></tr></thead>
          <tbody>${linhas}</tbody>
        </table>
        <p class="resc-dica">Clique em uma rescisão para abrir: dá para corrigir, gerar o PDF, baixar e reenviar.</p>`;
    } catch (erro) {
      if (numero !== estado.consultaHistorico) return;
      alvo.innerHTML = `<p>Não foi possível carregar: ${esc(erro.message)}</p>`;
    }
  }

  // troca para a página de Rescisões e abre a rescisão pedida
  function irParaRescisao(id, origem) {
    const menu = document.querySelector('.menu-item[data-page="rescisao"]');
    if (menu) menu.click(); // o dashboard.js troca de página
    estado.origem = origem; // depois do clique, que volta a origem para "lista"
    abrirDetalhe(id);
  }

  // ---------- detalhe ----------
  function htmlDetalhe(r, envios) {
    const podeBaixar = PODE_BAIXAR_E_ENVIAR.includes(r.status);
    const itens = r.itens.map((i) => `
      <tr><td>${i.codigo}</td><td>${esc(i.descricao)}</td><td>${esc(TIPO_TEXTO[i.tipo] ? i.tipo.charAt(0) + i.tipo.slice(1).toLowerCase() : i.tipo)}</td>
          <td>${esc(i.referencia || "")}</td><td class="resc-valor">${esc(moedaTexto(i.valor))}</td></tr>`).join("");
    const lista = envios.length
      ? `<ul class="resc-envios">${envios.slice().reverse().map((e) => `
          <li>${esc(new Date(e.data).toLocaleString("pt-BR"))} — ${esc(e.destinatario)} —
              ${e.sucesso ? "enviado" : "falhou: " + esc(e.erro || "")}</li>`).join("")}</ul>`
      : "<p>Nenhum envio por e-mail ainda.</p>";
    return `
      <h2>Rescisão #${r.id} — ${esc(nomeColaborador(r.colaborador_id))} ${badge(r.status)}</h2>
      <div class="resc-acoes">
        <button type="button" class="resc-btn" data-acao="voltar">${estado.origem === "historico" ? "← Voltar para o Histórico" : "← Voltar para a lista"}</button>
        ${PODE_GERAR.includes(r.status) ? '<button type="button" class="resc-btn principal" data-acao="gerar">Gerar PDF</button>' : ""}
        ${podeBaixar ? `<a class="resc-btn principal" href="/rescisoes/${r.id}/pdf" target="_blank" rel="noopener">Baixar PDF</a>` : ""}
        <button type="button" class="resc-btn" data-acao="corrigir">Corrigir dados</button>
      </div>
      ${podeBaixar && estado.emailSimulado ? `
      <p class="resc-aviso"><strong>Modo de teste ativo:</strong> o e-mail <strong>não é enviado de verdade</strong>; ele é só gravado como arquivo em storage/documents/temporary/emails_simulados. Para enviar de verdade, coloque EMAIL_SIMULADO=false no arquivo .env.</p>` : ""}
      ${podeBaixar ? `
      <div class="resc-acoes resc-envio">
        <input type="email" id="resc-destinatario" placeholder="E-mail de destino (vazio = e-mail do colaborador)">
        <button type="button" class="resc-btn principal" data-acao="enviar">Enviar por e-mail</button>
      </div>` : '<p class="resc-dica">Gere o PDF para poder baixar e enviar por e-mail.</p>'}
      <dl class="resc-resumo">
        <div><dt>Empresa</dt><dd>${esc(nomeEmpresa(r.empresa_id))}</dd></div>
        <div><dt>Data de desligamento</dt><dd>${esc(dataBR(r.data_desligamento))}</dd></div>
        <div><dt>Aviso prévio</dt><dd>${esc(dataBR(r.data_aviso_previo))}</dd></div>
        <div><dt>Causa do afastamento</dt><dd>${esc(r.causa_afastamento)}</dd></div>
        <div><dt>Remuneração (campo 21)</dt><dd>${esc(moedaTexto(r.remuneracao))}</dd></div>
        <div><dt>Observações</dt><dd>${esc(r.observacoes || "—")}</dd></div>
        <div><dt>Situação do colaborador</dt><dd>${esc(situacaoColaborador(r.colaborador_id))}</dd></div>
      </dl>
      ${situacaoColaborador(r.colaborador_id) === "Desligado"
        ? '<p class="resc-dica">Colaborador desligado: não é possível criar uma nova rescisão para ele. Esta rescisão ainda pode ser corrigida, gerada de novo e reenviada.</p>'
        : ""}
      <table class="resc-tabela">
        <thead><tr><th>Cód.</th><th>Verba</th><th>Tipo</th><th>Referência</th><th class="resc-valor">Valor</th></tr></thead>
        <tbody>${itens}</tbody>
      </table>
      <div class="resc-totais">
        <div class="resc-total"><span>Total bruto (46)</span><strong>${esc(moedaTexto(r.total_proventos))}</strong></div>
        <div class="resc-total"><span>Total das deduções (54)</span><strong>${esc(moedaTexto(r.total_descontos))}</strong></div>
        <div class="resc-total liquido"><span>Líquido a receber (55)</span><strong>${esc(moedaTexto(r.total_liquido))}</strong></div>
      </div>
      <h3 class="resc-grupo">Envios por e-mail</h3>
      ${lista}`;
  }

  async function abrirDetalhe(id, manterMensagem) {
    if (!manterMensagem) mensagem("");
    mostrar("detalhe");
    const alvo = $("resc-detalhe");
    alvo.innerHTML = "<p>Carregando...</p>";
    try {
      if (!estado.colaboradores.length) await carregarBase();
      const [rescisao, envios, modo, colaboradores] = await Promise.all([
        api(`/rescisoes/${id}`), api(`/rescisoes/${id}/envios`), api("/rescisoes/email-modo"), api("/colaboradores/"),
      ]);
      estado.colaboradores = colaboradores;
      estado.atual = rescisao;
      estado.emailSimulado = Boolean(modo && modo.simulado);
      alvo.innerHTML = htmlDetalhe(rescisao, envios);
    } catch (erro) {
      alvo.innerHTML = `<p>Não foi possível abrir: ${esc(erro.message)}</p>`;
    }
  }

  async function executar(botao, fazer, textoOk, id) {
    botao.disabled = true;
    let texto = textoOk;
    let tipo = "ok";
    try {
      await fazer();
    } catch (erro) {
      texto = erro.message;
      tipo = "erro";
    }
    await abrirDetalhe(id, true); // atualiza a tela com o status novo (inclusive depois de uma falha)...
    mensagem(texto, tipo); // ...e só então mostra o resultado
  }

  // ---------- formulário ----------
  function htmlVerbas(rubricas) {
    return ["PROVENTO", "DESCONTO", "INFORMATIVO"].map((tipo) => {
      const linhas = rubricas.filter((r) => r.tipo === tipo);
      if (!linhas.length) return "";
      return `
        <h3 class="resc-grupo">${TIPO_TEXTO[tipo]}</h3>
        <table class="resc-tabela resc-verbas">
          <thead><tr><th>Cód.</th><th>Verba</th><th>Referência</th><th>Valor (R$)</th></tr></thead>
          <tbody>${linhas.map((r) => `
            <tr><td>${r.codigo}</td><td>${esc(r.descricao)}</td>
                <td><input type="text" id="resc-r-${r.codigo}" maxlength="40" placeholder="ex.: 15"></td>
                <td><input type="number" id="resc-v-${r.codigo}" data-codigo="${r.codigo}" data-tipo="${tipo}" min="0" step="0.01" placeholder="0,00"></td></tr>`).join("")}
          </tbody>
        </table>`;
    }).join("");
  }

  function lerFormulario() {
    const campos = {
      colaboradorId: $("resc-colaborador").value,
      dataDesligamento: $("resc-data").value,
      dataAvisoPrevio: $("resc-aviso").value,
      causa: $("resc-causa").value,
      codigoAfastamento: $("resc-codigo").value,
      remuneracao: $("resc-remuneracao").value,
      observacoes: $("resc-observacoes").value,
    };
    const linhas = Array.from(document.querySelectorAll("#resc-verbas input[data-codigo]")).map((entrada) => ({
      codigo: Number(entrada.dataset.codigo),
      tipo: entrada.dataset.tipo,
      valor: entrada.value,
      referencia: $(`resc-r-${entrada.dataset.codigo}`).value,
    }));
    return { campos, linhas };
  }

  function atualizarTotais() {
    const { linhas } = lerFormulario();
    const t = calcularTotais(linhas.map((l) => ({ tipo: l.tipo, centavos: centavos(l.valor) })));
    $("resc-t-prov").textContent = moeda(t.proventos);
    $("resc-t-desc").textContent = moeda(t.descontos);
    $("resc-t-liq").textContent = moeda(t.liquido);
  }

  async function abrirFormulario(rescisao) {
    mensagem("");
    try {
      if (!estado.rubricas.length) await carregarBase();
    } catch (erro) {
      mensagem(`Não foi possível carregar os dados do formulário: ${erro.message}`, "erro");
      return;
    }
    estado.editandoId = rescisao ? rescisao.id : null;
    mostrar("form");
    $("resc-form-titulo").textContent = rescisao ? `Corrigir rescisão #${rescisao.id}` : "Nova rescisão";

    const comRescisao = new Set(estado.rescisoes.map((r) => r.colaborador_id));
    const elegiveis = estado.colaboradores.filter((c) => {
      if (rescisao && c.id === rescisao.colaborador_id) return true;
      return (c.situacao || "ATIVO") !== "DESLIGADO" && !comRescisao.has(c.id); // uma rescisão por colaborador
    });
    $("resc-colaborador").innerHTML = '<option value="">Selecione...</option>' + elegiveis.map(
      (c) => `<option value="${c.id}">${esc(c.nome)} — ${esc(nomeEmpresa(c.empresa_id))}</option>`).join("");
    $("resc-colaborador").disabled = Boolean(rescisao); // ao corrigir, o colaborador não muda
    $("resc-causa").innerHTML = '<option value="">Selecione...</option>' + estado.motivos.map(
      (m) => `<option value="${esc(m)}">${esc(m)}</option>`).join("");
    $("resc-verbas").innerHTML = htmlVerbas(estado.rubricas);

    $("resc-form").reset();
    $("resc-sugestao-info").classList.add("resc-oculto");
    if (!rescisao && !elegiveis.length) {
      mensagem("Não há colaboradores disponíveis: todos já têm rescisão ou já estão desligados.", "erro");
    }
    if (rescisao) {
      $("resc-colaborador").value = String(rescisao.colaborador_id);
      $("resc-data").value = rescisao.data_desligamento || "";
      $("resc-aviso").value = rescisao.data_aviso_previo || "";
      $("resc-causa").value = rescisao.causa_afastamento;
      $("resc-codigo").value = rescisao.codigo_afastamento || "";
      $("resc-remuneracao").value = rescisao.remuneracao || "";
      $("resc-observacoes").value = rescisao.observacoes || "";
      rescisao.itens.forEach((i) => {
        const v = $(`resc-v-${i.codigo}`);
        if (v) v.value = i.valor;
        const ref = $(`resc-r-${i.codigo}`);
        if (ref) ref.value = i.referencia || "";
      });
    }
    atualizarTotais();
  }

  async function sugerirValores() {
    const { campos } = lerFormulario();
    if (!campos.colaboradorId || !campos.dataDesligamento || !campos.causa) {
      mensagem("Para sugerir valores, escolha o colaborador, a data de desligamento e a causa do afastamento.", "erro");
      return;
    }
    const remuneracao = centavos(campos.remuneracao);
    if (Number.isNaN(remuneracao)) {
      mensagem("Remuneração inválida.", "erro");
      return;
    }
    const botao = $("resc-sugerir");
    botao.disabled = true;
    try {
      const resposta = await api("/rescisoes/sugestao", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          colaborador_id: Number(campos.colaboradorId),
          data_desligamento: campos.dataDesligamento,
          causa_afastamento: campos.causa,
          remuneracao: remuneracao === null ? null : centavosParaTexto(remuneracao), // vazio = salário do cadastro
        }),
      });
      const jaTemValor = CODIGOS_SUGERIDOS.some((c) => ($(`resc-v-${c}`).value || "").trim() !== "");
      if (jaTemValor && !window.confirm(
        "Já existem valores digitados nas verbas sugeridas (saldo de salário, 13º, férias e FGTS). Substituir pelos valores sugeridos?"
      )) {
        return;
      }
      CODIGOS_SUGERIDOS.forEach((c) => { // limpa as 5 verbas e preenche só as que valem para este caso
        $(`resc-v-${c}`).value = "";
        $(`resc-v-${c}`).title = "";
        $(`resc-r-${c}`).value = "";
      });
      resposta.itens.forEach((i) => {
        const campo = $(`resc-v-${i.codigo}`);
        if (!campo) return;
        campo.value = i.valor;
        campo.title = i.explicacao;
        $(`resc-r-${i.codigo}`).value = i.referencia || "";
      });
      const info = $("resc-sugestao-info");
      info.innerHTML = `<strong>Valores sugeridos (edite o que precisar):</strong>
        <ul>${resposta.itens.map((i) => `<li>${i.codigo} — ${esc(i.descricao)}: ${esc(moedaTexto(i.valor))} <em>(${esc(i.explicacao)})</em></li>`).join("")}</ul>
        ${resposta.avisos.map((a) => `<p>${esc(a)}</p>`).join("")}`;
      info.classList.remove("resc-oculto");
      atualizarTotais();
      mensagem("Valores sugeridos preenchidos. Confira e ajuste o que for preciso antes de salvar.", "ok");
    } catch (erro) {
      mensagem(erro.message, "erro");
    } finally {
      botao.disabled = false;
    }
  }

  async function salvarFormulario(evento) {
    evento.preventDefault();
    const { campos, linhas } = lerFormulario();
    const resultado = montarPayload(campos, linhas);
    if (resultado.erro) {
      mensagem(resultado.erro, "erro");
      return;
    }
    const botao = $("resc-salvar");
    botao.disabled = true;
    const editando = estado.editandoId;
    try {
      const salvo = await api(editando ? `/rescisoes/${editando}` : "/rescisoes", {
        method: editando ? "PUT" : "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(resultado.payload),
      });
      await abrirDetalhe(salvo.id);
      mensagem(
        editando
          ? "Rescisão corrigida. Gere o PDF de novo para atualizar o documento."
          : "Rescisão criada. Confira os valores e gere o PDF.",
        "ok"
      );
    } catch (erro) {
      mensagem(erro.message, "erro");
    } finally {
      botao.disabled = false;
    }
  }

  // ---------- ligações ----------
  function iniciar() {
    if (!$("resc-lista") || !$("resc-historico") || !$("resc-h-busca") || !$("resc-sugerir")) return; // a página não tem as seções de rescisões e histórico

    const menu = document.querySelector('.menu-item[data-page="rescisao"]');
    if (menu) menu.addEventListener("click", carregarLista);

    $("resc-nova").addEventListener("click", () => abrirFormulario(null));
    $("resc-cancelar").addEventListener("click", () => (estado.editandoId ? abrirDetalhe(estado.editandoId) : carregarLista()));
    $("resc-form").addEventListener("submit", salvarFormulario);
    $("resc-sugerir").addEventListener("click", sugerirValores);
    $("resc-verbas").addEventListener("input", atualizarTotais);
    $("resc-form").addEventListener("input", () => { // o aviso de erro some quando a pessoa volta a digitar
      if ($("resc-mensagem").classList.contains("erro")) mensagem("");
    });

    const abrirLinha = (evento) => {
      const linha = evento.target.closest("tr[data-id]");
      if (!linha) return;
      estado.origem = "lista";
      abrirDetalhe(Number(linha.dataset.id));
    };
    $("resc-lista").addEventListener("click", abrirLinha);
    $("resc-lista").addEventListener("keydown", (e) => { if (e.key === "Enter") abrirLinha(e); });
    $("resc-mostrar-enviadas").addEventListener("change", desenharLista);

    const menuHistorico = document.querySelector('.menu-item[data-page="historico"]');
    if (menuHistorico) menuHistorico.addEventListener("click", carregarHistoricoDocumentos);
    let espera = null; // a busca por texto espera a pessoa parar de digitar
    $("resc-h-busca").addEventListener("input", () => {
      clearTimeout(espera);
      espera = setTimeout(carregarHistoricoDocumentos, 300);
    });
    $("resc-h-tipo").addEventListener("change", carregarHistoricoDocumentos);
    $("resc-h-status").addEventListener("change", carregarHistoricoDocumentos);
    $("resc-h-limpar").addEventListener("click", () => {
      $("resc-h-busca").value = "";
      $("resc-h-tipo").value = "";
      $("resc-h-status").value = "";
      carregarHistoricoDocumentos();
    });

    const abrirDoHistorico = (evento) => {
      const linha = evento.target.closest("tr[data-rescisao]");
      if (linha) irParaRescisao(Number(linha.dataset.rescisao), "historico");
    };
    $("resc-historico").addEventListener("click", abrirDoHistorico);
    $("resc-historico").addEventListener("keydown", (e) => { if (e.key === "Enter") abrirDoHistorico(e); });

    $("resc-detalhe").addEventListener("click", (evento) => {
      const botao = evento.target.closest("[data-acao]");
      if (!botao || !estado.atual) return;
      const id = estado.atual.id;
      const acao = botao.dataset.acao;
      if (acao === "voltar") {
        const histo = document.querySelector('.menu-item[data-page="historico"]');
        if (estado.origem === "historico" && histo) histo.click();
        else carregarLista();
      }
      if (acao === "corrigir") abrirFormulario(estado.atual);
      if (acao === "gerar") {
        executar(botao, () => api(`/rescisoes/${id}/gerar`, { method: "POST" }), "PDF gerado.", id);
      }
      if (acao === "enviar") {
        const destinatario = ($("resc-destinatario").value || "").trim();
        if (destinatario && !emailValido(destinatario)) {
          mensagem("E-mail de destino inválido. Use o formato nome@empresa.com.br.", "erro");
          return;
        }
        executar(botao, () => api(`/rescisoes/${id}/enviar`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(destinatario ? { destinatario } : {}),
        }), (estado.emailSimulado
          ? "E-mail gravado em modo de teste: nada foi enviado de verdade."
          : "E-mail enviado.")
          + (situacaoColaborador(estado.atual.colaborador_id) === "Desligado" ? "" : " O colaborador agora consta como desligado."), id);
      }
    });
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", iniciar);
  else iniciar();
})();
