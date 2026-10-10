"""Jogador: uma nave com suas teclas, vidas e pontos."""

from dataclasses import dataclass, field

import pygame

from .config import PONTOS_POR_VIDA
from .entidades.nave import Nave


@dataclass(frozen=True)
class Teclas:
    esquerda: tuple[int, ...]
    direita: tuple[int, ...]
    cima: tuple[int, ...]
    baixo: tuple[int, ...]
    tiro: tuple[int, ...]
    dash: tuple[int, ...]
    arma: tuple[int, ...]


TECLAS_SOLO = Teclas(
    esquerda=(pygame.K_LEFT, pygame.K_a),
    direita=(pygame.K_RIGHT, pygame.K_d),
    cima=(pygame.K_UP, pygame.K_w),
    baixo=(pygame.K_DOWN, pygame.K_s),
    tiro=(pygame.K_SPACE,),
    dash=(pygame.K_LCTRL, pygame.K_RCTRL),
    arma=(pygame.K_q, pygame.K_TAB),
)
TECLAS_JOGADOR1 = Teclas(
    esquerda=(pygame.K_a,),
    direita=(pygame.K_d,),
    cima=(pygame.K_w,),
    baixo=(pygame.K_s,),
    tiro=(pygame.K_SPACE,),
    dash=(pygame.K_LCTRL,),
    arma=(pygame.K_q, pygame.K_TAB),
)
TECLAS_JOGADOR2 = Teclas(
    esquerda=(pygame.K_LEFT,),
    direita=(pygame.K_RIGHT,),
    cima=(pygame.K_UP,),
    baixo=(pygame.K_DOWN,),
    tiro=(pygame.K_RSHIFT,),
    dash=(pygame.K_RCTRL,),
    arma=(pygame.K_SLASH,),
)


@dataclass(frozen=True)
class Dispositivo:
    """Com o que o jogador joga: um dos dois esquemas de teclado ou um controle."""

    nome: str = field(compare=False)  # so para mostrar; dois dispositivos iguais tem as mesmas teclas / o mesmo controle
    teclas: Teclas | None = None
    controle: int | None = None  # instance_id do controle (None = teclado)


TECLADO_JOGADOR1 = Dispositivo("TECLADO  ·  WASD", TECLAS_JOGADOR1)
TECLADO_JOGADOR2 = Dispositivo("TECLADO  ·  SETAS", TECLAS_JOGADOR2)


class Jogador:
    def __init__(self, indice: int, nave: Nave, teclas: Teclas | None, vidas: int, controle: int | None = None):
        self.indice: int = indice
        self.nave: Nave = nave
        self.teclas: Teclas | None = teclas  # None: joga so com controle
        self.controle: int | None = controle  # instance_id do controle (None: teclado; no solo, qualquer um)
        self.vidas: int = vidas
        self.pontuacao: int = 0
        self.pontos_proxima_vida: int = PONTOS_POR_VIDA
        self.melhorias_pendentes: int = 0
        self.rounds_ganhos: int = 0
        self.tempo_eliminado: int | None = None  # frame da partida em que perdeu a ultima vida

    @property
    def vivo(self) -> bool:
        return self.vidas > 0

    @property
    def cor(self) -> tuple[int, int, int]:
        return self.nave.cor
