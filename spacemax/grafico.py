"""Primitivas de desenho vetorial (linhas finas com brilho)."""

import math

import pygame

from .config import COR_FUNDO


def misturar(cor, intensidade, fundo=COR_FUNDO):
    """Interpola `cor` com o fundo; intensidade 1 = cor pura, 0 = fundo."""
    return tuple(int(f + (c - f) * intensidade) for c, f in zip(cor, fundo))


def rotacionar(pontos, angulo, x, y):
    """Gira pontos locais (nariz apontando para cima) e desloca para (x, y)."""
    rad = math.radians(angulo)
    cos_a, sin_a = math.cos(rad), math.sin(rad)
    return [(x + px * cos_a - py * sin_a, y + px * sin_a + py * cos_a) for px, py in pontos]


def contorno(tela, cor, pontos, brilho=True):
    """Poligono so de contorno: halo largo e escuro + linha fina antialiased."""
    if brilho:
        pygame.draw.lines(tela, misturar(cor, 0.22), True, pontos, 4)
    pygame.draw.aalines(tela, cor, True, pontos)


def linha(tela, cor, inicio, fim, brilho=True):
    if brilho:
        pygame.draw.line(tela, misturar(cor, 0.25), inicio, fim, 4)
    pygame.draw.aaline(tela, cor, inicio, fim)


def circulo(tela, cor, centro, raio, largura=1):
    pygame.draw.circle(tela, cor, (int(centro[0]), int(centro[1])), int(raio), largura)
