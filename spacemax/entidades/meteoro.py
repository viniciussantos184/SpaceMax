"""Meteoros que caem do topo."""

import math
import random

import pygame

from ..config import ALTURA, COR_METEORO, COR_METEORO_BORDA, LARGURA
from .base import EntidadeColidivel


class Meteoro(EntidadeColidivel):
    def __init__(self, velocidade_min: float, velocidade_max: float):
        self.raio: int = random.randint(16, 30)
        super().__init__(random.uniform(self.raio, LARGURA - self.raio), -self.raio)
        self.velocidade_y: float = random.uniform(velocidade_min, velocidade_max)
        self.velocidade_x: float = random.uniform(-1.0, 1.0)
        self.angulo: float = 0
        self.velocidade_angular: float = random.uniform(-3, 3)
        # vida proporcional ao tamanho: meteoros grandes exigem mais de 1 tiro
        self.vida: int = 1 if self.raio < 23 else 2

        pontos = random.randint(7, 10)
        self.forma: list[tuple[float, float]] = []
        for i in range(pontos):
            ang = (2 * math.pi / pontos) * i
            variacao = random.uniform(0.75, 1.0)
            self.forma.append((ang, variacao))

    def atualizar(self):
        self.y += self.velocidade_y
        self.x += self.velocidade_x
        self.angulo += self.velocidade_angular

        if self.x - self.raio < 0 or self.x + self.raio > LARGURA:
            self.velocidade_x *= -1
            self.x = max(self.raio, min(LARGURA - self.raio, self.x))

    def fora_da_tela(self):
        return self.y - self.raio > ALTURA

    def levar_dano(self):
        self.vida -= 1
        return self.vida <= 0

    def rect(self):
        return pygame.Rect(
            int(self.x - self.raio), int(self.y - self.raio), self.raio * 2, self.raio * 2
        )

    def desenhar(self, tela):
        angulo_rad = math.radians(self.angulo)
        pontos_tela = []
        for ang, variacao in self.forma:
            a = ang + angulo_rad
            r = self.raio * variacao
            pontos_tela.append((self.x + r * math.cos(a), self.y + r * math.sin(a)))

        pygame.draw.polygon(tela, COR_METEORO, pontos_tela)
        pygame.draw.polygon(tela, COR_METEORO_BORDA, pontos_tela, 2)
