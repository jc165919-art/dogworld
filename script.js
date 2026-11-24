"use strict";

/* =====================================================
   DogWorld · interações da página inicial
   ===================================================== */

const $ = (seletor, raiz = document) => raiz.querySelector(seletor);
const $$ = (seletor, raiz = document) => Array.from(raiz.querySelectorAll(seletor));
const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

/* ---------- Tema claro/escuro ---------- */
const btnTema = $("#btn-tema");

function atualizarBotaoTema() {
  if (!btnTema) return;
  const escuro = document.documentElement.dataset.tema === "escuro";
  const acao = escuro ? "Ativar modo claro" : "Ativar modo escuro";
  btnTema.setAttribute("aria-label", acao);
  btnTema.setAttribute("title", acao);
  btnTema.setAttribute("aria-pressed", String(escuro));
}

atualizarBotaoTema();

btnTema?.addEventListener("click", () => {
  const escuro = document.documentElement.dataset.tema !== "escuro";
  document.documentElement.dataset.tema = escuro ? "escuro" : "claro";
  atualizarBotaoTema();
  try {
    localStorage.setItem("dogworld-tema", escuro ? "escuro" : "claro");
  } catch (erro) {
    console.warn("DogWorld: não foi possível salvar a preferência de tema.", erro);
  }
});

/* ---------- Menu mobile ---------- */
const btnMenu = $("#btn-menu");
const menu = $("#menu");

function alternarMenu(abrir) {
  if (!btnMenu || !menu) return;
  menu.classList.toggle("aberto", abrir);
  btnMenu.setAttribute("aria-expanded", String(abrir));
  btnMenu.setAttribute("aria-label", abrir ? "Fechar menu" : "Abrir menu");
}

btnMenu?.addEventListener("click", () => {
  const abrir = !menu.classList.contains("aberto");
  if (abrir) alternarBusca(false);
  alternarMenu(abrir);
});

$$("a", menu).forEach((link) => link.addEventListener("click", () => alternarMenu(false)));

document.addEventListener("click", (e) => {
  if (menu?.classList.contains("aberto") && !menu.contains(e.target) && !btnMenu.contains(e.target)) {
    alternarMenu(false);
  }
});

window.matchMedia("(min-width: 821px)").addEventListener("change", (e) => {
  if (e.matches) alternarMenu(false);
});

/* ---------- Busca de raças ---------- */
const btnBusca = $("#btn-busca");
const painelBusca = $("#busca");
const formBusca = $("#form-busca");
const campoBusca = $("#campo-busca");
const msgBusca = $("#busca-msg");
const listaRacas = $("#racas-lista");
const msgRacas = $("#racas-msg");
const botaoMaisRacas = $("#racas-mais");
let cartoes = $$(".raca", listaRacas);
let paginaAtual = 0;
let termoAtual = "";
let requisicaoAtual = 0;

function urlApiRacas() {
  if (window.DOGWORLD_API_URL) return window.DOGWORLD_API_URL;
  const host = window.location.hostname || "127.0.0.1";
  const local = ["localhost", "127.0.0.1"].includes(host);
  return local
    ? `${window.location.protocol === "https:" ? "https:" : "http:"}//${host}:5000/api/racas`
    : "/api/racas";
}

function criarItemInfo(rotulo, valor) {
  const item = document.createElement("li");
  const titulo = document.createElement("strong");
  titulo.textContent = `${rotulo}:`;
  item.append(titulo, document.createTextNode(` ${valor}`));
  return item;
}

function criarCartao(raca, fotoFallback) {
  const cartao = document.createElement("article");
  cartao.className = "card raca";
  cartao.dataset.nome = raca.nome;
  cartao.dataset.id = raca.id;

  const imagem = document.createElement("img");
  const foto = typeof raca.foto === "string" && raca.foto.startsWith("https://")
    ? raca.foto
    : fotoFallback;
  if (foto) imagem.src = foto;
  else imagem.hidden = true;
  imagem.alt = raca.nome;
  imagem.loading = "lazy";
  imagem.width = 350;
  imagem.height = 260;

  const corpo = document.createElement("div");
  corpo.className = "card__corpo";

  const titulo = document.createElement("h3");
  titulo.textContent = raca.nome;

  const descricao = document.createElement("p");
  descricao.textContent = raca.resumo;

  const informacoes = document.createElement("ul");
  informacoes.className = "raca__info";
  informacoes.hidden = true;
  (raca.caracteristicas || []).forEach(({ rotulo, valor }) => {
    informacoes.append(criarItemInfo(rotulo, valor));
  });

  const botao = document.createElement("button");
  botao.className = "btn btn--small";
  botao.type = "button";
  botao.setAttribute("aria-expanded", "false");
  botao.textContent = "Ver características";

  corpo.append(titulo, descricao, informacoes, botao);
  cartao.append(imagem, corpo);
  return cartao;
}

async function carregarRacas(termo = "", pagina = 0, anexar = false) {
  const numeroRequisicao = ++requisicaoAtual;
  msgRacas.textContent = termo ? "Pesquisando raças..." : "Carregando raças...";
  botaoMaisRacas.disabled = true;

  try {
    const url = new URL(urlApiRacas(), window.location.href);
    url.searchParams.set("pagina", String(pagina));
    if (termo) url.searchParams.set("busca", termo);

    const resposta = await fetch(url);
    const dados = await resposta.json();
    if (!resposta.ok) throw new Error(dados.erro || `A API respondeu com HTTP ${resposta.status}.`);
    if (!Array.isArray(dados.resultados) || !Number.isInteger(dados.total)) {
      throw new Error("A API retornou uma lista de raças inválida.");
    }

    if (numeroRequisicao !== requisicaoAtual) return null;

    const fotosFallback = new Map(cartoes.map((cartao) => [
      normalizar(cartao.dataset.nome),
      $("img", cartao).src,
    ]));
    const novosCartoes = dados.resultados.map((raca) =>
      criarCartao(raca, fotosFallback.get(normalizar(raca.nome)) || "")
    );
    if (anexar) listaRacas.append(...novosCartoes);
    else listaRacas.replaceChildren(...novosCartoes);

    cartoes = $$(".raca", listaRacas);
    termoAtual = termo;
    paginaAtual = pagina;
    msgRacas.textContent = dados.total
      ? `Exibindo ${cartoes.length} de ${dados.total} raças.`
      : "Nenhuma raça encontrada.";
    botaoMaisRacas.hidden = !dados.tem_mais;
    return dados;
  } catch (erro) {
    if (numeroRequisicao !== requisicaoAtual) return null;
    console.error("Não foi possível carregar as raças da API:", erro);
    msgRacas.textContent = erro.message || "Não foi possível carregar as raças.";
    return null;
  } finally {
    if (numeroRequisicao === requisicaoAtual) botaoMaisRacas.disabled = false;
  }
}

function alternarBusca(abrir) {
  if (!painelBusca || !btnBusca) return;
  painelBusca.hidden = !abrir;
  btnBusca.setAttribute("aria-expanded", String(abrir));
  if (abrir) {
    alternarMenu(false);
    campoBusca.focus();
  }
}

/* Remove acentos e maiúsculas para comparar os nomes */
const normalizar = (texto) =>
  texto.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();

function limparDestaques() {
  cartoes.forEach((c) => c.classList.remove("destacada"));
}

function abrirCartao(cartao, abrir) {
  const lista = $(".raca__info", cartao);
  const botao = $("button", cartao);
  lista.hidden = !abrir;
  botao.setAttribute("aria-expanded", String(abrir));
  botao.textContent = abrir ? "Fechar características" : "Ver características";

  if (!abrir || !cartao.dataset.id || cartao.dataset.detalhesCarregados === "true"
    || cartao.dataset.carregandoDetalhes === "true") return;

  cartao.dataset.carregandoDetalhes = "true";
  fetch(`${urlApiRacas()}/${encodeURIComponent(cartao.dataset.id)}`)
    .then(async (resposta) => {
      const dados = await resposta.json();
      if (!resposta.ok) throw new Error(dados.erro || `A API respondeu com HTTP ${resposta.status}.`);
      if (!Array.isArray(dados.caracteristicas)) throw new Error("Detalhes da raça inválidos.");
      lista.replaceChildren(...dados.caracteristicas.map(({ rotulo, valor }) => criarItemInfo(rotulo, valor)));
      cartao.dataset.detalhesCarregados = "true";
    })
    .catch((erro) => {
      console.error(`Não foi possível carregar detalhes de ${cartao.dataset.nome}:`, erro);
      lista.append(criarItemInfo("Aviso", "Não foi possível carregar informações adicionais."));
      cartao.dataset.detalhesCarregados = "true";
    })
    .finally(() => {
      cartao.dataset.carregandoDetalhes = "false";
    });
}

btnBusca?.addEventListener("click", () => alternarBusca(painelBusca.hidden));

formBusca?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const termo = campoBusca.value.trim();
  limparDestaques();

  if (!termo) {
    msgBusca.textContent = "Digite o nome de uma raça para buscar.";
    return;
  }

  msgBusca.textContent = `Buscando “${termo}”...`;
  const dados = await carregarRacas(termo);
  if (!dados) {
    msgBusca.textContent = "A busca não pôde ser concluída. Confira a API e tente novamente.";
    return;
  }

  if (!dados.total) {
    msgBusca.textContent = `Nenhuma raça encontrada para “${termo}”.`;
    return;
  }

  const quantidade = dados.total === 1
    ? "1 raça encontrada"
    : `${dados.total} raças encontradas`;
  msgBusca.textContent = `${quantidade} para “${termo}”.`;
  if (cartoes.length === 1) {
    cartoes[0].classList.add("destacada");
    abrirCartao(cartoes[0], true);
    cartoes[0].scrollIntoView({ behavior: reduzirMovimento ? "auto" : "smooth", block: "center" });
  }
});

campoBusca?.addEventListener("input", () => {
  if (campoBusca.value) return;
  msgBusca.textContent = "";
  limparDestaques();
  carregarRacas();
});

botaoMaisRacas.addEventListener("click", () => {
  carregarRacas(termoAtual, paginaAtual + 1, true);
});

/* Atalho: "/" abre a busca quando você não está digitando */
document.addEventListener("keydown", (e) => {
  const digitando = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName) || document.activeElement?.isContentEditable;
  if (e.key === "/" && !digitando && !e.ctrlKey && !e.metaKey) {
    e.preventDefault();
    alternarBusca(true);
  }
  if (e.key === "Escape") {
    alternarMenu(false);
    if (painelBusca && !painelBusca.hidden) {
      alternarBusca(false);
      btnBusca.focus();
    }
  }
});

/* ---------- Botões "Conhecer raça" ---------- */
listaRacas.addEventListener("click", (evento) => {
  const botao = evento.target.closest("button");
  if (!botao || !listaRacas.contains(botao)) return;
  const cartao = botao.closest(".raca");
  abrirCartao(cartao, botao.getAttribute("aria-expanded") !== "true");
});

carregarRacas();

/* ---------- Link ativo no menu conforme a seção visível ---------- */
const secoes = [
  { hash: "#topo", el: null },
  { hash: "#racas", el: $("#racas") },
  { hash: "#cuidados", el: $("#cuidados") },
];

/* Vários links apontam para #cuidados: só o primeiro de cada destino fica ativo */
const linkPorHash = new Map();
$$("a", menu).forEach((a) => {
  const hash = a.getAttribute("href");
  if (!linkPorHash.has(hash)) linkPorHash.set(hash, a);
});

function marcarSecaoAtiva() {
  const referencia = window.innerHeight * 0.4;
  let atual = "#topo";
  secoes.forEach(({ hash, el }) => {
    if (el && el.getBoundingClientRect().top <= referencia) atual = hash;
  });
  linkPorHash.forEach((link, hash) => {
    if (hash === atual) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
}

/* ---------- Botão de voltar ao topo ---------- */
const btnTopo = document.createElement("button");
btnTopo.type = "button";
btnTopo.className = "topo-btn";
btnTopo.hidden = true;
btnTopo.setAttribute("aria-label", "Voltar ao topo");
btnTopo.innerHTML = '<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="m6 14 6-6 6 6"/></svg>';
btnTopo.addEventListener("click", () => {
  window.scrollTo({ top: 0, behavior: reduzirMovimento ? "auto" : "smooth" });
});
document.body.appendChild(btnTopo);

/* ---------- Scroll (uma única passada por frame) ---------- */
let aguardando = false;
function aoRolar() {
  if (aguardando) return;
  aguardando = true;
  requestAnimationFrame(() => {
    marcarSecaoAtiva();
    btnTopo.hidden = window.scrollY < 700;
    aguardando = false;
  });
}
window.addEventListener("scroll", aoRolar, { passive: true });
window.addEventListener("resize", aoRolar, { passive: true });
marcarSecaoAtiva();

/* ---------- Ano no rodapé ---------- */
const ano = $("#ano");
if (ano) ano.textContent = new Date().getFullYear();