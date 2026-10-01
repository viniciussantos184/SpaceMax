"""Tiros disparados pela nave na direcao em que ela aponta (normal e explosivo)."""

import math

from .. import grafico
import pygame

from ..config import (
    ALCANCE_TIRO,
    ALCANCE_TIRO_EXPLOSIVO,
    COR_EXPLOSIVO,
    COR_PRIMARIA,
    VELOCIDADE_TIRO,
    VELOCIDADE_TIRO_EXPLOSIVO,
)
from .base import EntidadeColidivel


class Tiro(EntidadeColidivel):
    RAIO = 2
    COMPRIMENTO = 9
    VELOCIDADE = VELOCIDADE_TIRO
    ALCANCE = ALCANCE_TIRO
    EXPLOSIVO = False

    def __init__(
        self,
        x: float,
        y: float,
        angulo: float,
        vx_nave: float = 0.0,
        vy_nave: float = 0.0,
        alcance: int | None = None,
    ):
        rad = math.radians(angulo)
        # herda a velocidade da nave, como no Asteroids classico
        vx = math.sin(rad) * self.VELOCIDADE + vx_nave
        vy = -math.cos(rad) * self.VELOCIDADE + vy_nave
        super().__init__(x, y, self.RAIO, vx, vy)
        self.vida: int = alcance or self.ALCANCE

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


class TiroExplosivo(Tiro):
    """Mais lento e maior; explode ao acertar algo ou ao fim do alcance."""

    RAIO = 5
    VELOCIDADE = VELOCIDADE_TIRO_EXPLOSIVO
    ALCANCE = ALCANCE_TIRO_EXPLOSIVO
    EXPLOSIVO = True

    def desenhar(self, tela):
        pulso = 1 + 0.35 * math.sin(self.vida * 0.6)
        pygame.draw.circle(tela, grafico.misturar(COR_EXPLOSIVO, 0.3), (int(self.x), int(self.y)), int(8 * pulso))
        grafico.circulo(tela, COR_EXPLOSIVO, (self.x, self.y), self.RAIO)
        grafico.circulo(tela, (255, 230, 200), (self.x, self.y), 2, 0)
