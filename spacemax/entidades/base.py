"""Classes base das entidades do jogo."""

import math
from abc import ABC, abstractmethod

from ..config import ALTURA, LARGURA


class Entidade(ABC):
    """Qualquer objeto com posicao que e atualizado e desenhado a cada frame."""

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    @abstractmethod
    def atualizar(self):
        ...

    @abstractmethod
    def desenhar(self, tela):
        ...


class EntidadeColidivel(Entidade):
    """
    Entidade que se move no espaco e participa do sistema de colisao.

    Tem velocidade propria, colisao circular (pelo `raio`) e atravessa as
    bordas da tela, reaparecendo do lado oposto.
    """

    def __init__(self, x: float, y: float, raio: float, vx: float = 0.0, vy: float = 0.0):
        super().__init__(x, y)
        self.raio: float = raio
        self.vx: float = vx
        self.vy: float = vy

    def mover(self):
        self.x += self.vx
        self.y += self.vy
        self.atravessar_bordas()

    def atravessar_bordas(self):
        r = self.raio
        if self.x < -r:
            self.x += LARGURA + 2 * r
        elif self.x > LARGURA + r:
            self.x -= LARGURA + 2 * r
        if self.y < -r:
            self.y += ALTURA + 2 * r
        elif self.y > ALTURA + r:
            self.y -= ALTURA + 2 * r

    def colide_com(self, outra: "EntidadeColidivel") -> bool:
        return math.hypot(self.x - outra.x, self.y - outra.y) < self.raio + outra.raio
