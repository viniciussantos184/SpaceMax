"""Desenho de textos, HUD e telas de inicio / game over."""

import pygame

from .config import ALTURA, COR_TEXTO, COR_TEXTO_SOMBRA, COR_VIDA, LARGURA


def desenhar_texto(tela, fonte, texto, x, y, cor=COR_TEXTO, centralizado=True, sombra=True):
    if sombra:
        superficie_sombra = fonte.render(texto, True, COR_TEXTO_SOMBRA)
        rect_sombra = superficie_sombra.get_rect()
        if centralizado:
            rect_sombra.center = (x + 2, y + 2)
        else:
            rect_sombra.topleft = (x + 2, y + 2)
        tela.blit(superficie_sombra, rect_sombra)

    superficie = fonte.render(texto, True, cor)
    rect = superficie.get_rect()
    if centralizado:
        rect.center = (x, y)
    else:
        rect.topleft = (x, y)
    tela.blit(superficie, rect)


class Fontes:
    def __init__(self):
        self.titulo: pygame.font.Font = pygame.font.SysFont("arial", 54, bold=True)
        self.grande: pygame.font.Font = pygame.font.SysFont("arial", 36, bold=True)
        self.media: pygame.font.Font = pygame.font.SysFont("arial", 24)
        self.pequena: pygame.font.Font = pygame.font.SysFont("arial", 18)


def escurecer_tela(tela, opacidade):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, opacidade))
    tela.blit(overlay, (0, 0))


def desenhar_hud(tela, fontes, pontuacao, nivel, vidas, tempo_aviso_nivel):
    desenhar_texto(tela, fontes.grande, str(pontuacao), LARGURA / 2, 40)
    desenhar_texto(tela, fontes.pequena, f"Nivel {nivel}", LARGURA - 50, 30, cor=(200, 220, 255))

    for i in range(vidas):
        cx = 24 + i * 26
        cy = 30
        pygame.draw.polygon(
            tela,
            COR_VIDA,
            [(cx, cy - 10), (cx - 10, cy + 10), (cx, cy + 4), (cx + 10, cy + 10)],
        )

    if tempo_aviso_nivel > 0 and nivel > 1:
        alpha = min(255, int(255 * (tempo_aviso_nivel / 40)))
        superficie = fontes.titulo.render(f"NIVEL {nivel}", True, (255, 230, 120))
        superficie.set_alpha(alpha)
        rect = superficie.get_rect(center=(LARGURA / 2, ALTURA / 2 - 200))
        tela.blit(superficie, rect)


def desenhar_tela_inicio(tela, fontes, recorde):
    escurecer_tela(tela, 120)

    desenhar_texto(tela, fontes.titulo, "SpaceMax", LARGURA / 2, ALTURA / 2 - 140)
    desenhar_texto(
        tela, fontes.media, "Toque ESPACO ou clique para comecar", LARGURA / 2, ALTURA / 2 - 60
    )
    desenhar_texto(
        tela, fontes.pequena, "Setas/A-D: mover   ESPACO: atirar", LARGURA / 2, ALTURA / 2 - 20
    )
    desenhar_texto(
        tela,
        fontes.pequena,
        "Destrua os meteoros antes que colidam com sua nave",
        LARGURA / 2,
        ALTURA / 2 + 12,
    )
    desenhar_texto(tela, fontes.pequena, f"Recorde: {recorde}", LARGURA / 2, ALTURA / 2 + 50)


def desenhar_tela_gameover(tela, fontes, pontuacao, recorde):
    escurecer_tela(tela, 150)

    desenhar_texto(tela, fontes.titulo, "Game Over", LARGURA / 2, ALTURA / 2 - 100)
    desenhar_texto(tela, fontes.grande, f"Pontuacao: {pontuacao}", LARGURA / 2, ALTURA / 2 - 30)
    desenhar_texto(tela, fontes.media, f"Recorde: {recorde}", LARGURA / 2, ALTURA / 2 + 10)
    desenhar_texto(
        tela,
        fontes.pequena,
        "Toque ESPACO ou clique para jogar novamente",
        LARGURA / 2,
        ALTURA / 2 + 70,
    )
