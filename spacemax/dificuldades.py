"""Niveis de dificuldade: multiplicadores aplicados sobre os valores de config.py.

DIFICIL e o jogo original (todos os fatores em 1.0); MEDIO e FACIL aliviam a partida."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Dificuldade:
    chave: str
    nome: str
    resumo: str
    vidas_extra: int = 0  # somadas as vidas iniciais e ao maximo de vidas
    velocidade_asteroide: float = 1.0
    intervalo_spawn: float = 1.0  # maior = asteroides novos chegam mais devagar
    asteroides: float = 1.0  # quantidade na onda e limite na tela
    invencivel: float = 1.0  # duracao da invencibilidade ao perder uma vida
    intervalo_escudo: float = 1.0  # menor = escudos aparecem com mais frequencia
    vida_chefe: float = 1.0
    ritmo_chefe: float = 1.0  # maior = o chefe ataca menos
    velocidade_projetil: float = 1.0


DIFICULDADES = [
    Dificuldade(
        "facil", "FACIL", "asteroides lentos, chefes fracos, 2 vidas extras e mais escudos",
        vidas_extra=2, velocidade_asteroide=0.7, intervalo_spawn=1.6, asteroides=0.6, invencivel=1.5,
        intervalo_escudo=0.65, vida_chefe=0.55, ritmo_chefe=1.5, velocidade_projetil=0.75,
    ),
    Dificuldade(
        "medio", "MEDIO", "ritmo moderado, 1 vida extra e chefes um pouco mais fracos",
        vidas_extra=1, velocidade_asteroide=0.85, intervalo_spawn=1.25, asteroides=0.8, invencivel=1.25,
        intervalo_escudo=0.85, vida_chefe=0.8, ritmo_chefe=1.2, velocidade_projetil=0.88,
    ),
    Dificuldade("dificil", "DIFICIL", "o desafio original: asteroides rapidos e chefes completos"),
]
DIFICULDADE_PADRAO = 1  # MEDIO


def chave_recorde(modo, dificuldade) -> str:
    """O recorde e separado por dificuldade; o DIFICIL usa a chave antiga (os recordes ja salvos eram dele)."""
    if dificuldade.chave == "dificil":
        return modo.chave
    return f"{modo.chave}_{dificuldade.chave}"
