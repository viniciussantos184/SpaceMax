"""Tiro disparado pela nave."""

import pygame

from ..config import COR_TIRO, VELOCIDADE_TIRO
from .base import EntidadeColidivel


class Tiro(EntidadeColidivel):
    LARGURA = 4
    ALTURA = 14

    def __init__(self, x: float, y: float):
        super().__init__(x, y)

    def atualizar(self):
        self.y -= VELOCIDADE_TIRO

    def fora_da_tela(self):
        return self.y + self.ALTURA < 0

    def rect(self):
        return pygame.Rect(
            int(self.x - self.LARGURA / 2),
            int(self.y - self.ALTURA / 2),
            self.LARGURA,
            self.ALTURA,
        )

    def desenhar(self, tela):
        pygame.draw.rect(tela, COR_TIRO, self.rect(), border_radius=2)
