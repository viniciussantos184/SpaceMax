"""Projeteis disparados pelos chefes (incluindo minas que explodem em estilhacos)."""

import math

from .. import grafico
from ..config import ALTURA, COR_PERIGO, LARGURA
from .base import EntidadeColidivel

LOSANGO = [(0, -6), (3, 0), (0, 6), (-3, 0)]
DRONE = [(0, -8), (7, -4), (7, 4), (0, 8), (-7, 4), (-7, -4)]
MISSIL = [(0, -9), (4, 2), (4, 8), (-4, 8), (-4, 2)]
QUADRADO_MINA = [(-6, -6), (6, -6), (6, 6), (-6, 6)]
VELOCIDADE_ESTILHACO = 2.8
MARGEM_SAIDA = 30
VIDA_MAXIMA = 600  # frames
GIRO_GUIADO = 2.2  # graus por frame que um missil teleguiado consegue virar


class ProjetilChefe(EntidadeColidivel):
    RAIO = 4
    RAIO_MINA = 7
    RAIO_DRONE = 8

    def __init__(
        self,
        x: float,
        y: float,
        vx: float,
        vy: float,
        cor: tuple[int, int, int] = COR_PERIGO,
        detonacao: int = 0,
        fragmentos: int = 0,
        guiado: int = 0,
        destrutivel: bool = False,
    ):
        """Com `detonacao` > 0 vira uma mina: apos esse numero de frames se parte em `fragmentos`.

        Com `guiado` > 0 vira um missil que persegue `alvo` durante esse numero de frames.
        Com `destrutivel` vira um drone que os tiros da nave conseguem abater."""
        raio = self.RAIO_MINA if detonacao else self.RAIO_DRONE if destrutivel else self.RAIO
        super().__init__(x, y, raio, vx, vy)
        self.cor: tuple[int, int, int] = cor
        self.detonacao: int = detonacao
        self.fragmentos: int = fragmentos
        self.guiado: int = guiado
        self.destrutivel: bool = destrutivel
        self.abatido: bool = False  # removido por colisao (o chefe que lancou pode contar)
        self.alvo: tuple[float, float] | None = None  # o jogo atualiza com a posicao da nave
        self.tempo: int = 0

    def atualizar(self):
        if self.tempo < self.guiado and self.alvo:
            self.virar_para_alvo()
        # diferente do resto, nao atravessa as bordas: sai da tela e some
        self.x += self.vx
        self.y += self.vy
        self.tempo += 1

    def virar_para_alvo(self):
        atual = math.atan2(self.vy, self.vx)
        desejado = math.atan2(self.alvo[1] - self.y, self.alvo[0] - self.x)
        diferenca = (desejado - atual + math.pi) % (2 * math.pi) - math.pi
        limite = math.radians(GIRO_GUIADO)
        novo = atual + max(-limite, min(limite, diferenca))
        velocidade = math.hypot(self.vx, self.vy)
        self.vx, self.vy = math.cos(novo) * velocidade, math.sin(novo) * velocidade

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
        if self.destrutivel:
            self.desenhar_drone(tela)
            return
        if self.guiado:
            self.desenhar_missil(tela, angulo)
            return
        grafico.contorno(tela, self.cor, grafico.rotacionar(LOSANGO, angulo, self.x, self.y))

    def desenhar_drone(self, tela):
        pontos = grafico.rotacionar(DRONE, self.tempo * 6, self.x, self.y)
        grafico.contorno(tela, self.cor, pontos)
        grafico.circulo(tela, (255, 255, 255), (self.x, self.y), 2, 0)

    def desenhar_missil(self, tela, angulo):
        grafico.contorno(tela, self.cor, grafico.rotacionar(MISSIL, angulo, self.x, self.y))
        # chama na traseira enquanto ainda esta perseguindo
        if self.tempo < self.guiado and (self.tempo // 3) % 2 == 0:
            (cx, cy), = grafico.rotacionar([(0, 12)], angulo, self.x, self.y)
            grafico.circulo(tela, (255, 230, 200), (cx, cy), 2, 0)

    def desenhar_mina(self, tela):
        restante = self.detonacao - self.tempo
        # pisca em branco perto de explodir
        cor = self.cor
        if restante < 25 and (self.tempo // 3) % 2 == 0:
            cor = (255, 255, 255)
        pontos = grafico.rotacionar(QUADRADO_MINA, self.tempo * 4, self.x, self.y)
        grafico.contorno(tela, cor, pontos)
        grafico.circulo(tela, grafico.misturar(cor, 0.35), (self.x, self.y), 11)
