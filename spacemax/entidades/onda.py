"""Onda de choque: anel que se expande e apaga (efeito visual)."""

import pygame

from .. import grafico
from .base import Entidade


class Onda(Entidade):
    def __init__(
        self,
        x: float,
        y: float,
        cor: tuple[int, int, int],
        raio_final: float = 60,
        duracao: int = 22,
        raio_inicial: float = 4,
    ):
        super().__init__(x, y)
        self.cor: tuple[int, int, int] = cor
        self.raio_inicial: float = raio_inicial
        self.raio_final: float = raio_final
        self.duracao: int = duracao
        self.tempo: int = 0

    @property
    def progresso(self) -> float:
        return min(1.0, self.tempo / self.duracao)

    def atualizar(self):
        self.tempo += 1

    def terminou(self):
        return self.tempo >= self.duracao

    def desenhar(self, tela):
        # desacelera ao crescer (ease-out) e apaga no fim
        p = 1 - (1 - self.progresso) ** 3
        raio = self.raio_inicial + (self.raio_final - self.raio_inicial) * p
        intensidade = 1 - self.progresso
        largura = max(1, int(3 * intensidade + 0.5))
        centro = (int(self.x), int(self.y))
        pygame.draw.circle(tela, grafico.misturar(self.cor, intensidade * 0.3), centro, int(raio) + 2, largura + 2)
        pygame.draw.circle(tela, grafico.misturar(self.cor, intensidade), centro, int(raio), largura)
