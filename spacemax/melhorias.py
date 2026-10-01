"""Melhorias da nave: a cada nivel novo o jogador escolhe uma entre tres cartas."""

import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Melhoria:
    chave: str
    nome: str
    descricao: str
    nivel_max: int


MELHORIAS = [
    Melhoria("cadencia", "CADENCIA", "atira 15% mais rapido", 4),
    Melhoria("multiplo", "TIRO MULTIPLO", "+1 tiro em leque", 2),
    Melhoria("alcance", "ALCANCE", "tiros vao 25% mais longe", 3),
    Melhoria("motor", "MOTOR", "+12% aceleracao e velocidade", 3),
    Melhoria("manobra", "MANOBRA", "gira 15% mais rapido", 3),
    Melhoria("escudo", "ESCUDO LONGO", "escudo dura +2 s", 3),
    Melhoria("arsenal", "ARSENAL", "+1 tiro explosivo", 3),
    Melhoria("recarga", "RECARGA", "explosivos recarregam 25% antes", 3),
    Melhoria("reparo", "REPARO", "recupera 1 vida", 99),
]
POR_CHAVE = {m.chave: m for m in MELHORIAS}
OPCOES_POR_NIVEL = 3
LIMITE_MELHORIAS = 10  # total de melhorias que a nave pode receber por partida


def sortear_opcoes(niveis: dict[str, int], pode_reparar: bool) -> list[Melhoria]:
    """Ate 3 melhorias diferentes que ainda nao chegaram ao maximo (nenhuma apos o limite)."""
    if total_escolhidas(niveis) >= LIMITE_MELHORIAS:
        return []
    disponiveis = [
        m for m in MELHORIAS
        if niveis.get(m.chave, 0) < m.nivel_max and (m.chave != "reparo" or pode_reparar)
    ]
    return random.sample(disponiveis, min(OPCOES_POR_NIVEL, len(disponiveis)))


def total_escolhidas(niveis: dict[str, int]) -> int:
    return sum(niveis.values())
