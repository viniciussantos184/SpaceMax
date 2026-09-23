"""Particulas de explosao (efeito visual simples)."""

import math
import random

import pygame

from .base import Entidade


class Particula(Entidade):
    def __init__(self, x: float, y: float):
        super().__init__(x, y)
        angulo = random.uniform(0, 2 * math.pi)
        velocidade = random.uniform(1.5, 4.5)
        self.vx: float = math.cos(angulo) * velocidade
        self.vy: float = math.sin(angulo) * velocidade
        self.vida: int = random.randint(15, 30)
        self.vida_max: int = self.vida
        self.raio: int = random.randint(2, 4)

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1

    def morta(self):
        return self.vida <= 0

    def desenhar(self, tela):
        alpha = max(0, self.vida / self.vida_max)
        cor = (
            int(255 * alpha + 90 * (1 - alpha)),
            int(180 * alpha + 60 * (1 - alpha)),
            int(60 * alpha),
        )
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), self.raio)
