"""Tiro disparado pela nave na direcao em que ela aponta."""

import math

from .. import grafico
from ..config import ALCANCE_TIRO, COR_PRIMARIA, VELOCIDADE_TIRO
from .base import EntidadeColidivel


class Tiro(EntidadeColidivel):
    RAIO = 2
    COMPRIMENTO = 9

    def __init__(
        self, x: float, y: float, angulo: float, vx_nave: float = 0.0, vy_nave: float = 0.0
    ):
        rad = math.radians(angulo)
        # herda a velocidade da nave, como no Asteroids classico
        vx = math.sin(rad) * VELOCIDADE_TIRO + vx_nave
        vy = -math.cos(rad) * VELOCIDADE_TIRO + vy_nave
        super().__init__(x, y, self.RAIO, vx, vy)
        self.vida: int = ALCANCE_TIRO

    def atualizar(self):
        self.mover()
        self.vida -= 1

    def expirou(self):
        return self.vida <= 0

    def desenhar(self, tela):
        velocidade = math.hypot(self.vx, self.vy) or 1
        cauda = (
            self.x - self.vx / velocidade * self.COMPRIMENTO,
            self.y - self.vy / velocidade * self.COMPRIMENTO,
        )
        grafico.linha(tela, COR_PRIMARIA, cauda, (self.x, self.y))
