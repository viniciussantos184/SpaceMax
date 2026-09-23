"""Cenario: poeira estelar discreta com leve paralaxe."""

import random

import pygame

from .. import grafico
from ..config import ALTURA, COR_ESTRELA, LARGURA
from .base import Entidade


class Estrela(Entidade):
    def __init__(self):
        super().__init__(random.uniform(0, LARGURA), random.uniform(0, ALTURA))
        self.profundidade: float = random.uniform(0.2, 1.0)
        self.velocidade: float = 0.12 * self.profundidade
        self.cor: tuple[int, int, int] = COR_ESTRELA
        self.tingir(COR_ESTRELA)

    def tingir(self, cor_base):
        """Ajusta a cor da estrela ao tom da galaxia atual."""
        self.cor = grafico.misturar(cor_base, self.profundidade)

    def atualizar(self):
        self.y += self.velocidade
        if self.y > ALTURA:
            self.y = 0
            self.x = random.uniform(0, LARGURA)

    def desenhar(self, tela):
        if self.profundidade > 0.85:
            pygame.draw.circle(tela, self.cor, (int(self.x), int(self.y)), 1)
        else:
            tela.set_at((int(self.x), int(self.y)), self.cor)
