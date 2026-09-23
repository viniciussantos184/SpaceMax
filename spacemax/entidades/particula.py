"""Faiscas de explosao: pequenos tracos que se espalham e apagam."""

import math
import random

import pygame

from .. import grafico
from .base import Entidade


class Particula(Entidade):
    def __init__(
        self,
        x: float,
        y: float,
        cor: tuple[int, int, int] = (255, 255, 255),
        vx: float | None = None,
        vy: float | None = None,
        vida: int | None = None,
    ):
        """Sem vx/vy, a faisca sai numa direcao aleatoria (explosao)."""
        super().__init__(x, y)
        if vx is None or vy is None:
            angulo = random.uniform(0, 2 * math.pi)
            velocidade = random.uniform(1.0, 4.0)
            vx, vy = math.cos(angulo) * velocidade, math.sin(angulo) * velocidade
        self.vx: float = vx
        self.vy: float = vy
        self.vida: int = vida if vida is not None else random.randint(18, 36)
        self.vida_max: int = self.vida
        self.cor: tuple[int, int, int] = cor

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vx *= 0.96
        self.vy *= 0.96
        self.vida -= 1

    def morta(self):
        return self.vida <= 0

    def desenhar(self, tela):
        intensidade = max(0.0, self.vida / self.vida_max)
        cor = grafico.misturar(self.cor, intensidade)
        cauda = (self.x - self.vx * 2, self.y - self.vy * 2)
        pygame.draw.aaline(tela, cor, cauda, (self.x, self.y))
