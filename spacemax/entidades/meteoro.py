"""Asteroides que se quebram em pedacos menores ao serem atingidos."""

import math
import random

from .. import grafico
from ..config import (
    ALTURA,
    ASTEROIDE_GRANDE,
    ASTEROIDE_PEQUENO,
    COR_ASTEROIDE,
    DADOS_ASTEROIDE,
    FRAGMENTOS_POR_QUEBRA,
    LARGURA,
)
from .base import EntidadeColidivel


class Meteoro(EntidadeColidivel):
    def __init__(
        self,
        x: float,
        y: float,
        tamanho: int = ASTEROIDE_GRANDE,
        velocidade: float = 1.0,
        angulo: float | None = None,
    ):
        raio, pontos, multiplicador = DADOS_ASTEROIDE[tamanho]
        if angulo is None:
            angulo = random.uniform(0, 360)
        rad = math.radians(angulo)
        veloc = velocidade * multiplicador * random.uniform(0.8, 1.2)
        super().__init__(x, y, raio, math.sin(rad) * veloc, -math.cos(rad) * veloc)

        self.tamanho: int = tamanho
        self.pontos: int = pontos
        self.velocidade_base: float = velocidade
        self.angulo: float = random.uniform(0, 360)
        self.velocidade_angular: float = random.uniform(-1.2, 1.2) * multiplicador

        # contorno irregular: o raio varia em cada vertice
        vertices = random.randint(9, 12)
        self.forma: list[tuple[float, float]] = []
        for i in range(vertices):
            ang = (2 * math.pi / vertices) * i
            r = raio * random.uniform(0.72, 1.0)
            self.forma.append((math.cos(ang) * r, math.sin(ang) * r))

    @classmethod
    def na_borda(cls, velocidade: float) -> "Meteoro":
        """Cria um asteroide grande entrando por uma borda aleatoria da tela."""
        raio = DADOS_ASTEROIDE[ASTEROIDE_GRANDE][0]
        borda = random.choice(["topo", "base", "esquerda", "direita"])
        if borda == "topo":
            x, y = random.uniform(0, LARGURA), -raio
        elif borda == "base":
            x, y = random.uniform(0, LARGURA), ALTURA + raio
        elif borda == "esquerda":
            x, y = -raio, random.uniform(0, ALTURA)
        else:
            x, y = LARGURA + raio, random.uniform(0, ALTURA)

        # aponta aproximadamente para o centro, com desvio aleatorio
        alvo = math.degrees(math.atan2(LARGURA / 2 - x, -(ALTURA / 2 - y)))
        return cls(x, y, ASTEROIDE_GRANDE, velocidade, alvo + random.uniform(-40, 40))

    def quebrar(self) -> list["Meteoro"]:
        """Retorna os fragmentos menores (lista vazia se ja for o menor)."""
        if self.tamanho == ASTEROIDE_PEQUENO:
            return []
        return [
            Meteoro(self.x, self.y, self.tamanho - 1, self.velocidade_base)
            for _ in range(FRAGMENTOS_POR_QUEBRA)
        ]

    def atualizar(self):
        self.mover()
        self.angulo += self.velocidade_angular

    def desenhar(self, tela):
        pontos = grafico.rotacionar(self.forma, self.angulo, self.x, self.y)
        grafico.contorno(tela, COR_ASTEROIDE, pontos)
