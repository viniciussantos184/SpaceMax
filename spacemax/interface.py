"""HUD, avisos e telas de inicio / game over (estilo tech minimalista)."""

import pygame

from . import grafico
from .config import (
    ALTURA,
    COR_APAGADA,
    COR_EXPLOSIVO,
    COR_FUNDO,
    COR_ITEM,
    COR_PERIGO,
    COR_PRIMARIA,
    COR_SECUNDARIA,
    LARGURA,
)
from .entidades.nave import CASCO
from .melhorias import LIMITE_MELHORIAS, POR_CHAVE, total_escolhidas

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


def desenhar_aviso(tela, fontes, subtitulo, titulo, tempo, duracao, cor=COR_PRIMARIA, y=ALTURA / 2 - 150):
    """Aviso central que aparece e some suavemente (nivel novo, galaxia nova, chefe)."""
    if tempo <= 0:
        return
    decorrido = duracao - tempo
    alpha = int(255 * min(1.0, decorrido / 20, tempo / 40))

    desenhar_texto(tela, fontes.pequena, espacar(subtitulo), LARGURA / 2, y - 26, COR_APAGADA, alpha=alpha)
    rect = desenhar_texto(tela, fontes.grande, espacar(titulo), LARGURA / 2, y, cor, alpha=alpha)

    # tracos laterais que "crescem" com o aviso
    largura_traco = int(60 * min(1.0, decorrido / 25))
    cor_traco = grafico.misturar(cor, alpha / 255 * 0.8)
    pygame.draw.line(tela, cor_traco, (rect.left - 16 - largura_traco, y), (rect.left - 16, y))
    pygame.draw.line(tela, cor_traco, (rect.right + 16, y), (rect.right + 16 + largura_traco, y))


def desenhar_barra_chefe(tela, fontes, numero, nome, fracao, cor):
    """Barra de vida do chefe: fina, segmentada em 10 partes, na base da tela."""
    largura, altura = 360, 6
    x, y = LARGURA / 2 - largura / 2, ALTURA - 44
    desenhar_texto(tela, fontes.pequena, f"CHEFE {numero:02d}  ·  {nome}", LARGURA / 2, y - 14, COR_APAGADA)
    pygame.draw.rect(tela, grafico.misturar(cor, 0.35), (x - 3, y - 3, largura + 6, altura + 6), 1)
    preenchido = int(largura * fracao)
    if preenchido > 0:
        pygame.draw.rect(tela, cor, (x, y, preenchido, altura))
    for i in range(1, 10):
        tx = x + largura * i / 10
        pygame.draw.line(tela, COR_FUNDO, (tx, y), (tx, y + altura - 1))


def desenhar_arma(tela, fontes, arma, explosiva, municao, municao_max, fracao_recarga):
    """Canto inferior esquerdo: arma atual, tiros explosivos e barra de recarga."""
    x, y = MARGEM, ALTURA - 72
    desenhar_texto(tela, fontes.pequena, "ARMA  [Q]", x, y, COR_APAGADA, "topleft")
    cor = COR_EXPLOSIVO if explosiva else COR_PRIMARIA
    desenhar_texto(tela, fontes.media, arma, x, y + 16, cor, "topleft")

    # municao explosiva: um circulo por tiro (cheio = disponivel)
    for i in range(municao_max):
        centro = (x + 6 + i * 18, y + 48)
        if i < municao:
            pygame.draw.circle(tela, COR_EXPLOSIVO, centro, 5)
        else:
            pygame.draw.circle(tela, grafico.misturar(COR_EXPLOSIVO, 0.4), centro, 5, 1)
    if municao < municao_max:
        bx, largura = x + municao_max * 18 + 6, 70
        pygame.draw.rect(tela, grafico.misturar(COR_EXPLOSIVO, 0.35), (bx, y + 45, largura, 6), 1)
        pygame.draw.rect(tela, COR_EXPLOSIVO, (bx + 1, y + 46, int((largura - 2) * fracao_recarga), 4))


# ---------------------------------------------------------------------------
# Telas
# ---------------------------------------------------------------------------
COLUNA_ACAO = LARGURA / 2 - 150  # alinhada a direita
COLUNA_TECLADO = LARGURA / 2 - 120
COLUNA_CONTROLE = LARGURA / 2 + 110

CONTROLES_INICIO = [
    ("GIRAR", "SETAS ESQ/DIR · A / D", "ANALOGICO · DIRECIONAL"),
    ("ACELERAR", "SETA CIMA · W", "CIMA · RT"),
    ("FREAR", "SETA BAIXO · S", "BAIXO · LT"),
    ("ATIRAR", "ESPACO · CLIQUE", "A · RB"),
    ("IMPULSO", "CONTROL", "B"),
    ("TROCAR ARMA", "Q · TAB", "X · Y · LB"),
    ("PAUSAR", "P · ENTER · ESC", "START"),
    ("TELA CHEIA", "F11 · ALT+ENTER", "Y (NOS MENUS)"),
    ("SAIR", "ESC", "SELECT (NO PAUSE)"),
]


def _tabela_controles(tela, fontes, y, linhas, espacamento=22):
    """Tabela ACAO | TECLADO | CONTROLE."""
    desenhar_texto(tela, fontes.pequena, espacar("TECLADO"), COLUNA_TECLADO, y, COR_PRIMARIA, "midleft")
    desenhar_texto(tela, fontes.pequena, espacar("CONTROLE"), COLUNA_CONTROLE, y, COR_PRIMARIA, "midleft")
    pygame.draw.line(
        tela, grafico.misturar(COR_APAGADA, 0.5), (COLUNA_ACAO - 110, y + 12), (COLUNA_CONTROLE + 200, y + 12)
    )
    for i, (acao, teclado, controle) in enumerate(linhas):
        ly = y + 30 + i * espacamento
        desenhar_texto(tela, fontes.pequena, acao, COLUNA_ACAO, ly, COR_APAGADA, "midright")
        desenhar_texto(tela, fontes.pequena, teclado, COLUNA_TECLADO, ly, COR_SECUNDARIA, "midleft")
        desenhar_texto(tela, fontes.pequena, controle, COLUNA_CONTROLE, ly, COR_SECUNDARIA, "midleft")


def _prompt_piscando(tela, fontes, texto, y, frame):
    if (frame // 30) % 2 == 0:
        desenhar_texto(tela, fontes.media, f"[  {texto}  ]", LARGURA / 2, y, COR_PRIMARIA)


def desenhar_tela_inicio(tela, fontes, recorde, frame, nome_controle=None):
    escurecer_tela(tela, 160)
    desenhar_cantoneiras(tela, COR_PRIMARIA, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.titulo, espacar("SPACEMAX"), LARGURA / 2, cy - 210, COR_SECUNDARIA)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - 150, cy - 168), (LARGURA / 2 + 150, cy - 168))
    desenhar_texto(
        tela, fontes.pequena, espacar("QUEBRE OS ASTEROIDES · SOBREVIVA"), LARGURA / 2, cy - 148,
        COR_APAGADA,
    )

    _tabela_controles(tela, fontes, cy - 115, CONTROLES_INICIO)

    _prompt_piscando(tela, fontes, "ESPACO / START PARA COMECAR", cy + 145, frame)
    desenhar_texto(tela, fontes.pequena, f"RECORDE  {recorde:06d}", LARGURA / 2, cy + 182, COR_APAGADA)
    if nome_controle:
        desenhar_texto(tela, fontes.pequena, f"CONTROLE CONECTADO: {nome_controle}", LARGURA / 2, cy + 204, COR_ITEM)
    else:
        desenhar_texto(tela, fontes.pequena, "NENHUM CONTROLE CONECTADO", LARGURA / 2, cy + 204, COR_APAGADA)


def desenhar_tela_pausa(tela, fontes, melhorias_nave, tela_cheia, frame):
    escurecer_tela(tela, 170)
    desenhar_cantoneiras(tela, COR_PRIMARIA, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.titulo, espacar("PAUSADO"), LARGURA / 2, cy - 150, COR_SECUNDARIA)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - 140, cy - 108), (LARGURA / 2 + 140, cy - 108))

    estado_tela = "LIGADA" if tela_cheia else "DESLIGADA"
    _tabela_controles(tela, fontes, cy - 80, [
        ("CONTINUAR", "P · ENTER", "START · B"),
        ("MENU INICIAL", "ESC", "SELECT"),
        (f"TELA CHEIA ({estado_tela})", "F11 · ALT+ENTER", "Y"),
    ])

    # melhorias ja escolhidas nesta partida
    titulo = f"MELHORIAS DA NAVE  {total_escolhidas(melhorias_nave)}/{LIMITE_MELHORIAS}"
    desenhar_texto(tela, fontes.pequena, espacar(titulo), LARGURA / 2, cy + 50, COR_PRIMARIA)
    itens = [f"{POR_CHAVE[c].nome} {n}" for c, n in melhorias_nave.items() if c in POR_CHAVE]
    if not itens:
        itens = ["NENHUMA AINDA · A CADA 6 NIVEIS E A CADA CHEFE DERROTADO"]
    for i in range(0, len(itens), 4):
        linha = "   ·   ".join(itens[i:i + 4])
        desenhar_texto(tela, fontes.pequena, linha, LARGURA / 2, cy + 76 + (i // 4) * 20, COR_SECUNDARIA)

    _prompt_piscando(tela, fontes, "P / START PARA CONTINUAR", cy + 170, frame)


# ---------------------------------------------------------------------------
# Escolha de melhoria (a cada nivel)
# ---------------------------------------------------------------------------
LARGURA_CARTA, ALTURA_CARTA, VAO_CARTA = 230, 180, 30
Y_CARTA = ALTURA / 2 - 70


def _retangulos_cartas(quantidade):
    total = quantidade * LARGURA_CARTA + (quantidade - 1) * VAO_CARTA
    x0 = (LARGURA - total) / 2
    return [
        pygame.Rect(int(x0 + i * (LARGURA_CARTA + VAO_CARTA)), int(Y_CARTA), LARGURA_CARTA, ALTURA_CARTA)
        for i in range(quantidade)
    ]


def carta_em(posicao, quantidade):
    """Indice da carta sob o mouse (ou None)."""
    for i, rect in enumerate(_retangulos_cartas(quantidade)):
        if rect.collidepoint(posicao):
            return i
    return None


def _quebrar(texto, limite):
    linhas, atual = [], ""
    for palavra in texto.split():
        if atual and len(atual) + 1 + len(palavra) > limite:
            linhas.append(atual)
            atual = palavra
        else:
            atual = f"{atual} {palavra}".strip()
    return linhas + [atual] if atual else linhas


def desenhar_tela_melhoria(tela, fontes, nivel, opcoes, niveis_atuais, selecionada, pronto):
    escurecer_tela(tela, 175)
    cy = ALTURA / 2
    numero = total_escolhidas(niveis_atuais) + 1
    desenhar_texto(
        tela, fontes.pequena, espacar(f"NIVEL {nivel:02d} · MELHORIA {numero}/{LIMITE_MELHORIAS}"),
        LARGURA / 2, cy - 160, COR_APAGADA,
    )
    desenhar_texto(tela, fontes.grande, espacar("ESCOLHA UMA MELHORIA"), LARGURA / 2, cy - 130, COR_PRIMARIA)

    for i, (melhoria, rect) in enumerate(zip(opcoes, _retangulos_cartas(len(opcoes)))):
        ativa = i == selecionada
        cor = COR_PRIMARIA if ativa else COR_APAGADA
        if ativa:
            fundo = pygame.Surface(rect.size, pygame.SRCALPHA)
            fundo.fill((*COR_PRIMARIA, 22))
            tela.blit(fundo, rect.topleft)
        pygame.draw.rect(tela, cor, rect, 2 if ativa else 1)

        desenhar_texto(tela, fontes.pequena, f"[{i + 1}]", rect.centerx, rect.top + 20, cor)
        desenhar_texto(
            tela, fontes.media, melhoria.nome, rect.centerx, rect.top + 52,
            COR_SECUNDARIA if ativa else COR_APAGADA,
        )
        for j, linha in enumerate(_quebrar(melhoria.descricao, 26)):
            desenhar_texto(tela, fontes.pequena, linha, rect.centerx, rect.top + 86 + j * 18, COR_SECUNDARIA)

        # nivel atual -> proximo (quadradinhos)
        atual = niveis_atuais.get(melhoria.chave, 0)
        if melhoria.nivel_max <= 5:
            tamanho, vao = 12, 6
            largura = melhoria.nivel_max * tamanho + (melhoria.nivel_max - 1) * vao
            x0 = rect.centerx - largura / 2
            for k in range(melhoria.nivel_max):
                quadrado = pygame.Rect(int(x0 + k * (tamanho + vao)), rect.bottom - 34, tamanho, tamanho)
                if k < atual:
                    pygame.draw.rect(tela, COR_PRIMARIA, quadrado)
                elif k == atual:
                    pygame.draw.rect(tela, COR_ITEM, quadrado, 0 if ativa else 1)
                else:
                    pygame.draw.rect(tela, COR_APAGADA, quadrado, 1)
        else:
            desenhar_texto(tela, fontes.pequena, "+1 VIDA", rect.centerx, rect.bottom - 28, COR_PERIGO)

    dica = "< >  ESCOLHER   ·   ENTER / A  CONFIRMAR   ·   1  2  3"
    desenhar_texto(
        tela, fontes.pequena, dica, LARGURA / 2, Y_CARTA + ALTURA_CARTA + 40,
        COR_SECUNDARIA if pronto else COR_APAGADA,
    )


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
    _prompt_piscando(tela, fontes, "ESPACO / START PARA JOGAR NOVAMENTE", cy + 90, frame)
