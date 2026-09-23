"""Item especial (escudo temporario)."""

import random

import pygame

from ..config import ALTURA, COR_ITEM, LARGURA
from .base import EntidadeColidivel


class Item(EntidadeColidivel):
    RAIO = 12

    def __init__(self):
        super().__init__(random.uniform(self.RAIO, LARGURA - self.RAIO), -self.RAIO)
        self.velocidade_y: float = 2.5
        self.coletado: bool = False

    def atualizar(self):
        self.y += self.velocidade_y

    def fora_da_tela(self):
        return self.y - self.RAIO > ALTURA

    def rect(self):
        return pygame.Rect(
            int(self.x - self.RAIO), int(self.y - self.RAIO), self.RAIO * 2, self.RAIO * 2
        )

    def desenhar(self, tela):
        pygame.draw.circle(tela, COR_ITEM, (int(self.x), int(self.y)), self.RAIO)
        pygame.draw.circle(tela, (255, 255, 255), (int(self.x), int(self.y)), self.RAIO, 2)
