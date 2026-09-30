"""Projeteis disparados pelos chefes (incluindo minas que explodem em estilhacos)."""

import math

from .. import grafico
from ..config import ALTURA, COR_PERIGO, LARGURA
from .base import EntidadeColidivel

LOSANGO = [(0, -6), (3, 0), (0, 6), (-3, 0)]
QUADRADO_MINA = [(-6, -6), (6, -6), (6, 6), (-6, 6)]
VELOCIDADE_ESTILHACO = 2.8
MARGEM_SAIDA = 30
VIDA_MAXIMA = 600  # frames


class ProjetilChefe(EntidadeColidivel):
    RAIO = 4
    RAIO_MINA = 7

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        cor: tuple[int, int, int] = COR_PERIGO,
        detonacao: int = 0,
        fragmentos: int = 0,
    ):
        """Com `detonacao` > 0 vira uma mina: apos esse numero de frames se parte em `fragmentos`."""
        super().__init__(x, y, self.RAIO_MINA if detonacao else self.RAIO, vx, vy)
        self.cor: tuple[int, int, int] = cor
        self.detonacao: int = detonacao
        self.fragmentos: int = fragmentos
        self.tempo: int = 0

    def atualizar(self):
        # diferente do resto, nao atravessa as bordas: sai da tela e some
        self.x += self.vx
        self.y += self.vy
        self.tempo += 1

    def fora_da_tela(self):
        return not (
            -MARGEM_SAIDA < self.x < LARGURA + MARGEM_SAIDA
            and -MARGEM_SAIDA < self.y < ALTURA + MARGEM_SAIDA
        )

    def expirou(self):
        if self.detonacao and self.tempo >= self.detonacao:
            return True
        return self.fora_da_tela() or self.tempo >= VIDA_MAXIMA

    def detonar(self) -> list["ProjetilChefe"]:
        """Estilhacos da mina, so no frame exato da detonacao (lista vazia nos demais)."""
        if not self.detonacao or self.tempo != self.detonacao:
            return []
        estilhacos = []
        for i in range(self.fragmentos):
            angulo = 2 * math.pi * i / self.fragmentos
            vx = math.cos(angulo) * VELOCIDADE_ESTILHACO
            vy = math.sin(angulo) * VELOCIDADE_ESTILHACO
            estilhacos.append(ProjetilChefe(self.x, self.y, vx, vy, self.cor))
        return estilhacos

    def desenhar(self, tela):
        if self.detonacao:
            self.desenhar_mina(tela)
            return
        # losango alongado apontando na direcao do movimento
        angulo = math.degrees(math.atan2(self.vx, -self.vy))
        grafico.contorno(tela, self.cor, grafico.rotacionar(LOSANGO, angulo, self.x, self.y))

    def desenhar_mina(self, tela):
        restante = self.detonacao - self.tempo
        # pisca em branco perto de explodir
        cor = self.cor
        if restante < 25 and (self.tempo // 3) % 2 == 0:
            cor = (255, 255, 255)
        pontos = grafico.rotacionar(QUADRADO_MINA, self.tempo * 4, self.x, self.y)
        grafico.contorno(tela, cor, pontos)
        grafico.circulo(tela, grafico.misturar(cor, 0.35), (self.x, self.y), 11)
