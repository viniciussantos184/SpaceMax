"""Personagem principal: nave que gira 360 graus e acelera com inercia."""

import math
import random

import pygame

from .. import grafico
from ..config import (
    ACELERACAO_NAVE,
    ACELERACAO_ROTACAO,
    ALTURA,
    AMORTECIMENTO_ROTACAO,
    ATRITO_NAVE,
    COOLDOWN_DASH,
    COOLDOWN_TIRO,
    COR_CHAMA,
    COR_ITEM,
    COR_PRIMARIA,
    DURACAO_DASH,
    FREIO_NAVE,
    IMPULSO_DASH,
    LARGURA,
    RAMPA_PROPULSOR,
    ROTACAO_MAX_NAVE,
    VELOCIDADE_MAX_DASH,
    VELOCIDADE_MAX_NAVE,
)
from .base import EntidadeColidivel
from .particula import Particula
from .tiro import Tiro

# contorno da nave em coordenadas locais (nariz apontando para cima)
CASCO = [(0, -20), (5, -6), (14, 12), (5, 8), (-5, 8), (-14, 12), (-5, -6)]
DETALHES = [((0, -12), (0, -3)), ((5, -6), (5, 8)), ((-5, -6), (-5, 8))]
PONTA_NARIZ = (0, -20)
BOCAL_MOTOR = (0, 10)
# jatos laterais (RCS) perto do nariz: disparam para o lado oposto ao giro
JATO_ESQUERDO = ((-4, -9), (-11, -11))
JATO_DIREITO = ((4, -9), (11, -11))
COR_JATO = (200, 235, 255)


class Nave(EntidadeColidivel):
    RAIO = 13

    def __init__(self):
        super().__init__(LARGURA / 2, ALTURA / 2, self.RAIO)
        self.angulo: float = 0.0  # graus; 0 = apontando para cima
        self.velocidade_angular: float = 0.0
        self.potencia: float = 0.0  # 0..1: rampa do motor principal
        self.propulsor_ligado: bool = False
        self.cooldown_atual: int = 0
        self.cooldown_dash: int = 0
        self.tempo_dash: int = 0
        self.tempo_escudo: int = 0  # escudo do item
        self.tempo_invencivel: int = 0  # piscando apos ser atingida
        self.frame: int = 0

    # ----------------------------------------------------------------- controle
    def girar(self, direcao):
        """direcao: -1 esquerda, 1 direita, 0 soltou (o giro freia sozinho)."""
        if direcao:
            self.velocidade_angular += direcao * ACELERACAO_ROTACAO
            limite = ROTACAO_MAX_NAVE
            self.velocidade_angular = max(-limite, min(limite, self.velocidade_angular))
        else:
            self.velocidade_angular *= AMORTECIMENTO_ROTACAO
            if abs(self.velocidade_angular) < 0.05:
                self.velocidade_angular = 0.0

    def acelerar(self):
        self.propulsor_ligado = True

    def frear(self):
        self.vx *= FREIO_NAVE
        self.vy *= FREIO_NAVE

    def direcao(self):
        rad = math.radians(self.angulo)
        return math.sin(rad), -math.cos(rad)

    def pode_dash(self):
        return self.cooldown_dash <= 0

    def dash(self):
        """Impulso instantaneo na direcao do nariz (recarrega em COOLDOWN_DASH)."""
        dx, dy = self.direcao()
        self.vx += dx * IMPULSO_DASH
        self.vy += dy * IMPULSO_DASH
        self.cooldown_dash = COOLDOWN_DASH
        self.tempo_dash = DURACAO_DASH

    @property
    def carga_dash(self) -> float:
        """0 = acabou de usar, 1 = pronto."""
        return 1 - self.cooldown_dash / COOLDOWN_DASH

    def pode_atirar(self):
        return self.cooldown_atual <= 0

    def atirar(self):
        self.cooldown_atual = COOLDOWN_TIRO
        (bico_x, bico_y), = grafico.rotacionar([PONTA_NARIZ], self.angulo, self.x, self.y)
        return Tiro(bico_x, bico_y, self.angulo, self.vx, self.vy)

    # ---------------------------------------------------------------- protecao
    @property
    def protegida(self) -> bool:
        return self.tempo_escudo > 0 or self.tempo_invencivel > 0

    def ativar_escudo(self, frames):
        self.tempo_escudo = frames

    def reaparecer(self, frames_invencivel):
        self.x, self.y = LARGURA / 2, ALTURA / 2
        self.vx = self.vy = 0.0
        self.angulo = 0.0
        self.velocidade_angular = 0.0
        self.potencia = 0.0
        self.tempo_invencivel = frames_invencivel

    # ------------------------------------------------------------------- frame
    def atualizar(self):
        self.frame += 1
        self.angulo = (self.angulo + self.velocidade_angular) % 360

        # o motor ganha potencia aos poucos: da sensacao de peso sem ficar lento
        if self.propulsor_ligado:
            self.potencia = min(1.0, self.potencia + RAMPA_PROPULSOR)
            dx, dy = self.direcao()
            empuxo = ACELERACAO_NAVE * (0.45 + 0.55 * self.potencia)
            self.vx += dx * empuxo
            self.vy += dy * empuxo
        else:
            self.potencia = max(0.0, self.potencia - RAMPA_PROPULSOR * 2)
        self.propulsor_ligado = False  # o controle religa a cada frame

        self.vx *= ATRITO_NAVE
        self.vy *= ATRITO_NAVE
        limite = VELOCIDADE_MAX_DASH if self.tempo_dash > 0 else VELOCIDADE_MAX_NAVE
        velocidade = math.hypot(self.vx, self.vy)
        if velocidade > limite:
            # apos o impulso, volta ao limite normal suavemente
            fator = max(limite / velocidade, 0.97)
            self.vx *= fator
            self.vy *= fator
        self.mover()

        for atributo in ("cooldown_atual", "cooldown_dash", "tempo_dash",
                         "tempo_escudo", "tempo_invencivel"):
            valor = getattr(self, atributo)
            if valor > 0:
                setattr(self, atributo, valor - 1)

    def emitir_rastro(self) -> list[Particula]:
        """Particulas de exaustao do motor (e uma rajada maior durante o impulso)."""
        if self.potencia <= 0.05 and self.tempo_dash <= 0:
            return []
        (bocal_x, bocal_y), = grafico.rotacionar([BOCAL_MOTOR], self.angulo, self.x, self.y)
        dx, dy = self.direcao()
        quantidade = 5 if self.tempo_dash > 0 else (1 if self.potencia < 0.6 else 2)
        cor = COR_PRIMARIA if self.tempo_dash > 0 else COR_CHAMA

        rastro = []
        for _ in range(quantidade):
            espalhamento = random.uniform(-0.35, 0.35)
            velocidade = random.uniform(2.0, 3.5) * max(self.potencia, 0.6)
            # sai para tras do motor, somada a velocidade da nave
            vx = -dx * velocidade + -dy * espalhamento + self.vx * 0.5
            vy = -dy * velocidade + dx * espalhamento + self.vy * 0.5
            rastro.append(Particula(bocal_x, bocal_y, cor, vx, vy, random.randint(10, 20)))
        return rastro

    def desenhar(self, tela):
        # pisca enquanto esta invencivel apos ser atingida
        if self.tempo_invencivel > 0 and (self.frame // 5) % 2 == 0:
            return

        if self.potencia > 0:
            self.desenhar_chama(tela)
        self.desenhar_jatos_laterais(tela)

        if self.tempo_dash > 0:
            # "rastro fantasma" durante o impulso
            for passo in (3, 2, 1):
                fantasma = grafico.rotacionar(
                    CASCO, self.angulo, self.x - self.vx * passo * 1.5, self.y - self.vy * passo * 1.5
                )
                pygame.draw.aalines(tela, grafico.misturar(COR_PRIMARIA, 0.12 * (4 - passo)), True, fantasma)

        grafico.contorno(tela, COR_PRIMARIA, grafico.rotacionar(CASCO, self.angulo, self.x, self.y))
        for inicio, fim in DETALHES:
            a, b = grafico.rotacionar([inicio, fim], self.angulo, self.x, self.y)
            pygame.draw.aaline(tela, grafico.misturar(COR_PRIMARIA, 0.55), a, b)

        if self.tempo_escudo > 0:
            self.desenhar_escudo(tela)

    def desenhar_chama(self, tela):
        comprimento = (6 + 12 * self.potencia) * random.uniform(0.85, 1.15)
        largura = 3 + 1.5 * self.potencia
        chama = [(-largura, 9), (0, 9 + comprimento), (largura, 9)]
        pontos = grafico.rotacionar(chama, self.angulo, self.x, self.y)
        pygame.draw.lines(tela, grafico.misturar(COR_CHAMA, 0.3), False, pontos, 4)
        pygame.draw.aalines(tela, COR_CHAMA, False, pontos)

    def desenhar_jatos_laterais(self, tela):
        if abs(self.velocidade_angular) < 1.0:
            return
        # girando para a direita, o jato da esquerda empurra o nariz
        inicio, fim = JATO_ESQUERDO if self.velocidade_angular > 0 else JATO_DIREITO
        intensidade = min(1.0, abs(self.velocidade_angular) / ROTACAO_MAX_NAVE)
        fim = (inicio[0] + (fim[0] - inicio[0]) * intensidade * random.uniform(0.7, 1.0), fim[1])
        a, b = grafico.rotacionar([inicio, fim], self.angulo, self.x, self.y)
        pygame.draw.aaline(tela, grafico.misturar(COR_JATO, intensidade), a, b)

    def desenhar_escudo(self, tela):
        # pisca nos ultimos 1,5 s para avisar que vai acabar
        if self.tempo_escudo < 90 and (self.frame // 6) % 2 == 0:
            return
        raio = 26
        rect = pygame.Rect(0, 0, raio * 2, raio * 2)
        rect.center = (int(self.x), int(self.y))
        giro = math.radians(self.frame * 3)
        # tres arcos girando: visual de "campo de forca" tecnico
        for i in range(3):
            inicio = giro + i * (2 * math.pi / 3)
            pygame.draw.arc(tela, COR_ITEM, rect, inicio, inicio + math.radians(70), 2)
        grafico.circulo(tela, grafico.misturar(COR_ITEM, 0.25), (self.x, self.y), raio + 4)
