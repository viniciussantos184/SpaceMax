"""Personagem principal (nave que se move para os lados)."""

import pygame

from ..config import ALTURA, COOLDOWN_TIRO, COR_NAVE, COR_NAVE_BORDA, LARGURA, VELOCIDADE_NAVE
from .base import EntidadeColidivel
from .tiro import Tiro


class Nave(EntidadeColidivel):
    LARGURA = 40
    ALTURA = 28

    def __init__(self):
        super().__init__(LARGURA / 2, ALTURA - 60)
        self.escudo: bool = False
        self.cooldown_atual: int = 0

    def mover(self, direcao):
        self.x += direcao * VELOCIDADE_NAVE
        margem = self.LARGURA / 2
        self.x = max(margem, min(LARGURA - margem, self.x))

    def atualizar(self):
        if self.cooldown_atual > 0:
            self.cooldown_atual -= 1

    def pode_atirar(self):
        return self.cooldown_atual <= 0

    def atirar(self):
        self.cooldown_atual = COOLDOWN_TIRO
        return Tiro(self.x, self.y - self.ALTURA / 2)

    def rect(self):
        return pygame.Rect(
            int(self.x - self.LARGURA / 2),
            int(self.y - self.ALTURA / 2),
            self.LARGURA,
            self.ALTURA,
        )

    def desenhar(self, tela):
        pontos = [
            (0, -self.ALTURA / 2),
            (-self.LARGURA / 2, self.ALTURA / 2),
            (0, self.ALTURA / 4),
            (self.LARGURA / 2, self.ALTURA / 2),
        ]
        pontos_tela = [(self.x + px, self.y + py) for px, py in pontos]

        cor = (255, 215, 60) if self.escudo else COR_NAVE
        pygame.draw.polygon(tela, cor, pontos_tela)
        pygame.draw.polygon(tela, COR_NAVE_BORDA, pontos_tela, 2)

        if self.escudo:
            pygame.draw.circle(tela, (255, 230, 130), (int(self.x), int(self.y)), 28, 2)
