"""Item especial (escudo temporario) que flutua pela tela por alguns segundos."""

import math
import random

from .. import grafico
from ..config import ALTURA, COR_ITEM, FPS, LARGURA
from .base import EntidadeColidivel

LOSANGO = [(0, -11), (11, 0), (0, 11), (-11, 0)]
LOSANGO_INTERNO = [(0, -5), (5, 0), (0, 5), (-5, 0)]


class Item(EntidadeColidivel):
    RAIO = 12
    DURACAO = 9 * FPS

    def __init__(self):
        angulo = random.uniform(0, 2 * math.pi)
        super().__init__(
            random.uniform(80, LARGURA - 80),
            random.uniform(80, ALTURA - 80),
            self.RAIO,
            math.cos(angulo) * 0.6,
            math.sin(angulo) * 0.6,
        )
        self.coletado: bool = False
        self.vida: int = self.DURACAO
        self.angulo: float = 0.0

    def atualizar(self):
        self.mover()
        self.angulo += 2
        self.vida -= 1

    def expirou(self):
        return self.vida <= 0

    def desenhar(self, tela):
        # pisca nos ultimos 2 s antes de sumir
        if self.vida < 2 * FPS and (self.vida // 6) % 2 == 0:
            return
        pulso = 0.75 + 0.25 * math.sin(self.vida * 0.15)
        grafico.contorno(tela, COR_ITEM, grafico.rotacionar(LOSANGO, self.angulo, self.x, self.y))
        grafico.contorno(
            tela,
            grafico.misturar(COR_ITEM, pulso),
            grafico.rotacionar(LOSANGO_INTERNO, -self.angulo, self.x, self.y),
            brilho=False,
        )
