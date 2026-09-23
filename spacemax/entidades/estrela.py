"""Cenario com estrelas (paralaxe vertical, ja que a acao e vertical)."""

import random

import pygame

from ..config import ALTURA, COR_ESTRELA, LARGURA
from .base import Entidade


class Estrela(Entidade):
    def __init__(self):
        super().__init__(random.uniform(0, LARGURA), random.uniform(0, ALTURA))
        self.tamanho: int = random.choice([1, 1, 1, 2, 2, 3])
        self.velocidade: float = self.tamanho * 0.5 + 0.3

    def atualizar(self):
        self.y += self.velocidade
        if self.y > ALTURA + 2:
            self.y = -2
            self.x = random.uniform(0, LARGURA)

    def desenhar(self, tela):
        pygame.draw.circle(tela, COR_ESTRELA, (int(self.x), int(self.y)), self.tamanho)
