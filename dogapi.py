"""Cliente da TheDogAPI; a chave permanece somente no backend."""
import os
from pathlib import Path

# O modelo de tradução fica dentro do projeto (a mesma pasta usada no setup_translation.py)
os.environ.setdefault("XDG_DATA_HOME", str(Path(__file__).resolve().parent / ".data"))

import re
import threading
import time
import unicodedata
from difflib import SequenceMatcher
from functools import lru_cache
from typing import Any

import argostranslate.translate
import requests
from flask import current_app

_CACHE: dict[tuple[str, tuple[tuple[str, str], ...]], tuple[float, Any, int]] = {}
_CACHE_TTL_SECONDS = 600
_TRADUCAO_LOCK = threading.RLock()

_CAMPOS_INFO = (
    ("bred_for", "Criada para"),
    ("breed_group", "Grupo"),
    ("life_span", "Expectativa de vida"),
    ("temperament", "Temperamento"),
    ("origin", "Origem"),
    ("country_code", "Código do país"),
    ("description", "Descrição"),
    ("history", "História"),
    ("alt_names", "Outros nomes"),
    ("perfect_for", "Ideal para"),
    ("male_height_cm", "Altura dos machos (cm)"),
    ("female_height_cm", "Altura das fêmeas (cm)"),
    ("male_weight_kg", "Peso dos machos (kg)"),
    ("female_weight_kg", "Peso das fêmeas (kg)"),
    ("family_friendly", "Convivência com a família"),
    ("good_with_other_dogs_score", "Compatibilidade com outros cães (de 5)"),
    ("good_with_other_dogs_context", "Convivência com outros cães"),
    ("shedding_score", "Queda de pelos (de 5)"),
    ("shedding_reason", "Detalhes da queda de pelos"),
    ("grooming_score", "Necessidade de tosa (de 5)"),
    ("grooming_type", "Cuidados com a pelagem"),
    ("daily_exercise_time_minutes", "Exercício diário (minutos)"),
    ("exercise_type", "Tipo de exercício"),
    ("bidability_score", "Facilidade de treinamento (de 5)"),
    ("bidability_characteristics", "Treinabilidade"),
    ("prey_drive_score", "Instinto de caça (de 5)"),
    ("prey_drive_reason", "Detalhes do instinto de caça"),
    ("barking_score", "Tendência a latir (de 5)"),
    ("barking_characteristics", "Comportamento dos latidos"),
    ("wikipedia_url", "Mais informações"),
)

_GRUPOS_TRADUZIDOS = {
    "herding": "Pastoreio",
    "hound": "Farejador",
    "mixed": "Misto",
    "non-sporting": "Não esportivo",
    "sporting": "Esportivo",
    "working": "Trabalho",
}


class TheDogAPIError(Exception):
    def __init__(self, message: str, status_code: int = 502) -> None:
        super().__init__(message)
        self.status_code = status_code


def _obter(endpoint: str, parametros: dict[str, str | int] | None = None) -> tuple[Any, int]:
    cfg = current_app.config
    chave = cfg["DOG_API_KEY"].strip()
    if not chave:
        raise TheDogAPIError(
            "Configure DOG_API_KEY no arquivo .env e reinicie o backend.",
            status_code=503,
        )

    parametros = parametros or {}
    chave_cache = (
        endpoint,
        tuple(sorted((str(chave), str(valor)) for chave, valor in parametros.items())),
    )
    agora = time.time()
    guardado = _CACHE.get(chave_cache)
    if guardado and agora - guardado[0] < _CACHE_TTL_SECONDS:
        return guardado[1], guardado[2]

    url = f"{cfg['DOG_API_URL']}/{endpoint.lstrip('/')}"
    try:
        resposta = requests.get(
            url,
            params=parametros,
            headers={"x-api-key": chave},
            timeout=cfg["DOG_API_TIMEOUT"],
        )
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.HTTPError as erro:
        codigo = erro.response.status_code if erro.response is not None else 502
        current_app.logger.warning("TheDogAPI respondeu HTTP %s em %s.", codigo, endpoint)
        if codigo == 404:
            raise TheDogAPIError("Raça não encontrada.", status_code=404) from erro
        raise TheDogAPIError(
            "A TheDogAPI rejeitou a solicitação. Confira a chave e os limites da conta."
        ) from erro
    except (requests.RequestException, ValueError) as erro:
        current_app.logger.warning("Falha ao consultar TheDogAPI em %s: %s", endpoint, erro)
        raise TheDogAPIError(
            "Não foi possível consultar a TheDogAPI. Verifique a conexão e tente novamente."
        ) from erro

    total = len(dados) if isinstance(dados, list) else 1
    try:
        total = int(resposta.headers.get("pagination-count", total))
    except (TypeError, ValueError):
        pass

    _CACHE[chave_cache] = (agora, dados, total)
    return dados, total


def _texto(valor: Any) -> str | None:
    if isinstance(valor, bool):
        return "Sim" if valor else "Não"
    if isinstance(valor, (str, int, float)):
        texto = str(valor).strip()
        return texto or None
    if isinstance(valor, list):
        itens = [str(item).strip() for item in valor if item is not None and str(item).strip()]
        return ", ".join(itens) or None
    return None


@lru_cache(maxsize=1)
def _obter_tradutor() -> Any:
    with _TRADUCAO_LOCK:
        idiomas = {
            idioma.code: idioma
            for idioma in argostranslate.translate.get_installed_languages()
        }
        origem = idiomas.get("en")
        destino = idiomas.get("pt")
        if origem is None or destino is None:
            return None
        return origem.get_translation(destino)


@lru_cache(maxsize=4096)
def _traduzir(texto: str) -> str:
    if not any(caractere.isalpha() for caractere in texto):
        return texto

    with _TRADUCAO_LOCK:
        tradutor = _obter_tradutor()
        if tradutor is None:
            raise TheDogAPIError(
                "O modelo de tradução inglês-português não está instalado. "
                "Execute python setup_translation.py e reinicie o backend.",
                status_code=503,
            )

        return tradutor.translate(texto)


def _traduzir_campo(campo: str, texto: str) -> str:
    if campo == "breed_group":
        grupo = _GRUPOS_TRADUZIDOS.get(texto.casefold())
        if grupo:
            return grupo
    if campo == "life_span" and re.fullmatch(r"\d+(?:\s*-\s*\d+)?", texto):
        return f"{texto} anos"
    return _traduzir(texto)


def _formatar_raca(
    dados: dict[str, Any],
    incluir_caracteristicas: bool = True,
) -> dict[str, Any]:
    caracteristicas: list[dict[str, str]] = []

    if incluir_caracteristicas:
        for campo, rotulo in (("weight", "Peso"), ("height", "Altura")):
            medidas = dados.get(campo)
            if isinstance(medidas, dict):
                metricas = _texto(medidas.get("metric"))
                imperiais = _texto(medidas.get("imperial"))
                if metricas:
                    metricas = _traduzir(metricas)
                if imperiais:
                    imperiais = _traduzir(imperiais)
                valores = []
                if metricas:
                    unidade = "kg" if campo == "weight" else "cm"
                    valores.append(f"{metricas} {unidade}")
                if imperiais:
                    unidade = "lb" if campo == "weight" else "pol."
                    valores.append(f"{imperiais} {unidade}")
                if valores:
                    caracteristicas.append({"rotulo": rotulo, "valor": " / ".join(valores)})

        for campo, rotulo in _CAMPOS_INFO:
            valor = _texto(dados.get(campo))
            if valor:
                if campo != "wikipedia_url":
                    valor = _traduzir_campo(campo, valor)
                caracteristicas.append({"rotulo": rotulo, "valor": valor})

    imagem = dados.get("image")
    foto = imagem.get("url") if isinstance(imagem, dict) else None
    if not isinstance(foto, str) or not foto.startswith("https://"):
        foto = None

    nome = _texto(dados.get("name")) or "Raça sem nome"
    resumo = (
        _texto(dados.get("description"))
        or _texto(dados.get("bred_for"))
        or _texto(dados.get("temperament"))
    )
    if resumo:
        resumo = _traduzir(resumo)
    else:
        resumo = "Consulte as características para conhecer esta raça."

    return {
        "id": str(dados.get("id", "")),
        "nome": nome,
        "resumo": resumo,
        "foto": foto,
        "caracteristicas": caracteristicas,
    }


def _normalizar_nome(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto.casefold())
    sem_acentos = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", sem_acentos).split())


def _similaridade_busca(busca: str, nome: str) -> float:
    palavras_busca = busca.split()
    palavras_nome = nome.split()
    if not palavras_busca or not palavras_nome:
        return 0.0

    pontuacoes = []
    for palavra in palavras_busca:
        similaridades = [
            SequenceMatcher(None, palavra, palavra_nome).ratio()
            for palavra_nome in palavras_nome
            if min(len(palavra), len(palavra_nome))
            / max(len(palavra), len(palavra_nome)) >= 0.75
        ]
        pontuacoes.append(max(
            [1.0 if palavra in nome else 0.0, *similaridades]
        ))

    frase_busca = busca.replace(" ", "")
    frase_nome = nome.replace(" ", "")
    similaridade_frase = SequenceMatcher(None, frase_busca, frase_nome).ratio()
    return max(sum(pontuacoes) / len(pontuacoes), similaridade_frase)


def listar_racas(busca: str, pagina: int, limite: int) -> tuple[list[dict[str, Any]], int]:
    if busca:
        catalogo, _ = _obter("breeds", {"page": 0, "limit": 1000, "order": "ASC"})
        if not isinstance(catalogo, list):
            raise TheDogAPIError("A TheDogAPI retornou uma lista de raças inválida.")

        busca_normalizada = _normalizar_nome(busca)
        if len(busca_normalizada.replace(" ", "")) < 3:
            return [], 0

        correspondencias = []
        for raca in catalogo:
            if not isinstance(raca, dict):
                continue
            nome = _normalizar_nome(_texto(raca.get("name")) or "")
            similaridade = _similaridade_busca(busca_normalizada, nome)
            limite_similaridade = 0.65 if len(busca_normalizada.replace(" ", "")) <= 3 else 0.72
            if similaridade >= limite_similaridade:
                correspondencias.append((similaridade, nome, raca))

        correspondencias.sort(key=lambda item: (-item[0], item[1]))
        total = len(correspondencias)
        inicio = pagina * limite
        racas = [raca for _, _, raca in correspondencias[inicio:inicio + limite]]
        return [
            _formatar_raca(raca, incluir_caracteristicas=False)
            for raca in racas
        ], total

    dados, total = _obter("breeds", {"page": pagina, "limit": limite, "order": "ASC"})
    if not isinstance(dados, list):
        raise TheDogAPIError("A TheDogAPI retornou uma lista de raças inválida.")
    return [
        _formatar_raca(raca, incluir_caracteristicas=False)
        for raca in dados
        if isinstance(raca, dict)
    ], total


def buscar_raca(raca_id: int) -> dict[str, Any]:
    dados, _ = _obter(f"breeds/{raca_id}")
    if not isinstance(dados, dict):
        raise TheDogAPIError("A TheDogAPI retornou dados inválidos para esta raça.")
    return _formatar_raca(dados)