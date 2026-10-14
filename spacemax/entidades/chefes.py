"""
Chefes: um inimigo grande a cada NIVEIS_POR_CHEFE niveis.

Cada chefe tem forma, cor e padrao de ataque proprios. Aqui ficam a base e os
chefes 01-09; os chefes 10-20 e a ordem de aparicao (CHEFES) ficam em
chefes_elite.py. Depois do ultimo os chefes sao sorteados, cada vez mais fortes (`ciclo`).
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
FATOR_VIDA = 0.75  # fracao da VIDA_BASE de cada chefe
FATOR_INTERVALO = 1.2  # multiplica o intervalo entre ataques (maior = ataca menos)
FATOR_VELOCIDADE = 0.9  # multiplica a velocidade dos projeteis
FATOR_FURIOSO = 0.7  # intervalo entre ataques na fase furiosa (menor = mais agressivo)


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
    # multiplicadores da dificuldade escolhida (o jogo define antes de criar cada chefe)
    ajuste_vida: float = 1.0
    ajuste_ritmo: float = 1.0
    ajuste_velocidade: float = 1.0

    def __init__(self, ciclo: float = 0):
        super().__init__(LARGURA / 2, -self.RAIO * 2, self.RAIO)
        # quantas vezes a lista de chefes ja deu a volta; fracionario para que cada
        # chefe seja um pouco mais forte que o anterior (0.0, 0.05, 0.1 ... 1.0, 1.05 ...)
        self.ciclo: float = ciclo
        self.vida_max: int = max(1, int(self.VIDA_BASE * FATOR_VIDA * (1 + 0.5 * ciclo) * self.ajuste_vida))
        self.vida: int = self.vida_max
        self.tempo: int = 0
        self.tempo_entrada: int = DURACAO_ENTRADA
        self.clarao: int = 0
        self.angulo: float = 0.0
        self.alvo: tuple[float, float] = (LARGURA / 2, ALTURA / 2)
        self.recargas: dict[str, int] = {}
        self.som_pendente: str | None = None  # o jogo toca e limpa a cada frame

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

    def receber_dano(self, quantidade=1, x=None, y=None) -> bool:
        """(x, y): onde o golpe acertou (chefes com partes usam para saber qual parte)."""
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

    def ponto_contato(self, entidade) -> tuple[float, float, float]:
        """(x, y, raio) da parte do chefe que tocou `entidade` (para empurrar a nave)."""
        return self.x, self.y, self.raio

    def ataque_continuo(self, nave) -> bool:
        """Ataques que nao sao projeteis (ex.: laser) atingindo a nave neste frame."""
        return False

    def ao_bloquear(self, tiro):
        """Chamado quando `bloqueia(tiro)` segurou um tiro da nave (ex.: espelho reflete)."""

    def forca_sobre(self, nave) -> tuple[float, float]:
        """Aceleracao extra aplicada na nave a cada frame (ex.: gravidade)."""
        return 0.0, 0.0

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
        fator = FATOR_INTERVALO * (FATOR_FURIOSO if self.furioso else 1.0) * 0.85 ** self.ciclo * self.ajuste_ritmo
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
        velocidade *= FATOR_VELOCIDADE * (1 + 0.15 * self.ciclo) * self.ajuste_velocidade
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

    def __init__(self, ciclo: float = 0):
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

    def __init__(self, ciclo: float = 0):
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

    def __init__(self, ciclo: float = 0):
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

    def ponto_contato(self, entidade):
        for sx, sy in self.satelites():
            if math.hypot(entidade.x - sx, entidade.y - sy) < self.RAIO_SATELITE + entidade.raio:
                return sx, sy, self.RAIO_SATELITE
        return super().ponto_contato(entidade)

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

    def __init__(self, ciclo: float = 0):
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

    def __init__(self, ciclo: float = 0):
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


# ---------------------------------------------------------------------------
# 06 · GEMEOS: dois triangulos que orbitam um centro vazio; tiros alternados
# ---------------------------------------------------------------------------
class Gemeos(Chefe):
    NOME = "GEMEOS"
    COR = (255, 240, 120)
    RAIO = 50  # area do conjunto (explosoes e marcadores); o dano e nos gemeos
    VIDA_BASE = 60
    RAIO_GEMEO = 20
    TRIANGULO = [(0, -22), (19, 11), (-19, 11)]

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.giro: float = 0.0
        self.separacao: float = 60.0
        self.vez: int = 0  # qual gemeo atira agora

    def gemeos(self) -> list[tuple[float, float]]:
        a = math.radians(self.giro)
        dx, dy = math.cos(a) * self.separacao, math.sin(a) * self.separacao
        return [(self.x + dx, self.y + dy), (self.x - dx, self.y - dy)]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.009) * 250
        self.y = POSICAO_INICIAL_Y + math.sin(t * 0.021) * 35
        self.giro += 2.6 if self.furioso else 1.6
        # os gemeos se afastam e se aproximam como uma tesoura
        self.separacao = 62 + math.sin(t * 0.03) * (40 if self.furioso else 28)

    def _gemeo_tocado(self, entidade):
        for gx, gy in self.gemeos():
            if math.hypot(entidade.x - gx, entidade.y - gy) < self.RAIO_GEMEO + entidade.raio:
                return gx, gy
        return None

    def atinge(self, entidade) -> bool:
        return not self.entrando and self._gemeo_tocado(entidade) is not None

    def ponto_contato(self, entidade):
        gemeo = self._gemeo_tocado(entidade)
        if gemeo:
            return gemeo[0], gemeo[1], self.RAIO_GEMEO
        return super().ponto_contato(entidade)

    def padrao_ataque(self):
        novos = []
        if self.pronto("tiro", 34):
            gx, gy = self.gemeos()[self.vez]
            self.vez = 1 - self.vez
            desvios = (-9, 0, 9) if self.furioso else (0,)
            alvo = self.angulo_ate_alvo((gx, gy))
            novos += [self.disparar(alvo + d, 4.0, origem=(gx, gy)) for d in desvios]
        if self.pronto("cruz", 140):
            for gx, gy in self.gemeos():
                novos += [self.disparar(self.giro + 45 + 90 * i, 3.0, origem=(gx, gy)) for i in range(4)]
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        (ax, ay), (bx, by) = self.gemeos()

        # elo tracejado entre os dois
        for i in range(0, 10, 2):
            p0, p1 = i / 10, (i + 1) / 10
            pygame.draw.aaline(
                tela, self.cor_atual(0.35),
                (ax + (bx - ax) * p0, ay + (by - ay) * p0), (ax + (bx - ax) * p1, ay + (by - ay) * p1),
            )
        grafico.circulo(tela, self.cor_atual(0.5), (self.x, self.y), 3)

        carga = self.carga("cruz", 24)
        for (gx, gy), sentido in (((ax, ay), 1), ((bx, by), -1)):
            grafico.contorno(tela, cor, grafico.rotacionar(self.TRIANGULO, self.giro * 2 * sentido, gx, gy))
            if carga > 0 and not self.entrando:
                grafico.circulo(tela, grafico.misturar(self.COR, carga), (gx, gy), 26 - 10 * carga)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 07 · ESPECTRO: some, reaparece em outro ponto e solta um anel (intocavel oculto)
# ---------------------------------------------------------------------------
class Espectro(Chefe):
    NOME = "ESPECTRO"
    COR = (120, 140, 255)
    RAIO = 28
    VIDA_BASE = 65
    FORMA = [(0, -32), (24, -14), (22, 22), (8, 12), (0, 26), (-8, 12), (-22, 22), (-24, -14)]
    VISIVEL, SUMINDO, OCULTO, SURGINDO = range(4)
    DURACAO_FADE = 30
    DURACAO_OCULTO = 40

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.fase: int = self.VISIVEL
        self.tempo_fase: int = self.ritmo(150)
        self.ancora: tuple[float, float] = (LARGURA / 2, POSICAO_INICIAL_Y)
        self.destino: tuple[float, float] = self.ancora
        self.anel_pendente: bool = False
        self.minas_pendentes: bool = False

    @property
    def opacidade(self) -> float:
        if self.fase == self.SUMINDO:
            return self.tempo_fase / self.DURACAO_FADE
        if self.fase == self.OCULTO:
            return 0.0
        if self.fase == self.SURGINDO:
            return 1 - self.tempo_fase / self.DURACAO_FADE
        return 1.0

    @property
    def tangivel(self) -> bool:
        return self.fase == self.VISIVEL

    def receber_dano(self, quantidade=1, x=None, y=None) -> bool:
        return self.tangivel and super().receber_dano(quantidade, x, y)

    def atinge(self, entidade) -> bool:
        return self.tangivel and super().atinge(entidade)

    def sortear_destino(self):
        """Ponto longe da nave, para nao reaparecer em cima dela."""
        for _ in range(12):
            destino = (random.uniform(90, LARGURA - 90), random.uniform(90, ALTURA * 0.6))
            if math.hypot(destino[0] - self.alvo[0], destino[1] - self.alvo[1]) > 260:
                break
        self.destino = destino

    def mover_padrao(self):
        self.tempo_fase -= 1
        if self.fase == self.VISIVEL:
            t = self.tempo_ativo
            self.x = self.ancora[0] + math.sin(t * 0.05) * 18
            self.y = self.ancora[1] + math.sin(t * 0.08) * 10
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.SUMINDO, self.DURACAO_FADE
                self.minas_pendentes = self.furioso
                self.som_pendente = "teleporte"
        elif self.fase == self.SUMINDO:
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.OCULTO, self.DURACAO_OCULTO
                self.sortear_destino()
        elif self.fase == self.OCULTO:
            if self.tempo_fase <= 0:
                self.x, self.y = self.ancora = self.destino
                self.fase, self.tempo_fase = self.SURGINDO, self.DURACAO_FADE
        elif self.tempo_fase <= 0:  # SURGINDO
            self.fase, self.tempo_fase = self.VISIVEL, self.ritmo(150)
            self.anel_pendente = True
        self.angulo = math.sin(self.tempo * 0.04) * 8

    def padrao_ataque(self):
        novos = []
        if self.anel_pendente:
            self.anel_pendente = False
            novos += self.rajada_circular(14 if self.furioso else 10, 2.8, random.uniform(0, 36))
        if self.minas_pendentes:
            # furioso: deixa minas no lugar de onde sumiu
            self.minas_pendentes = False
            novos += [self.disparar(a, 0.6, detonacao=80, fragmentos=8) for a in (0, 180)]
        if self.tangivel and self.pronto("mira", 45):
            alvo = self.angulo_ate_alvo()
            novos += [self.disparar(alvo + d, 4.4) for d in (-6, 6)]
        return novos

    def desenhar(self, tela):
        # onde vai reaparecer: circulo que fecha ate o ponto
        if self.fase in (self.OCULTO, self.SURGINDO):
            p = 1 - self.tempo_fase / self.DURACAO_OCULTO if self.fase == self.OCULTO else 1.0
            grafico.circulo(tela, grafico.misturar(self.COR, 0.25 + 0.4 * p), self.destino, 70 - 40 * p)

        opacidade = self.opacidade
        if opacidade <= 0:
            return
        cor = self.cor_atual(opacidade)
        grafico.contorno(tela, cor, grafico.rotacionar(self.FORMA, self.angulo, self.x, self.y), brilho=self.tangivel)

        # olhos que acompanham a nave
        dx, dy = self.alvo[0] - self.x, self.alvo[1] - self.y
        distancia = max(1.0, math.hypot(dx, dy))
        ox, oy = dx / distancia * 3, dy / distancia * 3
        for lado in (-1, 1):
            grafico.circulo(tela, cor, (self.x + lado * 9 + ox, self.y - 6 + oy), 3, 0)
        if self.tangivel:
            self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 08 · VESPA: voo nervoso; misseis teleguiados e ferrao mirado
# ---------------------------------------------------------------------------
class Vespa(Chefe):
    NOME = "VESPA"
    COR = (170, 255, 60)
    RAIO = 26
    VIDA_BASE = 70
    CORPO = [(0, -26), (12, -8), (10, 16), (0, 30), (-10, 16), (-12, -8)]
    ASA = [(6, -6), (34, -20), (38, -2), (10, 6)]
    FERRAO = (0, 30)

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.destino: tuple[float, float] = (LARGURA / 2, POSICAO_INICIAL_Y)

    def mover_padrao(self):
        if self.pronto("destino", 70):
            self.destino = (random.uniform(110, LARGURA - 110), random.uniform(80, ALTURA * 0.45))
        suavidade = 0.06 if self.furioso else 0.045
        vx = (self.destino[0] - self.x) * suavidade
        self.x += vx
        self.y += (self.destino[1] - self.y) * suavidade
        self.angulo = -max(-25.0, min(25.0, vx * 4))  # inclina na direcao do voo

    def ponta_ferrao(self):
        (px, py), = grafico.rotacionar([self.FERRAO], self.angulo, self.x, self.y)
        return px, py

    def padrao_ataque(self):
        novos = []
        if self.pronto("misseis", 140):
            angulos = (200, 270, 340) if self.furioso else (210, 330)
            novos += [self.disparar(a, 3.2, guiado=110) for a in angulos]
        if self.pronto("ferrao", 50):
            origem = self.ponta_ferrao()
            novos.append(self.disparar(self.angulo_ate_alvo(origem), 5.0, origem=origem))
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        bater = math.sin(self.tempo * 0.7) * 0.35  # asas batendo
        for lado in (-1, 1):
            asa = [(lado * x, y * (1 + bater)) for x, y in self.ASA]
            grafico.contorno(
                tela, self.cor_atual(0.5), grafico.rotacionar(asa, self.angulo, self.x, self.y), brilho=False
            )
        grafico.contorno(tela, cor, grafico.rotacionar(self.CORPO, self.angulo, self.x, self.y))
        # listras do abdome
        for y in (2, 10, 18):
            a, b = grafico.rotacionar([(-9, y), (9, y)], self.angulo, self.x, self.y)
            pygame.draw.aaline(tela, self.cor_atual(0.6), a, b)

        carga = self.carga("misseis", 30)
        if carga > 0 and not self.entrando:
            grafico.circulo(tela, grafico.misturar(self.COR, carga), (self.x, self.y), 40 - 12 * carga)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 09 · FAROL: octogono com laser que varre a tela (avisa antes com uma mira)
# ---------------------------------------------------------------------------
class Farol(Chefe):
    NOME = "FAROL"
    COR = (235, 240, 255)
    RAIO = 32
    VIDA_BASE = 80
    OCTOGONO = _poligono_regular(8, 32, 22.5)
    INTERNO = _poligono_regular(8, 16, 22.5)
    DESCANSO, CARREGANDO, DISPARANDO = range(3)
    DURACAO_CARGA = 70
    DURACAO_FEIXE = 100
    ESPESSURA_FEIXE = 8  # meia largura usada na colisao
    ALCANCE_FEIXE = 1300

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.fase: int = self.DESCANSO
        self.tempo_fase: int = self.ritmo(90)
        self.angulo_feixe: float = 90.0
        self.sentido: int = 1
        self.destino: tuple[float, float] = (LARGURA / 2, POSICAO_INICIAL_Y)
        self.anel_pendente: bool = False

    def feixes(self) -> list[float]:
        if self.furioso:
            return [self.angulo_feixe, self.angulo_feixe + 180]
        return [self.angulo_feixe]

    def mover_padrao(self):
        self.tempo_fase -= 1
        if self.fase == self.DESCANSO:
            self.x += (self.destino[0] - self.x) * 0.03
            self.y += (self.destino[1] - self.y) * 0.03
            self.angulo += 1
            if self.tempo_fase <= 0:
                # o feixe comeca ao lado da nave e varre passando por ela
                self.sentido = random.choice((-1, 1))
                self.angulo_feixe = self.angulo_ate_alvo() - self.sentido * 40
                self.fase, self.tempo_fase = self.CARREGANDO, self.DURACAO_CARGA
        elif self.fase == self.CARREGANDO:
            self.angulo += 4
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.DISPARANDO, self.DURACAO_FEIXE
                self.som_pendente = "laser"
        else:  # DISPARANDO
            self.angulo_feixe += self.sentido * (1.4 if self.furioso else 1.1)
            if self.tempo_fase <= 0:
                self.fase, self.tempo_fase = self.DESCANSO, self.ritmo(110)
                self.destino = (random.uniform(160, LARGURA - 160), random.uniform(110, ALTURA * 0.5))
                self.anel_pendente = True

    def ataque_continuo(self, nave) -> bool:
        if self.entrando or self.fase != self.DISPARANDO:
            return False
        vx, vy = nave.x - self.x, nave.y - self.y
        for angulo in self.feixes():
            dx, dy = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
            if vx * dx + vy * dy > 0 and abs(vx * dy - vy * dx) < self.ESPESSURA_FEIXE + nave.raio:
                return True
        return False

    def padrao_ataque(self):
        novos = []
        if self.anel_pendente:
            self.anel_pendente = False
            novos += self.rajada_circular(14 if self.furioso else 10, 2.6, self.angulo)
        if self.fase == self.DESCANSO and self.pronto("tiro", 40):
            novos.append(self.disparar(self.angulo_ate_alvo(), 4.2))
        return novos

    def desenhar(self, tela):
        if not self.entrando:
            for angulo in self.feixes():
                self.desenhar_feixe(tela, angulo)
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.OCTOGONO, self.angulo * 0.5, self.x, self.y))
        grafico.contorno(
            tela, self.cor_atual(0.6), grafico.rotacionar(self.INTERNO, -self.angulo, self.x, self.y), brilho=False
        )
        lampada = 5 + (4 if self.fase != self.DESCANSO else 0)
        grafico.circulo(tela, cor, (self.x, self.y), lampada, 0)
        self.desenhar_marcadores(tela)

    def desenhar_feixe(self, tela, angulo):
        dx, dy = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
        inicio = (self.x + dx * (self.raio + 4), self.y + dy * (self.raio + 4))
        fim = (self.x + dx * self.ALCANCE_FEIXE, self.y + dy * self.ALCANCE_FEIXE)
        if self.fase == self.CARREGANDO:
            # mira tracejada que fica mais forte perto do disparo
            carga = 1 - self.tempo_fase / self.DURACAO_CARGA
            cor = grafico.misturar(self.COR, 0.2 + 0.6 * carga)
            for d in range(self.raio + 4, self.ALCANCE_FEIXE, 24):
                pygame.draw.aaline(
                    tela, cor, (self.x + dx * d, self.y + dy * d), (self.x + dx * (d + 12), self.y + dy * (d + 12))
                )
        elif self.fase == self.DISPARANDO:
            pulso = 1 + 0.25 * math.sin(self.tempo * 0.8)
            pygame.draw.line(
                tela, grafico.misturar(self.COR, 0.25), inicio, fim, int(self.ESPESSURA_FEIXE * 2.6 * pulso)
            )
            pygame.draw.line(tela, grafico.misturar(self.COR, 0.7), inicio, fim, self.ESPESSURA_FEIXE)
            pygame.draw.aaline(tela, (255, 255, 255), inicio, fim)

