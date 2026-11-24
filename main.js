"use strict";

/* =====================================================
   DogWorld · interações da página inicial
   ===================================================== */

const $ = (seletor, raiz = document) => raiz.querySelector(seletor);
const $$ = (seletor, raiz = document) => Array.from(raiz.querySelectorAll(seletor));
const reduzirMovimento = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
const cartoes = $$(".raca");

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
  botao.textContent = abrir ? "Fechar resumo" : "Conhecer raça";
}

btnBusca?.addEventListener("click", () => alternarBusca(painelBusca.hidden));

formBusca?.addEventListener("submit", (e) => {
  e.preventDefault();
  const termo = normalizar(campoBusca.value);
  limparDestaques();

  if (!termo) {
    msgBusca.textContent = "Digite o nome de uma raça para buscar.";
    return;
  }

  const achado = cartoes.find((c) => normalizar(c.dataset.nome).includes(termo));
  if (!achado) {
    msgBusca.textContent = "Nenhuma raça encontrada por enquanto. Novas raças chegarão em breve.";
    return;
  }

  msgBusca.textContent = `Encontrado: ${achado.dataset.nome}.`;
  achado.classList.add("destacada");
  abrirCartao(achado, true);
  achado.scrollIntoView({ behavior: reduzirMovimento ? "auto" : "smooth", block: "center" });
});

campoBusca?.addEventListener("input", () => {
  if (campoBusca.value) return;
  msgBusca.textContent = "";
  limparDestaques();
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
cartoes.forEach((cartao) => {
  const botao = $("button", cartao);
  botao.addEventListener("click", () => {
    abrirCartao(cartao, botao.getAttribute("aria-expanded") !== "true");
  });
});

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

/* ---------- Integração com a API (back-end Flask) ---------- */
/* Se a API estiver fora do ar, a página continua funcionando com o conteúdo do HTML. */
async function sincronizarComAPI() {
  if (typeof DogWorldAPI === "undefined") return;

  try {
    const { racas } = await DogWorldAPI.listarRacas();
    racas.forEach((raca) => {
      const cartao = cartoes.find((c) => c.dataset.slug === raca.slug);
      if (!cartao) return;
      $(".card__corpo > p", cartao).textContent = raca.descricao;
      const [porte, temperamento, vida] = $$(".raca__info li", cartao);
      porte.lastChild.textContent = ` ${raca.porte}`;
      temperamento.lastChild.textContent = ` ${raca.temperamento}`;
      vida.lastChild.textContent = ` ${raca.vida_media}`;
    });
  } catch (erro) {
    console.info("DogWorld: API indisponível, usando o conteúdo da página.", erro.message);
  }
}

/* Se a foto de um card não carregar, busca outra na API de cachorros */
async function trocarFotoQuebrada(img, slug) {
  if (img.dataset.reserva) return;
  img.dataset.reserva = "1";
  try {
    const { foto } = await DogWorldAPI.fotoDaRaca(slug);
    if (foto) img.src = foto;
  } catch (erro) {
    console.info("DogWorld: sem foto reserva para", slug);
  }
}

cartoes.forEach((cartao) => {
  const img = $("img", cartao);
  const slug = cartao.dataset.slug;
  if (!img || !slug || typeof DogWorldAPI === "undefined") return;
  img.addEventListener("error", () => trocarFotoQuebrada(img, slug));
  if (img.complete && img.naturalWidth === 0) trocarFotoQuebrada(img, slug);
});

sincronizarComAPI();