"""
Chefes 10-20 (niveis 50 a 100) e a ordem de aparicao de todos os chefes.

Cada um traz uma mecanica nova: escudo direcional, corpo de serpente, drones
que podem ser abatidos, espelhos que refletem tiros, aneis com vao, cabecas
que precisam cair antes do nucleo, copias falsas, bracos giratorios, raios
marcados no chao, gravidade e, no nivel 100, o Imperador.
"""

import math
import random

import pygame

from .. import grafico
from ..config import ALTURA, FPS, LARGURA
from .chefes import (
    POSICAO_INICIAL_Y,
    Arpao,
    Chefe,
    Espectro,
    Farol,
    Gemeos,
    Nucleo,
    Orbita,
    Prisma,
    Sentinela,
    Vespa,
    _poligono_regular,
)
from .projetil import ProjetilChefe


def _distancia_segmento(px, py, ax, ay, bx, by) -> float:
    """Distancia do ponto (px, py) ao segmento A-B."""
    dx, dy = bx - ax, by - ay
    comprimento2 = dx * dx + dy * dy or 1.0
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / comprimento2))
    return math.hypot(px - (ax + dx * t), py - (ay + dy * t))


def _diferenca_angular(a, b) -> float:
    """Diferenca entre dois angulos em graus, no intervalo -180..180."""
    return (a - b + 180) % 360 - 180


def _girar_ate(atual, alvo, maximo) -> float:
    return atual + max(-maximo, min(maximo, _diferenca_angular(alvo, atual)))


# ---------------------------------------------------------------------------
# 10 · BASTIAO: escudo em arco virado para a nave; o ponto fraco e as costas
# ---------------------------------------------------------------------------
class Bastiao(Chefe):
    NOME = "BASTIAO"
    COR = (90, 200, 255)
    RAIO = 48  # nucleo + arco
    VIDA_BASE = 85
    RAIO_ARCO = 48
    ABERTURA_ARCO = 240  # graus cobertos pelo escudo
    NUCLEO = _poligono_regular(6, 22, 30)

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.angulo_escudo: float = 90.0  # 0 = direita, sentido horario

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.007) * 260
        self.y = POSICAO_INICIAL_Y + 60 + math.sin(t * 0.013) * 70
        giro = 1.3 if self.furioso else 0.8
        self.angulo_escudo = _girar_ate(self.angulo_escudo, self.angulo_ate_alvo(), giro)
        self.angulo += 0.7

    def bloqueia(self, tiro) -> bool:
        if self.entrando:
            return False
        distancia = math.hypot(tiro.x - self.x, tiro.y - self.y)
        if not self.RAIO_ARCO - 10 < distancia < self.RAIO_ARCO + 12:
            return False
        angulo = math.degrees(math.atan2(tiro.y - self.y, tiro.x - self.x))
        return abs(_diferenca_angular(angulo, self.angulo_escudo)) < self.ABERTURA_ARCO / 2

    def padrao_ataque(self):
        novos = []
        if self.pronto("frente", 55):
            alvo = self.angulo_ate_alvo()
            novos += [self.disparar(alvo + d, 4.2) for d in (-12, 0, 12)]
        if self.furioso and self.pronto("costas", 120):
            # pune quem fica atras: leque saindo pelo vao do escudo
            costas = self.angulo_escudo + 180
            novos += [self.disparar(costas + d, 3.4) for d in range(-50, 51, 20)]
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.NUCLEO, self.angulo, self.x, self.y))
        grafico.circulo(tela, cor, (self.x, self.y), 6)

        # escudo: arco grosso com segmentos
        rect = pygame.Rect(0, 0, self.RAIO_ARCO * 2, self.RAIO_ARCO * 2)
        rect.center = (int(self.x), int(self.y))
        inicio = -(self.angulo_escudo + self.ABERTURA_ARCO / 2)  # pygame: anti-horario, y para cima
        for i in range(6):
            a = math.radians(inicio + i * self.ABERTURA_ARCO / 6 + 2)
            b = math.radians(inicio + (i + 1) * self.ABERTURA_ARCO / 6 - 2)
            pygame.draw.arc(tela, self.cor_atual(0.3), rect.inflate(10, 10), a, b, 6)
            pygame.draw.arc(tela, cor, rect, a, b, 3)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 11 · SERPENTE: so a cabeca leva dano; o corpo bloqueia tiros e machuca
# ---------------------------------------------------------------------------
class Serpente(Chefe):
    NOME = "SERPENTE"
    COR = (120, 255, 120)
    RAIO = 20
    VIDA_BASE = 90
    SEGMENTOS = 12
    RAIO_SEGMENTO = 13
    ESPACAMENTO = 7  # frames de historico entre segmentos
    CABECA = [(0, -22), (16, -4), (12, 14), (-12, 14), (-16, -4)]

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.historico: list[tuple[float, float]] = []

    def segmentos(self) -> list[tuple[float, float]]:
        pontos = []
        for i in range(1, self.SEGMENTOS + 1):
            indice = len(self.historico) - 1 - i * self.ESPACAMENTO
            pontos.append(self.historico[max(0, indice)] if self.historico else (self.x, self.y))
        return pontos

    def atualizar(self):
        super().atualizar()
        self.historico = (self.historico + [(self.x, self.y)])[-(self.SEGMENTOS + 1) * self.ESPACAMENTO:]

    def mover_padrao(self):
        t = self.tempo_ativo
        velocidade = 1.35 if self.furioso else 1.0
        anterior = (self.x, self.y)
        self.x = LARGURA / 2 + math.sin(t * 0.011 * velocidade) * (LARGURA / 2 - 90)
        self.y = POSICAO_INICIAL_Y + (ALTURA / 2 - 120) * (1 - math.cos(t * 0.017 * velocidade)) / 2 * 1.6
        self.angulo = math.degrees(math.atan2(self.x - anterior[0], -(self.y - anterior[1])))

    def _segmento_tocado(self, entidade):
        for sx, sy in self.segmentos():
            if math.hypot(entidade.x - sx, entidade.y - sy) < self.RAIO_SEGMENTO + entidade.raio:
                return sx, sy
        return None

    def bloqueia(self, tiro) -> bool:
        return not self.entrando and self._segmento_tocado(tiro) is not None

    def atinge(self, entidade) -> bool:
        if self.entrando:
            return False
        return self.colide_com(entidade) or self._segmento_tocado(entidade) is not None

    def ponto_contato(self, entidade):
        segmento = self._segmento_tocado(entidade)
        if segmento and not self.colide_com(entidade):
            return segmento[0], segmento[1], self.RAIO_SEGMENTO
        return super().ponto_contato(entidade)

    def padrao_ataque(self):
        novos = []
        if self.pronto("cabeca", 70):
            alvo = self.angulo_ate_alvo()
            novos += [self.disparar(alvo + d, 4.0) for d in (-10, 0, 10)]
        if self.pronto("cauda", 45):
            cauda = self.segmentos()[-1]
            novos.append(self.disparar(self.angulo_ate_alvo(cauda), 3.6, origem=cauda))
        if self.furioso and self.pronto("escamas", 200):
            # cada segmento solta um tiro para fora do corpo
            for i, (sx, sy) in enumerate(self.segmentos()[::2]):
                novos.append(self.disparar(self.angulo + 90 + 180 * (i % 2), 2.4, origem=(sx, sy)))
        return novos

    def desenhar(self, tela):
        for i, (sx, sy) in enumerate(reversed(self.segmentos())):
            intensidade = 0.35 + 0.5 * i / self.SEGMENTOS
            pontos = grafico.rotacionar(_poligono_regular(6, self.RAIO_SEGMENTO), self.tempo * 2 + i * 20, sx, sy)
            grafico.contorno(tela, self.cor_atual(intensidade), pontos, brilho=False)
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.CABECA, self.angulo, self.x, self.y))
        for lado in (-1, 1):
            (ox, oy), = grafico.rotacionar([(lado * 6, -6)], self.angulo, self.x, self.y)
            grafico.circulo(tela, cor, (ox, oy), 2, 0)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 12 · COLMEIA: solta drones cacadores que podem ser abatidos a tiro
# ---------------------------------------------------------------------------
class Colmeia(Chefe):
    NOME = "COLMEIA"
    COR = (255, 190, 40)
    RAIO = 34
    VIDA_BASE = 90
    HEXAGONO = _poligono_regular(6, 34, 30)
    FAVOS = [(0, 0), (12, -7), (12, 7), (0, 14), (-12, 7), (-12, -7), (0, -14)]
    VIDA_DRONE = 9 * FPS

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.drones: list[ProjetilChefe] = []

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.006) * 280
        self.y = POSICAO_INICIAL_Y + math.sin(t * 0.015) * 40
        self.angulo += 0.4

    def padrao_ataque(self):
        novos = []
        self.drones = [d for d in self.drones if not d.abatido and d.tempo < self.VIDA_DRONE]
        limite = 7 if self.furioso else 5
        if self.pronto("drones", 100) and len(self.drones) < limite:
            quantidade = 3 if self.furioso else 2
            for i in range(quantidade):
                drone = self.disparar(60 + 30 * i + random.uniform(-10, 10), 2.0, guiado=self.VIDA_DRONE, destrutivel=True)
                self.drones.append(drone)
                novos.append(drone)
        if self.furioso and self.pronto("anel", 170):
            novos += self.rajada_circular(12, 2.6, self.angulo)
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.HEXAGONO, self.angulo, self.x, self.y))
        favo = _poligono_regular(6, 6, 30)
        for fx, fy in self.FAVOS:
            (cx, cy), = grafico.rotacionar([(fx, fy)], self.angulo, self.x, self.y)
            pygame.draw.aalines(tela, self.cor_atual(0.6), True, grafico.rotacionar(favo, self.angulo, cx, cy))
        carga = self.carga("drones", 25)
        if carga > 0 and not self.entrando:
            grafico.circulo(tela, grafico.misturar(self.COR, carga), (self.x, self.y + 30), 4 + 6 * carga)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 13 · ESPELHO: duas placas refletem os tiros de volta; mire no vao do meio
# ---------------------------------------------------------------------------
class Espelho(Chefe):
    NOME = "ESPELHO"
    COR = (200, 230, 255)
    RAIO = 24
    VIDA_BASE = 95
    LOSANGO = [(0, -26), (18, 0), (0, 26), (-18, 0)]
    DISTANCIA_PLACA = 58
    MEIO_COMPRIMENTO = 30
    ABERTURA_PLACAS = 35  # graus entre a mira e cada placa (deixa um vao no meio)

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.mira: float = 90.0
        self.refletidos: list[ProjetilChefe] = []

    def placas(self) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        segmentos = []
        for lado in (-1, 1):
            a = math.radians(self.mira + lado * self.ABERTURA_PLACAS)
            cx = self.x + math.cos(a) * self.DISTANCIA_PLACA
            cy = self.y + math.sin(a) * self.DISTANCIA_PLACA
            tx, ty = -math.sin(a) * self.MEIO_COMPRIMENTO, math.cos(a) * self.MEIO_COMPRIMENTO
            segmentos.append(((cx - tx, cy - ty), (cx + tx, cy + ty)))
        return segmentos

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.008) * 240
        self.y = POSICAO_INICIAL_Y + 30 + math.sin(t * 0.019) * 50
        self.mira = _girar_ate(self.mira, self.angulo_ate_alvo(), 1.6 if self.furioso else 1.1)
        self.angulo += 1

    def bloqueia(self, tiro) -> bool:
        if self.entrando:
            return False
        return any(_distancia_segmento(tiro.x, tiro.y, *a, *b) < 6 + tiro.raio for a, b in self.placas())

    def atinge(self, entidade) -> bool:
        if self.entrando:
            return False
        if self.colide_com(entidade):
            return True
        # a nave tambem se machuca nas placas
        return any(_distancia_segmento(entidade.x, entidade.y, *a, *b) < 5 + entidade.raio for a, b in self.placas())

    def ao_bloquear(self, tiro):
        if tiro.EXPLOSIVO:
            return
        self.refletidos.append(self.disparar(self.angulo_ate_alvo((tiro.x, tiro.y)), 5.0, origem=(tiro.x, tiro.y)))
        self.som_pendente = "reflexo"

    def padrao_ataque(self):
        novos, self.refletidos = self.refletidos, []
        if self.pronto("mira", 60):
            novos.append(self.disparar(self.angulo_ate_alvo(), 4.6))
        if self.furioso and self.pronto("anel", 150):
            novos += self.rajada_circular(10, 2.6, self.mira + 18)
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.LOSANGO, self.angulo, self.x, self.y))
        grafico.circulo(tela, cor, (self.x, self.y), 5, 0)
        for a, b in self.placas():
            pygame.draw.line(tela, self.cor_atual(0.3), a, b, 8)
            pygame.draw.line(tela, cor, a, b, 3)
            pygame.draw.aaline(tela, (255, 255, 255), a, b)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 14 · PULSAR: emite aneis que crescem pela tela; passe pelo vao de cada anel
# ---------------------------------------------------------------------------
class Pulsar(Chefe):
    NOME = "PULSAR"
    COR = (255, 120, 160)
    RAIO = 28
    VIDA_BASE = 100
    VELOCIDADE_ANEL = 2.3
    ESPESSURA_ANEL = 5

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.aneis: list[list[float]] = []  # [raio, angulo do vao, abertura do vao]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.005) * 160
        self.y = POSICAO_INICIAL_Y + 80 + math.sin(t * 0.011) * 40
        self.angulo += 3
        for anel in self.aneis:
            anel[0] += self.VELOCIDADE_ANEL
        self.aneis = [a for a in self.aneis if a[0] < 1200]
        if self.pronto("anel", 150):
            # vao para um lado da nave: obriga a se mexer, mas da tempo
            vao = self.angulo_ate_alvo() + random.choice((-1, 1)) * random.uniform(40, 100)
            self.aneis.append([self.RAIO + 6, vao, 55 if self.furioso else 75])
            self.som_pendente = "alerta"

    def ataque_continuo(self, nave) -> bool:
        distancia = math.hypot(nave.x - self.x, nave.y - self.y)
        angulo = math.degrees(math.atan2(nave.y - self.y, nave.x - self.x))
        for raio, vao, abertura in self.aneis:
            if abs(distancia - raio) < self.ESPESSURA_ANEL + nave.raio:
                if abs(_diferenca_angular(angulo, vao)) > abertura / 2:
                    return True
        return False

    def padrao_ataque(self):
        if self.pronto("tiro", 60):
            alvo = self.angulo_ate_alvo()
            return [self.disparar(alvo + d, 3.8) for d in ((-8, 8) if self.furioso else (0,))]
        return []

    def desenhar(self, tela):
        for raio, vao, abertura in self.aneis:
            rect = pygame.Rect(0, 0, raio * 2, raio * 2)
            rect.center = (int(self.x), int(self.y))
            # pygame.draw.arc usa graus anti-horarios com y para cima
            inicio = math.radians(-(vao - abertura / 2) - (360 - abertura))
            fim = math.radians(-(vao - abertura / 2))
            pygame.draw.arc(tela, grafico.misturar(self.COR, 0.3), rect.inflate(8, 8), inicio, fim, 8)
            pygame.draw.arc(tela, self.COR, rect, inicio, fim, 3)

        cor = self.cor_atual()
        pulso = 1 + 0.15 * math.sin(self.tempo * 0.3)
        grafico.circulo(tela, cor, (self.x, self.y), 14 * pulso, 0)
        grafico.circulo(tela, cor, (self.x, self.y), self.RAIO)
        for lado in (0, 180):  # feixes do pulsar girando
            a = math.radians(self.angulo + lado)
            grafico.linha(tela, self.cor_atual(0.7), (self.x, self.y),
                          (self.x + math.cos(a) * 46, self.y + math.sin(a) * 46))
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 15 · HIDRA: tres cabecas protegem o nucleo; derrube as cabecas primeiro
# ---------------------------------------------------------------------------
class Hidra(Chefe):
    NOME = "HIDRA"
    COR = (60, 220, 200)
    RAIO = 26
    VIDA_BASE = 105
    RAIO_CABECA = 16
    ANGULOS_CABECAS = (40, 90, 140)  # para baixo (na direcao da nave)
    PESCOCO = 74
    CABECA = [(0, -16), (14, 6), (0, 14), (-14, 6)]

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        parte = int(self.vida_max * 0.2)
        self.vida_cabecas: list[int] = [parte] * 3  # o resto da vida fica no nucleo
        self.vez: int = 0
        self.cabeca_caiu: tuple[float, float] | None = None

    def cabecas(self) -> list[tuple[float, float]]:
        pontos = []
        for i, base in enumerate(self.ANGULOS_CABECAS):
            a = math.radians(base + math.sin(self.tempo * 0.04 + i * 2) * 14)
            pontos.append((self.x + math.cos(a) * self.PESCOCO, self.y + math.sin(a) * self.PESCOCO))
        return pontos

    def cabecas_vivas(self) -> list[tuple[int, tuple[float, float]]]:
        return [(i, p) for i, p in enumerate(self.cabecas()) if self.vida_cabecas[i] > 0]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.008) * 230
        self.y = POSICAO_INICIAL_Y - 20 + math.sin(t * 0.017) * 30
        self.angulo += 1

    def _cabeca_tocada(self, entidade):
        for i, (cx, cy) in self.cabecas_vivas():
            if math.hypot(entidade.x - cx, entidade.y - cy) < self.RAIO_CABECA + entidade.raio:
                return i, (cx, cy)
        return None

    def bloqueia(self, tiro) -> bool:
        # enquanto houver cabecas, o nucleo e blindado
        return not self.entrando and bool(self.cabecas_vivas()) and self.colide_com(tiro)

    def atinge(self, entidade) -> bool:
        if self.entrando:
            return False
        return self.colide_com(entidade) or self._cabeca_tocada(entidade) is not None

    def ponto_contato(self, entidade):
        tocada = self._cabeca_tocada(entidade)
        if tocada and not self.colide_com(entidade):
            return tocada[1][0], tocada[1][1], self.RAIO_CABECA
        return super().ponto_contato(entidade)

    def receber_dano(self, quantidade=1, x=None, y=None) -> bool:
        if self.entrando or self.morto():
            return False
        vivas = self.cabecas_vivas()
        if not vivas:
            return super().receber_dano(quantidade, x, y)
        if x is None:
            return False
        i, (cx, cy) = min(vivas, key=lambda c: math.hypot(c[1][0] - x, c[1][1] - y))
        if math.hypot(cx - x, cy - y) > 100:
            return False
        dano = min(quantidade, self.vida_cabecas[i])
        self.vida_cabecas[i] -= dano
        self.vida -= dano
        self.clarao = 6
        if self.vida_cabecas[i] <= 0:
            self.cabeca_caiu = (cx, cy)
        return True

    def padrao_ataque(self):
        novos = []
        if self.cabeca_caiu:  # a cabeca solta um ultimo anel ao cair
            novos += [self.disparar(360 * k / 8, 2.6, origem=self.cabeca_caiu) for k in range(8)]
            self.cabeca_caiu = None
        vivas = self.cabecas_vivas()
        if vivas and self.pronto("cabecas", 40):
            _, origem = vivas[self.vez % len(vivas)]
            self.vez += 1
            novos.append(self.disparar(self.angulo_ate_alvo(origem), 4.2, origem=origem))
        if not vivas and self.pronto("espiral", 8):
            # sem cabecas, o nucleo se desespera: espiral tripla
            novos += [self.disparar(self.angulo * 7 + k * 120, 2.8) for k in range(3)]
        return novos

    def desenhar(self, tela):
        cor = self.cor_atual()
        for i, (cx, cy) in enumerate(self.cabecas()):
            if self.vida_cabecas[i] <= 0:
                grafico.circulo(tela, self.cor_atual(0.2), (cx, cy), 5)
                continue
            pygame.draw.aaline(tela, self.cor_atual(0.5), (self.x, self.y), (cx, cy))
            angulo = math.degrees(math.atan2(self.alvo[0] - cx, -(self.alvo[1] - cy)))
            grafico.contorno(tela, cor, grafico.rotacionar(self.CABECA, angulo, cx, cy))
        blindado = bool(self.cabecas_vivas())
        nucleo = _poligono_regular(8, self.RAIO, self.angulo)
        grafico.contorno(tela, cor if not blindado else self.cor_atual(0.6), grafico.rotacionar(nucleo, 0, self.x, self.y))
        if blindado:
            grafico.circulo(tela, self.cor_atual(0.4), (self.x, self.y), self.RAIO + 6)
        else:
            grafico.circulo(tela, cor, (self.x, self.y), 8 + 2 * math.sin(self.tempo * 0.3), 0)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 16 · MIRAGEM: tres copias iguais; so a verdadeira leva dano (ela pisca ao ser atingida)
# ---------------------------------------------------------------------------
class Miragem(Chefe):
    NOME = "MIRAGEM"
    COR = (230, 150, 255)
    RAIO = 26
    VIDA_BASE = 105
    FORMA = _poligono_regular(5, 28, -90)
    RAIO_RODA = 150
    DURACAO_EMBARALHAR = 70

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.centro: tuple[float, float] = (LARGURA / 2, POSICAO_INICIAL_Y)
        self.giro: float = 0.0
        self.verdadeira: int = 0
        self.embaralhando: int = self.DURACAO_EMBARALHAR // 2  # comeca se separando do centro
        self.vez: int = 0

    def imagens(self) -> list[tuple[float, float]]:
        raio = self.RAIO_RODA
        if self.embaralhando:
            # se juntam no centro e se espalham de novo (de olho, da para seguir)
            p = self.embaralhando / self.DURACAO_EMBARALHAR
            raio *= abs(2 * p - 1)
        cx, cy = self.centro
        return [
            (cx + math.cos(math.radians(self.giro + 120 * i)) * raio,
             cy + math.sin(math.radians(self.giro + 120 * i)) * raio * 0.6)
            for i in range(3)
        ]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.centro = (LARGURA / 2 + math.sin(t * 0.006) * 120, POSICAO_INICIAL_Y + math.sin(t * 0.014) * 40)
        self.giro += 0.9 if self.furioso else 0.6
        if self.embaralhando:
            self.embaralhando -= 1
            if self.embaralhando == self.DURACAO_EMBARALHAR // 2:
                self.verdadeira = random.randrange(3)
                self.giro += random.choice((0, 120, 240))
        elif self.pronto("embaralhar", 6 * FPS):
            self.embaralhando = self.DURACAO_EMBARALHAR
        self.angulo += 1.2
        # a posicao "oficial" do chefe e a da copia verdadeira
        self.x, self.y = self.imagens()[self.verdadeira]

    def padrao_ataque(self):
        if self.embaralhando or not self.pronto("tiro", 28):
            return []
        origem = self.imagens()[self.vez % 3]
        self.vez += 1
        return [self.disparar(self.angulo_ate_alvo(origem), 3.8, origem=origem)]

    def desenhar(self, tela):
        if self.entrando:
            grafico.contorno(tela, self.cor_atual(), grafico.rotacionar(self.FORMA, self.angulo, self.x, self.y))
            return
        for i, (ix, iy) in enumerate(self.imagens()):
            # as falsas nao recebem o clarao do dano: e assim que se descobre a verdadeira
            cor = self.cor_atual() if i == self.verdadeira else self.COR
            grafico.contorno(tela, cor, grafico.rotacionar(self.FORMA, self.angulo, ix, iy))
            grafico.circulo(tela, cor, (ix, iy), 6)
        # marcadores iguais nas tres copias (nao entregam a verdadeira)
        x, y = self.x, self.y
        for ix, iy in self.imagens():
            self.x, self.y = ix, iy
            self.desenhar_marcadores(tela)
        self.x, self.y = x, y


# ---------------------------------------------------------------------------
# 17 · CICLONE: bracos giratorios que bloqueiam tiros e cortam a nave
# ---------------------------------------------------------------------------
class Ciclone(Chefe):
    NOME = "CICLONE"
    COR = (150, 255, 230)
    RAIO = 26
    VIDA_BASE = 110
    INICIO_BRACO = 30
    FIM_BRACO = 165
    AVISO_INVERSAO = 40

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.giro: float = 0.0
        self.sentido: int = 1
        self.espiral: float = 0.0

    def bracos(self) -> list[tuple[tuple[float, float], tuple[float, float]]]:
        quantidade = 4 if self.furioso else 3
        segmentos = []
        for i in range(quantidade):
            a = math.radians(self.giro + 360 * i / quantidade)
            dx, dy = math.cos(a), math.sin(a)
            segmentos.append(((self.x + dx * self.INICIO_BRACO, self.y + dy * self.INICIO_BRACO),
                              (self.x + dx * self.FIM_BRACO, self.y + dy * self.FIM_BRACO)))
        return segmentos

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.005) * 200
        self.y = ALTURA / 2 - 40 + math.sin(t * 0.009) * 80
        if self.pronto("inverter", 5 * FPS):
            self.sentido = -self.sentido
        # perto de inverter o giro desacelera (e os bracos piscam)
        freando = self.carga("inverter", self.AVISO_INVERSAO)
        velocidade = (1.5 if self.furioso else 1.0) * (1 - freando)
        self.giro += self.sentido * velocidade
        self.angulo -= 3

    def bloqueia(self, tiro) -> bool:
        if self.entrando:
            return False
        return any(_distancia_segmento(tiro.x, tiro.y, *a, *b) < 6 + tiro.raio for a, b in self.bracos())

    def ataque_continuo(self, nave) -> bool:
        if self.entrando:
            return False
        return any(_distancia_segmento(nave.x, nave.y, *a, *b) < 4 + nave.raio for a, b in self.bracos())

    def padrao_ataque(self):
        if self.pronto("espiral", 14):
            self.espiral += 23
            return [self.disparar(self.espiral, 2.6)]
        return []

    def desenhar(self, tela):
        aviso = self.carga("inverter", self.AVISO_INVERSAO)
        cor_braco = self.COR if not (aviso > 0 and (self.tempo // 4) % 2) else (255, 255, 255)
        cor_braco = self.cor_atual() if self.entrando else cor_braco
        for a, b in self.bracos():
            pygame.draw.line(tela, grafico.misturar(cor_braco, 0.25), a, b, 9)
            pygame.draw.line(tela, cor_braco, a, b, 3)
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(_poligono_regular(3, self.RAIO), self.angulo, self.x, self.y))
        grafico.circulo(tela, cor, (self.x, self.y), self.INICIO_BRACO)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 18 · TEMPESTADE: marca pontos no chao e um raio cai neles pouco depois
# ---------------------------------------------------------------------------
class Tempestade(Chefe):
    NOME = "TEMPESTADE"
    COR = (180, 200, 255)
    RAIO = 34
    VIDA_BASE = 115
    NUVEM = [(-34, 6), (-28, -10), (-12, -18), (6, -20), (22, -12), (34, 2), (24, 14), (-20, 14)]
    AVISO_RAIO = 60
    DURACAO_RAIO = 12
    RAIO_IMPACTO = 46

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.raios: list[list[float]] = []  # [x, y, frames ate cair (negativo = caindo)]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.007) * 300
        self.y = POSICAO_INICIAL_Y - 40 + math.sin(t * 0.02) * 15
        for raio in self.raios:
            raio[2] -= 1
            if raio[2] == 0:
                self.som_pendente = "trovao"
        self.raios = [r for r in self.raios if r[2] > -self.DURACAO_RAIO]
        if self.pronto("raios", 110):
            quantidade = 5 if self.furioso else 3
            ax, ay = self.alvo
            self.raios.append([ax, ay, self.AVISO_RAIO])  # um sempre onde a nave esta
            for _ in range(quantidade - 1):
                x = min(LARGURA - 40, max(40, ax + random.uniform(-220, 220)))
                y = min(ALTURA - 40, max(120, ay + random.uniform(-160, 160)))
                self.raios.append([x, y, self.AVISO_RAIO + random.randint(0, 20)])

    def ataque_continuo(self, nave) -> bool:
        return any(
            r[2] <= 0 and math.hypot(nave.x - r[0], nave.y - r[1]) < self.RAIO_IMPACTO + nave.raio
            for r in self.raios
        )

    def padrao_ataque(self):
        if self.pronto("chuva", 18):
            origem = (self.x + random.uniform(-30, 30), self.y + 16)
            return [self.disparar(90 + random.uniform(-15, 15), 3.0, origem=origem)]
        return []

    def desenhar(self, tela):
        for x, y, tempo in self.raios:
            if tempo > 0:
                # aviso: circulo que fecha + cruz no centro
                p = 1 - tempo / self.AVISO_RAIO
                cor = grafico.misturar(self.COR, 0.3 + 0.6 * p)
                grafico.circulo(tela, cor, (x, y), self.RAIO_IMPACTO + 30 * (1 - p))
                grafico.circulo(tela, grafico.misturar(self.COR, 0.25), (x, y), self.RAIO_IMPACTO)
                pygame.draw.aaline(tela, cor, (x - 8, y), (x + 8, y))
                pygame.draw.aaline(tela, cor, (x, y - 8), (x, y + 8))
            else:
                # o raio: zigue-zague do topo ate o ponto + clarao
                pontos, py = [(x, 0)], 0.0
                while py < y - 30:
                    py += random.uniform(30, 60)
                    pontos.append((x + random.uniform(-22, 22), min(py, y)))
                pontos.append((x, y))
                pygame.draw.lines(tela, grafico.misturar(self.COR, 0.4), False, pontos, 7)
                pygame.draw.lines(tela, (255, 255, 255), False, pontos, 2)
                pygame.draw.circle(tela, grafico.misturar(self.COR, 0.35), (int(x), int(y)), self.RAIO_IMPACTO)
                grafico.circulo(tela, (255, 255, 255), (x, y), self.RAIO_IMPACTO)

        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.NUVEM, 0, self.x, self.y))
        for i in range(3):  # "olhos" eletricos
            grafico.circulo(tela, cor, (self.x - 12 + 12 * i, self.y - 2), 2 + (self.tempo // 6 + i) % 2, 0)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 19 · SINGULARIDADE: buraco negro que puxa a nave; jatos giratorios
# ---------------------------------------------------------------------------
class Singularidade(Chefe):
    NOME = "SINGULARIDADE"
    COR = (255, 140, 90)
    RAIO = 30
    VIDA_BASE = 120
    GRAVIDADE = 8.0
    GRAVIDADE_MAX = 0.12

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.jato: float = 0.0

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.004) * 220
        self.y = ALTURA / 2 - 60 + math.sin(t * 0.009) * 60
        self.angulo += 2.5

    def forca_sobre(self, nave):
        if self.entrando:
            return 0.0, 0.0
        dx, dy = self.x - nave.x, self.y - nave.y
        distancia = max(1.0, math.hypot(dx, dy))
        forca = min(self.GRAVIDADE_MAX, self.GRAVIDADE / distancia) * (1.3 if self.furioso else 1.0)
        return dx / distancia * forca, dy / distancia * forca

    def padrao_ataque(self):
        novos = []
        # jatos relativisticos: 2 s ligados, 3 s desligados
        if (self.tempo_ativo // FPS) % 5 < 2 and self.pronto("jato", 6):
            self.jato += 7 if self.furioso else 5
            novos += [self.disparar(self.jato + lado, 3.2) for lado in (0, 180)]
        if self.pronto("anel", 160):
            novos += self.rajada_circular(16 if self.furioso else 12, 2.2, self.angulo)
        return novos

    def desenhar(self, tela):
        if not self.entrando:
            # linhas de atracao: circulos tracejados que encolhem
            for k in range(3):
                raio = 160 - ((self.tempo * 1.5 + k * 50) % 150)
                cor = grafico.misturar(self.COR, 0.12 + 0.18 * (1 - raio / 160))
                for i in range(0, 360, 20):
                    a = math.radians(i + self.angulo * 0.3)
                    pygame.draw.aaline(
                        tela, cor,
                        (self.x + math.cos(a) * raio, self.y + math.sin(a) * raio),
                        (self.x + math.cos(a + 0.15) * raio, self.y + math.sin(a + 0.15) * raio),
                    )
        # disco de acrecao achatado
        disco = pygame.Rect(0, 0, 130, 40)
        disco.center = (int(self.x), int(self.y))
        cor = self.cor_atual()
        pygame.draw.ellipse(tela, self.cor_atual(0.35), disco.inflate(10, 6), 5)
        pygame.draw.ellipse(tela, cor, disco, 2)
        # horizonte de eventos: disco preto com anel de luz
        pygame.draw.circle(tela, (0, 0, 0), (int(self.x), int(self.y)), self.RAIO)
        grafico.circulo(tela, cor, (self.x, self.y), self.RAIO, 2)
        grafico.circulo(tela, self.cor_atual(0.4), (self.x, self.y), self.RAIO + 6)
        self.desenhar_marcadores(tela)


# ---------------------------------------------------------------------------
# 20 · IMPERADOR (nivel 100): alterna tres fases com ataques de varios chefes
# ---------------------------------------------------------------------------
class Imperador(Chefe):
    NOME = "IMPERADOR"
    COR = (255, 215, 0)
    RAIO = 40
    VIDA_BASE = 170
    DURACAO_FASE = 7 * FPS
    AVISO_FEIXE = 45
    ALCANCE_FEIXE = 1300
    ESPESSURA_FEIXE = 8
    FASES = ("COROA", "RAIO", "LEGIAO")

    def __init__(self, ciclo: float = 0):
        super().__init__(ciclo)
        self.angulo_feixe: float = 90.0
        self.estrela = [
            (math.cos(math.radians(i * 22.5 - 90)) * (40 if i % 2 == 0 else 22),
             math.sin(math.radians(i * 22.5 - 90)) * (40 if i % 2 == 0 else 22))
            for i in range(16)
        ]

    @property
    def fase(self) -> int:
        return (self.tempo_ativo // self.DURACAO_FASE) % 3

    @property
    def tempo_na_fase(self) -> int:
        return self.tempo_ativo % self.DURACAO_FASE

    def feixes(self) -> list[float]:
        return [self.angulo_feixe, self.angulo_feixe + 180] if self.furioso else [self.angulo_feixe]

    def mover_padrao(self):
        t = self.tempo_ativo
        self.x = LARGURA / 2 + math.sin(t * 0.006) * 260
        self.y = POSICAO_INICIAL_Y + 40 + math.sin(t * 0.012) * 60
        self.angulo += 0.8
        if self.fase == 1:
            if self.tempo_na_fase == 0:
                self.angulo_feixe = self.angulo_ate_alvo() + 60
            elif self.tempo_na_fase > self.AVISO_FEIXE:
                if self.tempo_na_fase == self.AVISO_FEIXE + 1:
                    self.som_pendente = "laser"
                self.angulo_feixe += 0.9

    def ataque_continuo(self, nave) -> bool:
        if self.entrando or self.fase != 1 or self.tempo_na_fase <= self.AVISO_FEIXE:
            return False
        vx, vy = nave.x - self.x, nave.y - self.y
        for angulo in self.feixes():
            dx, dy = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
            if vx * dx + vy * dy > 0 and abs(vx * dy - vy * dx) < self.ESPESSURA_FEIXE + nave.raio:
                return True
        return False

    def padrao_ataque(self):
        novos = []
        if self.fase == 0:  # COROA: aneis e leque mirado
            if self.pronto("anel", 50):
                novos += self.rajada_circular(16 if self.furioso else 12, 3.0, self.angulo * 3)
            if self.pronto("leque", 70):
                alvo = self.angulo_ate_alvo()
                novos += [self.disparar(alvo + d, 4.4) for d in (-20, -10, 0, 10, 20)]
        elif self.fase == 1:  # RAIO: so tiros esparsos alem do feixe
            if self.pronto("tiro", 50):
                novos.append(self.disparar(self.angulo_ate_alvo(), 4.0))
        else:  # LEGIAO: misseis e minas
            if self.pronto("misseis", 120):
                novos += [self.disparar(a, 3.2, guiado=110) for a in (200, 270, 340)]
            if self.pronto("mina", 150):
                novos.append(self.disparar(self.angulo_ate_alvo(), 1.9, detonacao=70, fragmentos=10))
        return novos

    def desenhar(self, tela):
        if not self.entrando and self.fase == 1:
            for angulo in self.feixes():
                self.desenhar_feixe(tela, angulo)
        cor = self.cor_atual()
        grafico.contorno(tela, cor, grafico.rotacionar(self.estrela, self.angulo, self.x, self.y))
        grafico.contorno(
            tela, self.cor_atual(0.6),
            grafico.rotacionar(_poligono_regular(8, 18), -self.angulo * 2, self.x, self.y), brilho=False,
        )
        grafico.circulo(tela, cor, (self.x, self.y), 7, 0)
        # tres pontos indicam a fase atual
        for i in range(3):
            centro = (self.x - 14 + 14 * i, self.y + 56)
            grafico.circulo(tela, cor if i == self.fase else self.cor_atual(0.3), centro, 3, 0 if i == self.fase else 1)
        self.desenhar_marcadores(tela)

    def desenhar_feixe(self, tela, angulo):
        dx, dy = math.cos(math.radians(angulo)), math.sin(math.radians(angulo))
        inicio = (self.x + dx * (self.raio + 4), self.y + dy * (self.raio + 4))
        fim = (self.x + dx * self.ALCANCE_FEIXE, self.y + dy * self.ALCANCE_FEIXE)
        if self.tempo_na_fase <= self.AVISO_FEIXE:
            cor = grafico.misturar(self.COR, 0.25 + 0.6 * self.tempo_na_fase / self.AVISO_FEIXE)
            for d in range(self.raio + 4, self.ALCANCE_FEIXE, 24):
                pygame.draw.aaline(tela, cor, (self.x + dx * d, self.y + dy * d),
                                   (self.x + dx * (d + 12), self.y + dy * (d + 12)))
            return
        pygame.draw.line(tela, grafico.misturar(self.COR, 0.25), inicio, fim, self.ESPESSURA_FEIXE * 3)
        pygame.draw.line(tela, grafico.misturar(self.COR, 0.7), inicio, fim, self.ESPESSURA_FEIXE)
        pygame.draw.aaline(tela, (255, 255, 255), inicio, fim)


# ordem de aparicao: um chefe a cada 5 niveis (nivel 5 ate 100); depois recomeca, mais forte
CHEFES = [
    Sentinela, Arpao, Orbita, Gemeos, Prisma, Espectro, Nucleo, Vespa, Farol, Bastiao,
    Serpente, Colmeia, Espelho, Pulsar, Hidra, Miragem, Ciclone, Tempestade, Singularidade, Imperador,
]
