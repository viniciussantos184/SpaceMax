"""
Planos de fundo: uma galaxia diferente a cada NIVEIS_POR_GALAXIA niveis.

Cada fundo e gerado proceduralmente uma unica vez (nebulosas suaves, uma
galaxia espiral distante e a grade tecnica) e depois so e copiado na tela.
"""

import math
import random
from dataclasses import dataclass

import pygame

from .config import ALTURA, LARGURA

NIVEIS_POR_GALAXIA = 10
ESPACAMENTO_GRADE = 48


@dataclass(frozen=True)
class Galaxia:
    nome: str
    cor_fundo: tuple[int, int, int]
    cores_nebulosa: tuple[tuple[int, int, int], tuple[int, int, int]]
    cor_espiral: tuple[int, int, int]
    cor_estrelas: tuple[int, int, int]
    cor_grade: tuple[int, int, int]


GALAXIAS = [
    Galaxia("VIA LACTEA", (9, 11, 16), ((20, 70, 110), (40, 30, 90)),
            (150, 200, 255), (120, 135, 155), (22, 28, 38)),
    Galaxia("ANDROMEDA", (12, 8, 18), ((110, 30, 120), (50, 30, 130)),
            (240, 170, 255), (160, 130, 175), (32, 22, 40)),
    Galaxia("NUVEM DE MAGALHAES", (16, 10, 8), ((150, 70, 20), (110, 30, 40)),
            (255, 200, 140), (175, 145, 120), (40, 26, 20)),
    Galaxia("TRIANGULO", (7, 14, 12), ((20, 110, 80), (20, 70, 100)),
            (160, 255, 210), (120, 160, 145), (18, 36, 30)),
    Galaxia("SOMBRERO", (16, 8, 10), ((140, 20, 40), (90, 20, 70)),
            (255, 170, 160), (170, 125, 130), (40, 20, 24)),
    Galaxia("REDEMOINHO", (8, 12, 18), ((60, 120, 170), (140, 160, 190)),
            (225, 240, 255), (150, 165, 185), (24, 32, 44)),
]


def indice_galaxia(nivel: int) -> int:
    """Nivel 1-10 -> 0, 11-20 -> 1, ... (cresce sem limite; o tema repete em ciclo)."""
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
    fundo.blit(_nebulosas(sorteio, galaxia), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    fundo.blit(_espiral(sorteio, galaxia), (0, 0), special_flags=pygame.BLEND_RGB_ADD)
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
