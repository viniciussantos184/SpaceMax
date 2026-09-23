"""HUD, avisos e telas de inicio / game over (estilo tech minimalista)."""

import pygame

from . import grafico
from .config import (
    ALTURA,
    COR_APAGADA,
    COR_FUNDO,
    COR_ITEM,
    COR_PERIGO,
    COR_PRIMARIA,
    COR_SECUNDARIA,
    LARGURA,
)
from .entidades.nave import CASCO

FONTES_MONO = "consolas,menlo,dejavusansmono,liberationmono,couriernew"
MARGEM = 24


class Fontes:
    def __init__(self):
        self.titulo: pygame.font.Font = pygame.font.SysFont(FONTES_MONO, 56, bold=True)
        self.grande: pygame.font.Font = pygame.font.SysFont(FONTES_MONO, 30, bold=True)
        self.media: pygame.font.Font = pygame.font.SysFont(FONTES_MONO, 18)
        self.pequena: pygame.font.Font = pygame.font.SysFont(FONTES_MONO, 13)


def espacar(texto):
    """Espacamento entre letras, tipico de interfaces tecnicas: 'ABC' -> 'A B C'."""
    return " ".join(texto)


def desenhar_texto(tela, fonte, texto, x, y, cor=COR_SECUNDARIA, ancora="center", alpha=255):
    superficie = fonte.render(texto, True, cor)
    if alpha < 255:
        superficie.set_alpha(alpha)
    rect = superficie.get_rect(**{ancora: (int(x), int(y))})
    tela.blit(superficie, rect)
    return rect


def escurecer_tela(tela, opacidade):
    overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
    overlay.fill((*COR_FUNDO, opacidade))
    tela.blit(overlay, (0, 0))


def desenhar_cantoneiras(tela, cor=COR_APAGADA, tamanho=14, recuo=10):
    """Moldura em 'L' nos quatro cantos da tela."""
    for cx, sx in ((recuo, 1), (LARGURA - recuo - 1, -1)):
        for cy, sy in ((recuo, 1), (ALTURA - recuo - 1, -1)):
            pygame.draw.line(tela, cor, (cx, cy), (cx + sx * tamanho, cy))
            pygame.draw.line(tela, cor, (cx, cy), (cx, cy + sy * tamanho))


def desenhar_icone_nave(tela, x, y, cor, escala=0.55):
    pontos = [(px * escala, py * escala) for px, py in CASCO]
    pygame.draw.aalines(tela, cor, True, grafico.rotacionar(pontos, 0, x, y))


# ---------------------------------------------------------------------------
# HUD
# ---------------------------------------------------------------------------
def desenhar_hud(tela, fontes, pontuacao, recorde, nivel, vidas, setor, nome_galaxia):
    desenhar_cantoneiras(tela)

    # esquerda: pontos + vidas
    desenhar_texto(tela, fontes.pequena, "PONTOS", MARGEM, 20, COR_APAGADA, "topleft")
    desenhar_texto(tela, fontes.grande, f"{pontuacao:06d}", MARGEM, 34, ancora="topleft")
    for i in range(vidas):
        desenhar_icone_nave(tela, MARGEM + 8 + i * 22, 84, COR_PRIMARIA)

    # centro: setor / galaxia + nivel
    desenhar_texto(
        tela, fontes.pequena, f"SETOR {setor:02d}  ·  {nome_galaxia}", LARGURA / 2, 26, COR_APAGADA
    )
    desenhar_texto(tela, fontes.media, f"NIVEL {nivel:02d}", LARGURA / 2, 48, COR_PRIMARIA)

    # direita: recorde
    desenhar_texto(tela, fontes.pequena, "RECORDE", LARGURA - MARGEM, 20, COR_APAGADA, "topright")
    desenhar_texto(
        tela, fontes.grande, f"{recorde:06d}", LARGURA - MARGEM, 34, COR_APAGADA, "topright"
    )


def desenhar_aviso(tela, fontes, subtitulo, titulo, tempo, duracao, cor=COR_PRIMARIA):
    """Aviso central que aparece e some suavemente (nivel novo, galaxia nova)."""
    if tempo <= 0:
        return
    decorrido = duracao - tempo
    alpha = int(255 * min(1.0, decorrido / 20, tempo / 40))
    y = ALTURA / 2 - 150

    desenhar_texto(tela, fontes.pequena, espacar(subtitulo), LARGURA / 2, y - 26, COR_APAGADA, alpha=alpha)
    rect = desenhar_texto(tela, fontes.grande, espacar(titulo), LARGURA / 2, y, cor, alpha=alpha)

    # tracos laterais que "crescem" com o aviso
    largura_traco = int(60 * min(1.0, decorrido / 25))
    cor_traco = grafico.misturar(cor, alpha / 255 * 0.8)
    pygame.draw.line(tela, cor_traco, (rect.left - 16 - largura_traco, y), (rect.left - 16, y))
    pygame.draw.line(tela, cor_traco, (rect.right + 16, y), (rect.right + 16 + largura_traco, y))


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------
def _linha_controle(tela, fontes, y, acao, teclas):
    desenhar_texto(tela, fontes.pequena, acao, LARGURA / 2 - 20, y, COR_APAGADA, "midright")
    desenhar_texto(tela, fontes.pequena, teclas, LARGURA / 2 + 20, y, COR_SECUNDARIA, "midleft")


def _prompt_piscando(tela, fontes, texto, y, frame):
    if (frame // 30) % 2 == 0:
        desenhar_texto(tela, fontes.media, f"[  {texto}  ]", LARGURA / 2, y, COR_PRIMARIA)


def desenhar_tela_inicio(tela, fontes, recorde, frame):
    escurecer_tela(tela, 150)
    desenhar_cantoneiras(tela, COR_PRIMARIA, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.titulo, espacar("SPACEMAX"), LARGURA / 2, cy - 150, COR_SECUNDARIA)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - 150, cy - 108), (LARGURA / 2 + 150, cy - 108))
    desenhar_texto(
        tela, fontes.pequena, espacar("QUEBRE OS ASTEROIDES · SOBREVIVA"), LARGURA / 2, cy - 88,
        COR_APAGADA,
    )

    controles = [
        ("GIRAR", "SETAS ESQ/DIR  ou  A / D"),
        ("ACELERAR", "SETA CIMA  ou  W"),
        ("FREAR", "SETA BAIXO  ou  S"),
        ("IMPULSO", "CONTROL"),
        ("ATIRAR", "ESPACO"),
        ("SAIR", "ESC"),
    ]
    for i, (acao, teclas) in enumerate(controles):
        _linha_controle(tela, fontes, cy - 40 + i * 22, acao, teclas)

    _prompt_piscando(tela, fontes, "PRESSIONE ESPACO", cy + 108, frame)
    desenhar_texto(tela, fontes.pequena, f"RECORDE  {recorde:06d}", LARGURA / 2, cy + 150, COR_APAGADA)


def desenhar_tela_gameover(tela, fontes, pontuacao, recorde, nivel, setor, novo_recorde, frame):
    escurecer_tela(tela, 170)
    desenhar_cantoneiras(tela, COR_PERIGO, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.titulo, espacar("FIM DE JOGO"), LARGURA / 2, cy - 130, COR_PERIGO)
    pygame.draw.line(tela, COR_PERIGO, (LARGURA / 2 - 170, cy - 88), (LARGURA / 2 + 170, cy - 88))

    desenhar_texto(tela, fontes.pequena, "PONTOS", LARGURA / 2, cy - 55, COR_APAGADA)
    desenhar_texto(tela, fontes.grande, f"{pontuacao:06d}", LARGURA / 2, cy - 30)
    if novo_recorde:
        desenhar_texto(tela, fontes.pequena, espacar("NOVO RECORDE"), LARGURA / 2, cy - 2, COR_ITEM)
    else:
        desenhar_texto(tela, fontes.pequena, f"RECORDE  {recorde:06d}", LARGURA / 2, cy - 2, COR_APAGADA)

    desenhar_texto(
        tela, fontes.pequena, f"NIVEL {nivel:02d}   ·   SETOR {setor:02d}", LARGURA / 2, cy + 24,
        COR_APAGADA,
    )
    _prompt_piscando(tela, fontes, "ESPACO PARA JOGAR NOVAMENTE", cy + 90, frame)
