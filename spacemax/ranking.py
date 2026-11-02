"""Ranking persistente: a pontuacao de cada jogador ao fim de cada partida, salva em ranking.json."""

import json
from datetime import datetime

from .config import CAMINHO_RANKING

LIMITE_POR_CATEGORIA = 50  # entradas guardadas por modo e dificuldade


def carregar_ranking() -> list[dict]:
    try:
        with open(CAMINHO_RANKING, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
    except (FileNotFoundError, ValueError, OSError):
        return []
    if not isinstance(dados, list):
        return []
    return [e for e in dados if isinstance(e, dict) and isinstance(e.get("pontos"), int)]


def salvar_ranking(entradas: list[dict]):
    try:
        with open(CAMINHO_RANKING, "w", encoding="utf-8") as arquivo:
            json.dump(entradas, arquivo, ensure_ascii=False, indent=2)
    except OSError:
        pass


def _categoria(entrada) -> tuple[str, str]:
    return entrada.get("modo"), entrada.get("dificuldade")


def nova_entrada(nome, pontos, modo, dificuldade, nivel) -> dict:
    return {
        "nome": nome,
        "pontos": pontos,
        "modo": modo,
        "dificuldade": dificuldade,
        "nivel": nivel,
        "data": datetime.now().isoformat(timespec="seconds"),
    }


def adicionar(entradas: list[dict], novas: list[dict]) -> list[dict]:
    """Junta as entradas novas ao ranking, mantem so as melhores de cada categoria e ordena por pontos.

    Em empate de pontos a entrada mais antiga fica na frente (a ordenacao e estavel)."""
    todas = entradas + novas
    todas.sort(key=lambda e: e["pontos"], reverse=True)
    contagem: dict[tuple[str, str], int] = {}
    mantidas = []
    for entrada in todas:
        categoria = _categoria(entrada)
        contagem[categoria] = contagem.get(categoria, 0) + 1
        if contagem[categoria] <= LIMITE_POR_CATEGORIA:
            mantidas.append(entrada)
    return mantidas


def melhores(entradas: list[dict], modo: str, dificuldade: str, quantidade: int = 5) -> list[dict]:
    """As `quantidade` melhores entradas do modo e da dificuldade (ja ordenadas)."""
    da_categoria = [e for e in entradas if _categoria(e) == (modo, dificuldade)]
    return da_categoria[:quantidade]
