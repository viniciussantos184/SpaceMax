"""
Planos de fundo: um setor diferente a cada NIVEIS_POR_GALAXIA niveis.

Cada setor tem um tipo de cenario (galaxia espiral, nebulosa, aglomerado,
buraco negro, planeta, cinturao de asteroides, supernova, estrela binaria ou
galaxia eliptica) e cores proprias. O fundo e gerado proceduralmente uma
unica vez e depois so e copiado na tela. Os 35 setores cobrem ate o nivel 100+.
"""

import math
import random
from dataclasses import dataclass

import pygame

from .config import ALTURA, LARGURA

NIVEIS_POR_GALAXIA = 3
ESPACAMENTO_GRADE = 48


@dataclass(frozen=True)
class Galaxia:
    nome: str
    cor_fundo: tuple[int, int, int]
    cores_nebulosa: tuple[tuple[int, int, int], tuple[int, int, int]]
    cor_espiral: tuple[int, int, int]
    cor_estrelas: tuple[int, int, int]
    cor_grade: tuple[int, int, int]
    tipo: str = "espiral"  # qual cenario desenhar (ver CENARIOS no fim do arquivo)


def _g(nome, fundo, nebulosa1, nebulosa2, principal, estrelas, grade, tipo="espiral"):
    return Galaxia(nome, fundo, (nebulosa1, nebulosa2), principal, estrelas, grade, tipo)


# tipos intercalados: cada setor novo tem um cenario diferente do anterior
GALAXIAS = [
    _g("VIA LACTEA", (9, 11, 16), (20, 70, 110), (40, 30, 90), (150, 200, 255), (120, 135, 155), (22, 28, 38)),
    _g("NEBULOSA DE ORION", (12, 8, 16), (150, 40, 90), (60, 40, 150), (255, 170, 200), (170, 140, 170),
       (34, 22, 38), "nebulosa"),
    _g("ANDROMEDA", (12, 8, 18), (110, 30, 120), (50, 30, 130), (240, 170, 255), (160, 130, 175), (32, 22, 40)),
    _g("PLEIADES", (6, 10, 18), (30, 60, 140), (20, 90, 150), (170, 210, 255), (130, 150, 190), (18, 26, 42),
       "aglomerado"),
    _g("KEPLER-22", (6, 12, 14), (20, 80, 90), (30, 50, 90), (90, 200, 190), (120, 150, 150), (16, 32, 34),
       "planeta"),
    _g("NUVEM DE MAGALHAES", (16, 10, 8), (150, 70, 20), (110, 30, 40), (255, 200, 140), (175, 145, 120),
       (40, 26, 20)),
    _g("SAGITARIO A*", (8, 6, 6), (90, 40, 20), (60, 20, 40), (255, 170, 90), (150, 120, 110), (30, 20, 18),
       "buraco_negro"),
    _g("CINTURAO DE KUIPER", (8, 10, 14), (40, 60, 90), (30, 40, 60), (150, 170, 200), (110, 120, 140),
       (22, 26, 34), "cinturao"),
    _g("TRIANGULO", (7, 14, 12), (20, 110, 80), (20, 70, 100), (160, 255, 210), (120, 160, 145), (18, 36, 30)),
    _g("NEBULOSA DO CARANGUEJO", (10, 8, 14), (150, 60, 30), (40, 90, 160), (255, 200, 150), (160, 140, 150),
       (32, 22, 30), "supernova"),
    _g("ALFA CENTAURI", (12, 10, 6), (120, 90, 20), (120, 50, 20), (255, 230, 170), (170, 155, 120),
       (36, 30, 18), "binaria"),
    _g("M87", (12, 10, 8), (110, 80, 40), (70, 50, 40), (255, 220, 170), (165, 150, 130), (34, 28, 22),
       "eliptica"),
    _g("SOMBRERO", (16, 8, 10), (140, 20, 40), (90, 20, 70), (255, 170, 160), (170, 125, 130), (40, 20, 24)),
    _g("NEBULOSA DA AGUIA", (8, 12, 10), (40, 120, 70), (140, 100, 40), (220, 255, 190), (140, 160, 135),
       (22, 34, 26), "nebulosa"),
    _g("OMEGA CENTAURI", (12, 10, 8), (120, 90, 40), (90, 60, 40), (255, 225, 170), (170, 155, 130),
       (34, 28, 20), "aglomerado"),
    _g("TRAPPIST-1", (14, 6, 6), (120, 30, 30), (90, 40, 20), (230, 110, 80), (165, 120, 110), (40, 18, 18),
       "planeta"),
    _g("REDEMOINHO", (8, 12, 18), (60, 120, 170), (140, 160, 190), (225, 240, 255), (150, 165, 185),
       (24, 32, 44)),
    _g("CYGNUS X-1", (6, 8, 14), (30, 60, 140), (80, 30, 120), (140, 190, 255), (120, 130, 170), (18, 22, 40),
       "buraco_negro"),
    _g("CINTURAO PRINCIPAL", (12, 10, 8), (90, 70, 40), (60, 50, 40), (210, 180, 140), (150, 140, 125),
       (32, 28, 22), "cinturao"),
    _g("BETELGEUSE", (16, 6, 4), (180, 50, 20), (140, 30, 30), (255, 140, 80), (180, 120, 100), (44, 18, 14),
       "supernova"),
    _g("CATAVENTO", (6, 10, 20), (20, 60, 160), (90, 40, 160), (140, 180, 255), (115, 130, 175), (18, 24, 44)),
    _g("SIRIUS", (6, 10, 18), (40, 80, 160), (60, 60, 140), (200, 225, 255), (140, 155, 185), (18, 26, 44),
       "binaria"),
    _g("MAFFEI 1", (14, 8, 10), (120, 50, 60), (90, 40, 70), (255, 190, 200), (170, 135, 145), (38, 22, 26),
       "eliptica"),
    _g("NEBULOSA DA HELICE", (6, 10, 14), (30, 110, 140), (150, 40, 60), (160, 240, 255), (130, 155, 165),
       (16, 30, 38), "nebulosa"),
    _g("GIRASSOL", (14, 13, 6), (140, 120, 20), (90, 110, 30), (255, 240, 150), (170, 165, 120), (36, 34, 18)),
    _g("AGLOMERADO DE HERCULES", (8, 8, 14), (60, 50, 120), (40, 70, 120), (210, 200, 255), (145, 140, 175),
       (24, 22, 40), "aglomerado"),
    _g("PROXIMA B", (10, 8, 14), (90, 40, 120), (40, 40, 100), (200, 140, 255), (150, 130, 170), (28, 22, 40),
       "planeta"),
    _g("CHARUTO", (18, 7, 7), (170, 40, 20), (150, 90, 30), (255, 150, 110), (180, 130, 115), (44, 20, 18)),
    _g("TON 618", (10, 6, 12), (120, 30, 100), (50, 20, 90), (255, 140, 230), (160, 120, 160), (34, 18, 36),
       "buraco_negro"),
    _g("NUVEM DE OORT", (6, 8, 12), (40, 50, 70), (30, 40, 70), (170, 190, 220), (110, 120, 140), (18, 22, 32),
       "cinturao"),
    _g("OLHO NEGRO", (5, 5, 8), (50, 50, 70), (80, 30, 50), (200, 190, 220), (110, 110, 125), (20, 20, 28)),
    _g("SN 1987A", (8, 6, 14), (80, 40, 160), (160, 40, 90), (230, 180, 255), (150, 130, 170), (26, 18, 40),
       "supernova"),
    _g("RODA DE CARRO", (6, 14, 16), (20, 120, 130), (120, 40, 110), (150, 255, 245), (125, 165, 165),
       (16, 36, 40)),
    _g("GRANDE ATRATOR", (4, 4, 6), (60, 60, 80), (90, 60, 30), (255, 240, 200), (140, 140, 150), (20, 20, 26),
       "buraco_negro"),  # setor 34: niveis 100-102 (o Imperador)
    _g("GIRINO", (10, 6, 16), (90, 20, 150), (20, 100, 150), (200, 160, 255), (145, 125, 175), (28, 18, 44)),
]


def indice_galaxia(nivel: int) -> int:
    """Nivel 1-3 -> 0, 4-6 -> 1, ... (cresce sem limite; depois do ultimo setor repete em ciclo)."""
    return (nivel - 1) // NIVEIS_POR_GALAXIA


def galaxia_do_indice(indice: int) -> Galaxia:
    return GALAXIAS[indice % len(GALAXIAS)]


# ---------------------------------------------------------------------------
# Renderizacao procedural
# ---------------------------------------------------------------------------
def _escurecer(cor, intensidade):
    return tuple(int(c * intensidade) for c in cor)


def _brilho_radial(tamanho, cor, intensidade_max, achatamento=1.0):
    """Disco com gradiente do centro (claro) para a borda (preto), para somar luz."""
    largura = max(2, int(tamanho * 2))
    altura = max(2, int(tamanho * 2 * achatamento))
    disco = pygame.Surface((largura, altura))
    passos = 16
    for passo in range(passos, 0, -1):
        fracao = passo / passos
        intensidade = intensidade_max * (1 - fracao) ** 1.6
        rect = pygame.Rect(0, 0, largura * fracao, altura * fracao)
        rect.center = (largura // 2, altura // 2)
        pygame.draw.ellipse(disco, _escurecer(cor, intensidade), rect)
    return disco


def _nebulosas(sorteio, galaxia):
    # desenha em baixa resolucao e amplia com suavizacao: gradientes macios e baratos;
    # as nuvens sao somadas (BLEND_RGB_ADD), como luz de verdade
    escala = 8
    pequena = pygame.Surface((LARGURA // escala, ALTURA // escala))
    for _ in range(8):
        cor = sorteio.choice(galaxia.cores_nebulosa)
        raio = sorteio.uniform(14, 36)
        nuvem = _brilho_radial(raio, cor, sorteio.uniform(0.22, 0.4), sorteio.uniform(0.5, 1.0))
        x = sorteio.uniform(0, pequena.get_width()) - nuvem.get_width() / 2
        y = sorteio.uniform(0, pequena.get_height()) - nuvem.get_height() / 2
        pequena.blit(nuvem, (x, y), special_flags=pygame.BLEND_RGB_ADD)
    return pygame.transform.smoothscale(pequena, (LARGURA, ALTURA))


def _espiral(sorteio, galaxia):
    camada = pygame.Surface((LARGURA, ALTURA))
    cx = sorteio.uniform(LARGURA * 0.2, LARGURA * 0.8)
    cy = sorteio.uniform(ALTURA * 0.25, ALTURA * 0.75)
    tamanho = sorteio.uniform(100, 160)
    inclinacao = sorteio.uniform(0.35, 0.6)  # achata a espiral (vista em perspectiva)
    giro = sorteio.uniform(0, 2 * math.pi)
    num_bracos = sorteio.choice([2, 2, 3])

    # halo difuso da galaxia inteira
    halo = _brilho_radial(tamanho * 1.1, galaxia.cor_espiral, 0.22, inclinacao)
    halo = pygame.transform.rotate(halo, -math.degrees(giro))
    camada.blit(halo, halo.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)

    # estrelas dos bracos espirais
    for _ in range(2600):
        braco = sorteio.randrange(num_bracos)
        t = sorteio.random() ** 0.7  # mais pontos perto do nucleo
        ang = t * 3.4 * math.pi + braco * (2 * math.pi / num_bracos)
        r = t * tamanho
        dispersao = 4 + 14 * t
        px = math.cos(ang) * r + sorteio.gauss(0, dispersao)
        py = (math.sin(ang) * r + sorteio.gauss(0, dispersao)) * inclinacao
        x = int(cx + px * math.cos(giro) - py * math.sin(giro))
        y = int(cy + px * math.sin(giro) + py * math.cos(giro))
        if 0 <= x < LARGURA and 0 <= y < ALTURA:
            cor = _escurecer(galaxia.cor_espiral, 0.9 * (1 - t) + 0.15)
            atual = camada.get_at((x, y))
            camada.set_at((x, y), tuple(min(255, a + c) for a, c in zip(atual[:3], cor)))

    # nucleo brilhante
    nucleo = _brilho_radial(tamanho * 0.28, galaxia.cor_espiral, 1.0, inclinacao)
    nucleo = pygame.transform.rotate(nucleo, -math.degrees(giro))
    camada.blit(nucleo, nucleo.get_rect(center=(cx, cy)), special_flags=pygame.BLEND_RGB_ADD)
    return camada


def _somar(fundo, camada):
    fundo.blit(camada, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


def _somar_ponto(camada, x, y, cor):
    x, y = int(x), int(y)
    if 0 <= x < LARGURA and 0 <= y < ALTURA:
        atual = camada.get_at((x, y))
        camada.set_at((x, y), tuple(min(255, a + c) for a, c in zip(atual[:3], cor)))


def _brilho_em(camada, cor, x, y, tamanho, intensidade, achatamento=1.0, giro=0.0):
    disco = _brilho_radial(tamanho, cor, intensidade, achatamento)
    if giro:
        disco = pygame.transform.rotate(disco, -math.degrees(giro))
    camada.blit(disco, disco.get_rect(center=(int(x), int(y))), special_flags=pygame.BLEND_RGB_ADD)


def _estrela_brilhante(camada, cor, x, y, tamanho):
    """Estrela com halo e cruz de difracao."""
    _brilho_em(camada, cor, x, y, tamanho, 0.9)
    for dx, dy in ((1, 0), (0, 1)):
        for passo in range(1, int(tamanho * 1.6)):
            intensidade = 0.6 * (1 - passo / (tamanho * 1.6))
            for sinal in (-1, 1):
                _somar_ponto(camada, x + dx * passo * sinal, y + dy * passo * sinal, _escurecer(cor, intensidade))


def _centro_sorteado(sorteio):
    return sorteio.uniform(LARGURA * 0.2, LARGURA * 0.8), sorteio.uniform(ALTURA * 0.25, ALTURA * 0.75)


# ------------------------------------------------------------------ cenarios
def _cenario_espiral(fundo, sorteio, galaxia):
    _somar(fundo, _espiral(sorteio, galaxia))


def _cenario_nebulosa(fundo, sorteio, galaxia):
    # nuvens densas e brilhantes no lugar da galaxia, com estrelas jovens dentro
    escala = 8
    pequena = pygame.Surface((LARGURA // escala, ALTURA // escala))
    cores = (*galaxia.cores_nebulosa, galaxia.cor_espiral)
    for _ in range(22):
        nuvem = _brilho_radial(
            sorteio.uniform(10, 30), sorteio.choice(cores), sorteio.uniform(0.25, 0.5), sorteio.uniform(0.4, 1.0)
        )
        nuvem = pygame.transform.rotate(nuvem, sorteio.uniform(0, 180))
        x = sorteio.gauss(pequena.get_width() / 2, pequena.get_width() / 4) - nuvem.get_width() / 2
        y = sorteio.gauss(pequena.get_height() / 2, pequena.get_height() / 4) - nuvem.get_height() / 2
        pequena.blit(nuvem, (x, y), special_flags=pygame.BLEND_RGB_ADD)
    _somar(fundo, pygame.transform.smoothscale(pequena, (LARGURA, ALTURA)))
    camada = pygame.Surface((LARGURA, ALTURA))
    for _ in range(6):
        _estrela_brilhante(camada, galaxia.cor_espiral, *_centro_sorteado(sorteio), sorteio.uniform(5, 10))
    _somar(fundo, camada)


def _cenario_aglomerado(fundo, sorteio, galaxia):
    camada = pygame.Surface((LARGURA, ALTURA))
    cx, cy = _centro_sorteado(sorteio)
    _brilho_em(camada, galaxia.cor_espiral, cx, cy, 130, 0.35)
    for _ in range(3500):
        dx, dy = sorteio.gauss(0, 75), sorteio.gauss(0, 75)
        perto = max(0.0, 1 - math.hypot(dx, dy) / 220)
        _somar_ponto(camada, cx + dx, cy + dy, _escurecer(galaxia.cor_espiral, 0.15 + 0.6 * perto))
    for _ in range(9):
        x, y = cx + sorteio.gauss(0, 60), cy + sorteio.gauss(0, 60)
        _estrela_brilhante(camada, galaxia.cor_espiral, x, y, sorteio.uniform(3, 7))
    _somar(fundo, camada)


def _cenario_eliptica(fundo, sorteio, galaxia):
    camada = pygame.Surface((LARGURA, ALTURA))
    cx, cy = _centro_sorteado(sorteio)
    giro = sorteio.uniform(0, math.pi)
    _brilho_em(camada, galaxia.cor_espiral, cx, cy, 230, 0.5, 0.62, giro)
    _brilho_em(camada, galaxia.cor_espiral, cx, cy, 70, 1.0, 0.7, giro)
    for _ in range(900):
        px, py = sorteio.gauss(0, 110), sorteio.gauss(0, 65)
        x = cx + px * math.cos(giro) - py * math.sin(giro)
        y = cy + px * math.sin(giro) + py * math.cos(giro)
        _somar_ponto(camada, x, y, _escurecer(galaxia.cor_espiral, 0.35))
    for _ in range(3):  # galaxias pequenas ao longe
        _brilho_em(camada, galaxia.cores_nebulosa[0], *_centro_sorteado(sorteio), 14, 0.8, 0.4, sorteio.uniform(0, 3))
    _somar(fundo, camada)


def _cenario_buraco_negro(fundo, sorteio, galaxia):
    cx, cy = _centro_sorteado(sorteio)
    giro = sorteio.uniform(-0.4, 0.4)
    raio_sombra = 50
    tras, frente = pygame.Surface((LARGURA, ALTURA)), pygame.Surface((LARGURA, ALTURA))
    _brilho_em(tras, galaxia.cor_espiral, cx, cy, 260, 0.25, 0.5, giro)
    for _ in range(7000):
        r = raio_sombra + 8 + sorteio.random() ** 1.8 * 200
        a = sorteio.uniform(0, 2 * math.pi)
        px, py = math.cos(a) * r, math.sin(a) * r * 0.26
        x = cx + px * math.cos(giro) - py * math.sin(giro)
        y = cy + px * math.sin(giro) + py * math.cos(giro)
        # mais quente perto do centro e mais claro do lado que "vem" na nossa direcao
        brilho = (1 - (r - raio_sombra) / 220) * (0.55 + 0.45 * math.cos(a))
        cor = _escurecer(galaxia.cor_espiral, 0.15 + 0.85 * max(0.0, brilho))
        _somar_ponto(tras if math.sin(a) < 0 else frente, x, y, cor)
    _somar(fundo, tras)
    pygame.draw.circle(fundo, (0, 0, 0), (int(cx), int(cy)), raio_sombra)
    pygame.draw.circle(fundo, galaxia.cor_espiral, (int(cx), int(cy)), raio_sombra + 2, 2)
    # luz curvada por cima da sombra (lente gravitacional)
    rect = pygame.Rect(0, 0, raio_sombra * 2 + 30, raio_sombra * 2 + 18)
    rect.center = (int(cx), int(cy))
    pygame.draw.arc(fundo, _escurecer(galaxia.cor_espiral, 0.6), rect, 0.2, math.pi - 0.2, 2)
    _somar(fundo, frente)


def _cenario_planeta(fundo, sorteio, galaxia):
    raio = sorteio.uniform(170, 230)
    # parcialmente fora da tela, em um dos cantos de baixo ou laterais
    cx = sorteio.choice((LARGURA * 0.1, LARGURA * 0.9))
    cy = sorteio.uniform(ALTURA * 0.75, ALTURA * 1.0)
    camada = pygame.Surface((LARGURA, ALTURA))
    _brilho_em(camada, galaxia.cor_espiral, cx, cy, raio * 1.35, 0.45)  # atmosfera
    _somar(fundo, camada)

    luz = (1 if cx < LARGURA / 2 else -1, -1)  # luz vindo do centro da tela, de cima
    passos = 40
    for k in range(passos):
        fracao = k / passos
        r = raio * (1 - fracao * 0.85)
        x = cx + luz[0] * raio * fracao * 0.45
        y = cy + luz[1] * raio * fracao * 0.45
        pygame.draw.circle(fundo, _escurecer(galaxia.cor_espiral, 0.12 + 0.55 * fracao ** 1.4), (int(x), int(y)), int(r))
    # faixas de nuvens: arcos finos e escuros
    for i in range(5):
        rect = pygame.Rect(0, 0, raio * 2, raio * (0.3 + 0.25 * i))
        rect.center = (int(cx), int(cy + sorteio.uniform(-raio * 0.5, raio * 0.5)))
        pygame.draw.arc(fundo, _escurecer(galaxia.cor_espiral, 0.2), rect, math.pi * 0.1, math.pi * 0.9, 1)

    # anel inclinado
    anel = pygame.Surface((int(raio * 3.2), int(raio * 0.9)), pygame.SRCALPHA)
    for k, largura in enumerate((3, 2, 1)):
        rect = anel.get_rect().inflate(-k * 22, -k * 8)
        pygame.draw.ellipse(anel, (*_escurecer(galaxia.cor_espiral, 0.75 - 0.15 * k), 220), rect, largura)
    anel = pygame.transform.rotate(anel, sorteio.uniform(-18, 18))
    fundo.blit(anel, anel.get_rect(center=(int(cx), int(cy))))

    # lua pequena
    lx, ly = cx - luz[0] * raio * 1.6, cy - raio * 1.25
    pygame.draw.circle(fundo, _escurecer(galaxia.cor_espiral, 0.35), (int(lx), int(ly)), 14)
    pygame.draw.circle(fundo, _escurecer(galaxia.cor_espiral, 0.65), (int(lx + luz[0] * 4), int(ly - 4)), 10)


def _cenario_cinturao(fundo, sorteio, galaxia):
    angulo = sorteio.uniform(-0.5, 0.5)
    cx, cy = LARGURA / 2, sorteio.uniform(ALTURA * 0.35, ALTURA * 0.65)
    dx, dy = math.cos(angulo), math.sin(angulo)
    camada = pygame.Surface((LARGURA, ALTURA))
    for _ in range(3000):  # poeira da faixa
        t, desvio = sorteio.uniform(-700, 700), sorteio.gauss(0, 45)
        _somar_ponto(camada, cx + dx * t - dy * desvio, cy + dy * t + dx * desvio,
                     _escurecer(galaxia.cor_espiral, 0.18))
    _somar(fundo, camada)
    for _ in range(240):  # rochas
        t, desvio = sorteio.uniform(-700, 700), sorteio.gauss(0, 55)
        x, y = cx + dx * t - dy * desvio, cy + dy * t + dx * desvio
        tamanho = sorteio.choice((1.5, 2, 2, 3, 3, 4, 6, 9))
        lados = sorteio.randint(5, 7)
        pontos = [
            (x + math.cos(2 * math.pi * i / lados) * tamanho * sorteio.uniform(0.7, 1.2),
             y + math.sin(2 * math.pi * i / lados) * tamanho * sorteio.uniform(0.7, 1.2))
            for i in range(lados)
        ]
        brilho = sorteio.uniform(0.15, 0.4)
        pygame.draw.polygon(fundo, _escurecer(galaxia.cor_espiral, brilho * 0.6), pontos)
        if tamanho >= 3:
            pygame.draw.aalines(fundo, _escurecer(galaxia.cor_espiral, brilho), True, pontos)


def _cenario_supernova(fundo, sorteio, galaxia):
    camada = pygame.Surface((LARGURA, ALTURA))
    cx, cy = _centro_sorteado(sorteio)
    _brilho_em(camada, galaxia.cor_espiral, cx, cy, 170, 0.3)
    # casca em expansao: filamentos nas cores da nebulosa
    for _ in range(2600):
        a = sorteio.uniform(0, 2 * math.pi)
        r = sorteio.gauss(130, 10) * (1 + 0.15 * math.sin(a * 5))
        cor = _escurecer(sorteio.choice(galaxia.cores_nebulosa), sorteio.uniform(0.5, 1.4))
        _somar_ponto(camada, cx + math.cos(a) * r, cy + math.sin(a) * r, tuple(min(255, c) for c in cor))
    # raios de luz
    for _ in range(36):
        a = sorteio.uniform(0, 2 * math.pi)
        comprimento = sorteio.uniform(60, 260)
        for passo in range(10, int(comprimento), 2):
            intensidade = 0.5 * (1 - passo / comprimento)
            _somar_ponto(camada, cx + math.cos(a) * passo, cy + math.sin(a) * passo,
                         _escurecer(galaxia.cor_espiral, intensidade))
    _estrela_brilhante(camada, (255, 255, 255), cx, cy, 14)
    _somar(fundo, camada)


def _cenario_binaria(fundo, sorteio, galaxia):
    camada = pygame.Surface((LARGURA, ALTURA))
    cx, cy = _centro_sorteado(sorteio)
    a = sorteio.uniform(0, math.pi)
    ax, ay = cx - math.cos(a) * 80, cy - math.sin(a) * 80
    bx, by = cx + math.cos(a) * 70, cy + math.sin(a) * 70
    _brilho_em(camada, galaxia.cor_espiral, ax, ay, 110, 0.9)
    _brilho_em(camada, galaxia.cores_nebulosa[0], bx, by, 70, 1.0)
    # gas sendo puxado da estrela menor para a maior
    for _ in range(1600):
        t = sorteio.random()
        curva = math.sin(t * math.pi) * 40
        x = bx + (ax - bx) * t - math.sin(a) * curva + sorteio.gauss(0, 4)
        y = by + (ay - by) * t + math.cos(a) * curva + sorteio.gauss(0, 4)
        _somar_ponto(camada, x, y, _escurecer(galaxia.cores_nebulosa[0], 0.5))
    _estrela_brilhante(camada, (255, 255, 255), ax, ay, 16)
    _estrela_brilhante(camada, (255, 255, 255), bx, by, 10)
    _somar(fundo, camada)


CENARIOS = {
    "espiral": _cenario_espiral,
    "nebulosa": _cenario_nebulosa,
    "aglomerado": _cenario_aglomerado,
    "eliptica": _cenario_eliptica,
    "buraco_negro": _cenario_buraco_negro,
    "planeta": _cenario_planeta,
    "cinturao": _cenario_cinturao,
    "supernova": _cenario_supernova,
    "binaria": _cenario_binaria,
}


def _grade(galaxia):
    camada = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    for x in range(0, LARGURA, ESPACAMENTO_GRADE):
        pygame.draw.line(camada, (*galaxia.cor_grade, 110), (x, 0), (x, ALTURA))
    for y in range(0, ALTURA, ESPACAMENTO_GRADE):
        pygame.draw.line(camada, (*galaxia.cor_grade, 110), (0, y), (LARGURA, y))
    # pequenas cruzes em algumas intersecoes: detalhe de "painel tecnico"
    for x in range(0, LARGURA, ESPACAMENTO_GRADE * 4):
        for y in range(0, ALTURA, ESPACAMENTO_GRADE * 4):
            cor = (*galaxia.cor_grade, 255)
            pygame.draw.line(camada, cor, (x - 4, y), (x + 4, y))
            pygame.draw.line(camada, cor, (x, y - 4), (x, y + 4))
    return camada


def renderizar_fundo(indice: int) -> pygame.Surface:
    """Gera o fundo da galaxia `indice` (deterministico: mesmo indice, mesmo fundo)."""
    galaxia = galaxia_do_indice(indice)
    sorteio = random.Random(indice)

    fundo = pygame.Surface((LARGURA, ALTURA))
    fundo.fill(galaxia.cor_fundo)
    _somar(fundo, _nebulosas(sorteio, galaxia))
    CENARIOS[galaxia.tipo](fundo, sorteio, galaxia)
    fundo.blit(_grade(galaxia), (0, 0))
    return fundo


class PlanoDeFundo:
    """Mantem o fundo atual e faz a transicao suave ao trocar de galaxia."""

    DURACAO_TRANSICAO = 90  # frames

    def __init__(self):
        self.indice: int = 0
        self.fundo: pygame.Surface = renderizar_fundo(0)
        self.fundo_anterior: pygame.Surface | None = None
        self.tempo_transicao: int = 0

    @property
    def galaxia(self) -> Galaxia:
        return galaxia_do_indice(self.indice)

    def ir_para(self, indice: int, com_transicao: bool = True) -> bool:
        """Troca a galaxia; retorna True se mudou."""
        if indice == self.indice:
            return False
        self.fundo_anterior = self.fundo if com_transicao else None
        self.indice = indice
        self.fundo = renderizar_fundo(indice)
        self.tempo_transicao = self.DURACAO_TRANSICAO if com_transicao else 0
        return True

    def atualizar(self):
        if self.tempo_transicao > 0:
            self.tempo_transicao -= 1
            if self.tempo_transicao == 0:
                self.fundo_anterior = None

    def desenhar(self, tela):
        if self.fundo_anterior is None:
            tela.blit(self.fundo, (0, 0))
            return
        progresso = 1 - self.tempo_transicao / self.DURACAO_TRANSICAO
        tela.blit(self.fundo_anterior, (0, 0))
        self.fundo.set_alpha(int(255 * progresso))
        tela.blit(self.fundo, (0, 0))
        self.fundo.set_alpha(None)
