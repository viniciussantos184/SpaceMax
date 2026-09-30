"""
Chefes: um inimigo grande a cada NIVEIS_POR_CHEFE niveis.

Cada chefe tem forma, cor e padrao de ataque proprios. A ordem segue a lista
CHEFES; depois do ultimo ela recomeca com os chefes mais fortes (`ciclo`).
"""

import math
import random

import pygame

from .. import grafico
from ..config import ALTURA, FPS, LARGURA
from .base import EntidadeColidivel
from .projetil import ProjetilChefe

DURACAO_ENTRADA = 2 * FPS
POSICAO_INICIAL_Y = 160  # altura em que o chefe para ao terminar a entrada

# ajuste geral de dificuldade (vale para todos os chefes)
FATOR_VIDA = 0.45  # fracao da VIDA_BASE de cada chefe
FATOR_INTERVALO = 1.7  # multiplica o intervalo entre ataques (maior = ataca menos)
FATOR_VELOCIDADE = 0.7  # multiplica a velocidade dos projeteis


def _poligono_regular(lados, raio, giro=0.0):
    return [
        (math.cos(math.radians(giro + 360 * i / lados)) * raio,
         math.sin(math.radians(giro + 360 * i / lados)) * raio)
        for i in range(lados)
    ]


class Chefe(EntidadeColidivel):
    """Base dos chefes: entrada pelo topo, vida, clarao ao levar dano e fase furiosa."""

    NOME = "CHEFE"
    COR = (255, 84, 112)
    RAIO = 36
    VIDA_BASE = 40

    def __init__(self, ciclo: int = 0):
        super().__init__(LARGURA / 2, -self.RAIO * 2, self.RAIO)
        self.ciclo: int = ciclo  # quantas vezes a lista de chefes ja deu a volta
        self.vida_max: int = int(self.VIDA_BASE * FATOR_VIDA * (1 + 0.35 * ciclo))
        self.vida: int = self.vida_max
        self.tempo: int = 0
        self.tempo_entrada: int = DURACAO_ENTRADA
        self.clarao: int = 0
        self.angulo: float = 0.0
        self.alvo: tuple[float, float] = (LARGURA / 2, ALTURA / 2)
        self.recargas: dict[str, int] = {}

    # ------------------------------------------------------------------ estado
    @property
    def entrando(self) -> bool:
        return self.tempo_entrada > 0

    @property
    def furioso(self) -> bool:
        """Abaixo de metade da vida o chefe ataca mais rapido."""
        return self.vida <= self.vida_max / 2

    @property
    def tempo_ativo(self) -> int:
        """Frames desde o fim da entrada (0 no primeiro frame de luta)."""
        return max(0, self.tempo - DURACAO_ENTRADA - 1)

    @property
    def fracao_barra(self) -> float:
        """Vida para a barra do HUD; durante a entrada a barra 'carrega'."""
        if self.entrando:
            return 1 - self.tempo_entrada / DURACAO_ENTRADA
        return self.vida / self.vida_max

    def morto(self):
        return self.vida <= 0

    def definir_alvo(self, x, y):
        self.alvo = (x, y)

    def receber_dano(self, quantidade=1) -> bool:
        if self.entrando or self.morto():
            return False
        self.vida = max(0, self.vida - quantidade)
        self.clarao = 6
        return True

    def atinge(self, entidade) -> bool:
        """Colisao com o corpo do chefe (ignorada durante a entrada)."""
        return not self.entrando and self.colide_com(entidade)

    def bloqueia(self, tiro) -> bool:
        """Partes que absorvem tiros sem levar dano (escudos, satelites...)."""
        return False

    # ------------------------------------------------------------------- frame
    def atualizar(self):
        self.tempo += 1
        if self.clarao > 0:
            self.clarao -= 1
        if self.entrando:
            self.tempo_entrada -= 1
            p = 1 - self.tempo_entrada / DURACAO_ENTRADA
            p = 1 - (1 - p) ** 3  # desce rapido e freia ao chegar
            self.x = LARGURA / 2
            self.y = -self.raio * 2 + (POSICAO_INICIAL_Y + self.raio * 2) * p
            return
        self.mover_padrao()

    def atacar(self) -> list[ProjetilChefe]:
        if self.entrando:
            return []
        return self.padrao_ataque()

    def mover_padrao(self):
        """Movimento proprio de cada chefe (chamado apos a entrada)."""

    def padrao_ataque(self) -> list[ProjetilChefe]:
        return []

    # ------------------------------------------------------------ utilitarios
    def ritmo(self, frames):
        """Intervalo entre ataques: menor na fase furiosa e a cada volta do ciclo."""
        fator = FATOR_INTERVALO * (0.8 if self.furioso else 1.0) * 0.9 ** self.ciclo
        return max(4, int(frames * fator))

    def pronto(self, nome, intervalo) -> bool:
        """Contador de recarga por ataque; True no frame em que o ataque dispara."""
        restante = self.recargas.get(nome, intervalo) - 1
        if restante <= 0:
            self.recargas[nome] = self.ritmo(intervalo)
            return True
        self.recargas[nome] = restante
        return False

    def carga(self, nome, antecedencia) -> float:
        """0..1 nos ultimos `antecedencia` frames antes do ataque (para avisos visuais)."""
        restante = self.recargas.get(nome, antecedencia + 1)
        return max(0.0, 1 - restante / antecedencia)

    def angulo_ate_alvo(self, origem=None) -> float:
        x, y = origem or (self.x, self.y)
        return math.degrees(math.atan2(self.alvo[1] - y, self.alvo[0] - x))

    def disparar(self, angulo, velocidade, origem=None, **extra) -> ProjetilChefe:
        """Projetil em `angulo` (graus, 0 = direita, sentido horario na tela)."""
        rad = math.radians(angulo)
        x, y = origem or (self.x, self.y)
        velocidade *= FATOR_VELOCIDADE * (1 + 0.1 * self.ciclo)
        return ProjetilChefe(x, y, math.cos(rad) * velocidade, math.sin(rad) * velocidade, self.COR, **extra)

    def rajada_circular(self, quantidade, velocidade, deslocamento=0.0):
        return [self.disparar(deslocamento + 360 * i / quantidade, velocidade) for i in range(quantidade)]

    # ----------------------------------------------------------------- desenho
    def cor_atual(self, intensidade=1.0):
        cor = self.COR
        if self.clarao > 0:
            brilho = self.clarao / 6
            cor = tuple(int(c + (255 - c) * brilho) for c in cor)
        if self.entrando:
            intensidade *= 1 - self.tempo_entrada / DURACAO_ENTRADA
        return grafico.misturar(cor, intensidade)

    def desenhar_marcadores(self, tela):
        """Cantoneiras de 'alvo travado' em volta do chefe; piscam na fase furiosa."""
        intensidade = 0.35
        if self.furioso and (self.tempo // 8) % 2 == 0:
            intensidade = 0.8
        cor = self.cor_atual(intensidade)
        d, t = self.raio + 14, 8
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = self.x + sx * d, self.y + sy * d
                pygame.draw.aaline(tela, cor, (cx, cy), (cx - sx * t, cy))
                pygame.draw.aaline(tela, cor, (cx, cy), (cx, cy - sy * t))


# ---------------------------------------------------------------------------
# 01 · SENTINELA: hexagono com anel segmentado; rajadas em circulo
# ---------------------------------------------------------------------------
class Sentinela(Chefe):
    NOME = "SENTINELA"
    COR = (255, 84, 112)
    RAIO = 36
    VIDA_BASE = 40
    NUCLEO = _poligono_regular(6, 22)

    def __init__(self, ciclo: int = 0):
        super().__init__(ciclo)
        self.deslocamento_rajada: float = 0.0

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.012) * 300
        self.y = POSICAO_INICIAL_Y + math.sin(t * 0.024) * 30
        self.angulo += 1.5 if self.furioso else 0.6

    def padrao_ataque(self):
        if not self.pronto("rajada", 80):
            return []
        # cada rajada sai girada para os vaos nao ficarem sempre no mesmo lugar
        self.deslocamento_rajada += 15
        quantidade = 16 if self.furioso else 12
        return self.rajada_circular(quantidade, 3.2, self.deslocamento_rajada)

    def desenhar(self, tela):
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.NUCLEO, self.angulo, self.x, self.y))

        # anel externo: seis segmentos com vao, girando ao contrario do nucleo
        giro = -self.angulo * 1.6
        for i in range(6):
            a = math.radians(giro + i * 60 + 10)
            b = math.radians(giro + i * 60 + 50)
            grafico.linha(
                tela, cor,
                (self.x + math.cos(a) * 36, self.y + math.sin(a) * 36),
                (self.x + math.cos(b) * 36, self.y + math.sin(b) * 36),
            )

        # aviso da rajada: marcas acendem em volta pouco antes do disparo
        carga = self.carga("rajada", 24)
        if carga > 0 and not self.entrando:
            cor_marca = grafico.misturar(self.COR, carga)
            for i in range(12):
                a = math.radians(self.deslocamento_rajada + 15 + i * 30)
                inicio = (self.x + math.cos(a) * 44, self.y + math.sin(a) * 44)
                fim = (self.x + math.cos(a) * 50, self.y + math.sin(a) * 50)
                pygame.draw.aaline(tela, cor_marca, inicio, fim)

        # "olho" que acompanha a nave
        dx, dy = self.alvo[0] - self.x, self.alvo[1] - self.y
        distancia = max(1.0, math.hypot(dx, dy))
        grafico.circulo(tela, cor, (self.x + dx / distancia * 7, self.y + dy / distancia * 7), 4)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 02 · ARPAO: ponta de flecha que persegue a mira; leque de tiros mirados
# ---------------------------------------------------------------------------
class Arpao(Chefe):
    NOME = "ARPAO"
    COR = (180, 130, 255)
    RAIO = 28
    VIDA_BASE = 50
    FORMA = [(0, -38), (22, 16), (9, 9), (0, 24), (-9, 9), (-22, 16)]
    DETALHE = [(0, -24), (0, 8)]
    PONTA = (0, -38)

    def __init__(self, ciclo: int = 0):
        super().__init__(ciclo)
        self.angulo = 180.0  # entra com a ponta para baixo (0 = cima)
        self.destino: tuple[float, float] = (LARGURA / 2, POSICAO_INICIAL_Y)

    def mover_padrao(self):
        if self.pronto("destino", 150):
            self.destino = (random.uniform(140, LARGURA - 140), random.uniform(90, ALTURA * 0.55))
        suavidade = 0.035 if self.furioso else 0.022
        self.x += (self.destino[0] - self.x) * suavidade
        self.y += (self.destino[1] - self.y) * suavidade

        # gira a ponta na direcao da nave com velocidade limitada
        alvo = math.degrees(math.atan2(self.alvo[0] - self.x, -(self.alvo[1] - self.y)))
        diferenca = (alvo - self.angulo + 180) % 360 - 180
        self.angulo += max(-3.0, min(3.0, diferenca))

    def padrao_ataque(self):
        if not self.pronto("leque", 60):
            return []
        quantidade = 5 if self.furioso else 3
        (px, py), = grafico.rotacionar([self.PONTA], self.angulo, self.x, self.y)
        centro = self.angulo - 90  # converte "0 = cima" para o angulo dos projeteis
        return [
            self.disparar(centro + (i - (quantidade - 1) / 2) * 13, 4.6, origem=(px, py))
            for i in range(quantidade)
        ]

    def desenhar(self, tela):
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.FORMA, self.angulo, self.x, self.y))
        a, b = grafico.rotacionar(self.DETALHE, self.angulo, self.x, self.y)
        pygame.draw.aaline(tela, self.cor_atual(0.55), a, b)

        # a ponta acende antes do leque
        carga = self.carga("leque", 20)
        if carga > 0 and not self.entrando:
            (px, py), = grafico.rotacionar([self.PONTA], self.angulo, self.x, self.y)
            grafico.circulo(tela, grafico.misturar(self.COR, carga), (px, py), 2 + 4 * carga)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 03 · ORBITA: nucleo em losango com satelites que bloqueiam tiros; espiral
# ---------------------------------------------------------------------------
class Orbita(Chefe):
    NOME = "ORBITA"
    COR = (110, 255, 170)
    RAIO = 24
    VIDA_BASE = 55
    RAIO_ORBITA = 78
    RAIO_SATELITE = 11
    SATELITES = 3
    LOSANGO = [(0, -24), (24, 0), (0, 24), (-24, 0)]
    LOSANGO_INTERNO = [(0, -11), (11, 0), (0, 11), (-11, 0)]
    QUADRADO = [(-7, -7), (7, -7), (7, 7), (-7, 7)]

    def __init__(self, ciclo: int = 0):
        super().__init__(ciclo)
        self.espiral: float = 0.0
        self.giro_orbita: float = 0.0

    def satelites(self) -> list[tuple[float, float]]:
        return [
            (self.x + math.cos(a) * self.RAIO_ORBITA, self.y + math.sin(a) * self.RAIO_ORBITA)
            for a in (math.radians(self.giro_orbita + 360 * i / self.SATELITES) for i in range(self.SATELITES))
        ]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.008) * 220
        self.y = POSICAO_INICIAL_Y + math.sin(t * 0.017) * 45
        self.giro_orbita += 2.0 if self.furioso else 1.1
        self.angulo += 0.8

    def bloqueia(self, tiro) -> bool:
        if self.entrando:
            return False
        return any(
            math.hypot(tiro.x - sx, tiro.y - sy) < self.RAIO_SATELITE + tiro.raio
            for sx, sy in self.satelites()
        )

    def atinge(self, entidade) -> bool:
        if self.entrando:
            return False
        if self.colide_com(entidade):
            return True
        return any(
            math.hypot(entidade.x - sx, entidade.y - sy) < self.RAIO_SATELITE + entidade.raio
            for sx, sy in self.satelites()
        )

    def padrao_ataque(self):
        novos = []
        # espiral em rajadas de 3 s com 1 s de pausa para respirar
        if (self.tempo_ativo // FPS) % 4 != 3 and self.pronto("espiral", 9):
            bracos = 2 if self.furioso else 1
            for b in range(bracos):
                novos.append(self.disparar(self.espiral + b * 180, 2.6))
            self.espiral += 17
        if self.pronto("satelites", 110):
            for sx, sy in self.satelites():
                novos.append(self.disparar(self.angulo_ate_alvo((sx, sy)), 3.4, origem=(sx, sy)))
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        fraca = self.cor_atual(0.3)

        # orbita pontilhada
        for i in range(24):
            a = math.radians(i * 15 + self.giro_orbita * 0.3)
            ponto = (self.x + math.cos(a) * self.RAIO_ORBITA, self.y + math.sin(a) * self.RAIO_ORBITA)
            grafico.circulo(tela, fraca, ponto, 1, 0)

        grafico.contorno(tela, cor, grafico.rotacionar(self.LOSANGO, self.angulo, self.x, self.y))
        grafico.contorno(
            tela, self.cor_atual(0.6),
            grafico.rotacionar(self.LOSANGO_INTERNO, -self.angulo * 2, self.x, self.y), brilho=False,
        )

        # satelites ligados ao nucleo por um "cabo" fino
        for sx, sy in self.satelites():
            pygame.draw.aaline(tela, fraca, (self.x, self.y), (sx, sy))
            grafico.contorno(tela, cor, grafico.rotacionar(self.QUADRADO, self.angulo * 3, sx, sy))
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 04 · PRISMA: quadrado que mira, investe contra a nave e solta um anel
# ---------------------------------------------------------------------------
class Prisma(Chefe):
    NOME = "PRISMA"
    COR = (255, 120, 220)
    RAIO = 30
    VIDA_BASE = 60
    EXTERNO = [(-30, -30), (30, -30), (30, 30), (-30, 30)]
    INTERNO = [(-15, -15), (15, -15), (15, 15), (-15, 15)]
    MIRANDO, INVESTIDA, RECUPERANDO = range(3)
    TRAVA_MIRA = 25  # ultimos frames da mira: o alvo congela (da para desviar)

    def __init__(self, ciclo: int = 0):
        super().__init__(ciclo)
        self.fase: int = self.RECUPERANDO
        self.tempo_fase: int = self.ritmo(60)
        self.mira: tuple[float, float] = self.alvo
        self.rastro: list[tuple[float, float]] = []
        self.anel_pendente: bool = False

    def mover_padrao(self):
        self.tempo_fase -= 1

        if self.fase == self.MIRANDO:
            if self.tempo_fase > self.TRAVA_MIRA:
                self.mira = self.alvo
            self.angulo += 6
            if self.tempo_fase <= 0:
                dx, dy = self.mira[0] - self.x, self.mira[1] - self.y
                distancia = max(1.0, math.hypot(dx, dy))
                velocidade = 8.0 + 0.7 * self.ciclo
                self.vx, self.vy = dx / distancia * velocidade, dy / distancia * velocidade
                self.fase, self.tempo_fase = self.INVESTIDA, 45

        elif self.fase == self.INVESTIDA:
            self.angulo += 12
            self.rastro = (self.rastro + [(self.x, self.y)])[-6:]
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.RECUPERANDO, self.ritmo(70)
                self.anel_pendente = True

        else:  # RECUPERANDO: desliza ate parar
            self.vx *= 0.9
            self.vy *= 0.9
            self.angulo += 2
            self.rastro = self.rastro[1:]
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.MIRANDO, self.ritmo(60)

        self.x += self.vx
        self.y += self.vy
        self.quicar()

    def quicar(self):
        r = self.raio
        if self.x < r or self.x > LARGURA - r:
            self.x = max(r, min(LARGURA - r, self.x))
            self.vx = -self.vx
        if self.y < r or self.y > ALTURA - r:
            self.y = max(r, min(ALTURA - r, self.y))
            self.vy = -self.vy

    def padrao_ataque(self):
        if not self.anel_pendente:
            return []
        self.anel_pendente = False
        return self.rajada_circular(12 if self.furioso else 8, 3.0, self.angulo)

    def desenhar(self, tela):
        if self.fase == self.MIRANDO and not self.entrando:
            self.desenhar_mira(tela)

        for i, (rx, ry) in enumerate(self.rastro):
            fantasma = grafico.rotacionar(self.EXTERNO, self.angulo, rx, ry)
            pygame.draw.aalines(tela, self.cor_atual(0.08 + 0.05 * i), True, fantasma)

        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.EXTERNO, self.angulo, self.x, self.y))
        grafico.contorno(
            tela, self.cor_atual(0.7),
            grafico.rotacionar(self.INTERNO, -self.angulo * 1.5 + 45, self.x, self.y), brilho=False,
        )
        grafico.circulo(tela, cor, (self.x, self.y), 2, 0)
        self.desenhar_marcadores(tela)

    def desenhar_mira(self, tela):
        """Linha tracejada ate o ponto da investida; fica solida quando a mira trava."""
        travada = self.tempo_fase <= self.TRAVA_MIRA
        cor = self.COR if travada else grafico.misturar(self.COR, 0.45)
        dx, dy = self.mira[0] - self.x, self.mira[1] - self.y
        distancia = math.hypot(dx, dy)
        if distancia < 1:
            return
        ux, uy = dx / distancia, dy / distancia
        passo = 16
        for d in range(int(self.raio + 10), int(distancia), passo):
            fim = min(distancia, d + (passo if travada else passo / 2))
            pygame.draw.aaline(tela, cor, (self.x + ux * d, self.y + uy * d), (self.x + ux * fim, self.y + uy * fim))
        grafico.circulo(tela, cor, self.mira, 10)


# ---------------------------------------------------------------------------
# 05 · NUCLEO: aneis concentricos; espiral dupla e minas que explodem
# ---------------------------------------------------------------------------
class Nucleo(Chefe):
    NOME = "NUCLEO"
    COR = (255, 150, 60)
    RAIO = 34
    VIDA_BASE = 70

    def __init__(self, ciclo: int = 0):
        super().__init__(ciclo)
        self.espiral: float = 0.0

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.01) * 200
        self.y = POSICAO_INICIAL_Y + math.sin(t * 0.02) * 40
        self.angulo += 2.2 if self.furioso else 1.2

    def padrao_ataque(self):
        novos = []
        if self.pronto("espiral", 13):
            bracos = 3 if self.furioso else 2
            for b in range(bracos):
                novos.append(self.disparar(self.espiral + b * 360 / bracos, 2.8))
            self.espiral += 11
        if self.pronto("mina", 150):
            fragmentos = 10 if self.furioso else 8
            novos.append(self.disparar(self.angulo_ate_alvo(), 1.9, detonacao=70, fragmentos=fragmentos))
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        self.desenhar_anel(tela, cor, 22, 3, 80, self.angulo)
        self.desenhar_anel(tela, self.cor_atual(0.7), 36, 4, 50, -self.angulo * 0.7)

        # nucleo pulsante com mira em cruz
        pulso = 9 + 2 * math.sin(self.tempo * 0.15)
        grafico.circulo(tela, cor, (self.x, self.y), pulso)
        for a in (0, 90, 180, 270):
            rad = math.radians(a + self.angulo * 0.5)
            inicio = (self.x + math.cos(rad) * 3, self.y + math.sin(rad) * 3)
            fim = (self.x + math.cos(rad) * 6, self.y + math.sin(rad) * 6)
            pygame.draw.aaline(tela, cor, inicio, fim)
        self.desenhar_marcadores(tela)

    def desenhar_anel(self, tela, cor, raio, arcos, abertura, giro):
        rect = pygame.Rect(0, 0, raio * 2, raio * 2)
        rect.center = (int(self.x), int(self.y))
        for i in range(arcos):
            inicio = math.radians(giro + i * 360 / arcos)
            pygame.draw.arc(tela, cor, rect, inicio, inicio + math.radians(abertura), 2)


# ordem de aparicao: nivel 5, 10, 15, 20, 25 (depois recomeca, mais forte)
CHEFES = [Sentinela, Arpao, Orbita, Prisma, Nucleo]
