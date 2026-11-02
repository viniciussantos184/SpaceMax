"""HUD, avisos e telas de inicio / game over (estilo tech minimalista)."""

from dataclasses import dataclass

import pygame

from . import grafico
from .config import (
    ALTURA,
    COR_APAGADA,
    COR_EXPLOSIVO,
    COR_FUNDO,
    COR_ITEM,
    COR_JOGADOR2,
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


@dataclass
class Placar:
    """O que o HUD mostra de cada jogador no multiplayer."""

    nome: str
    cor: tuple[int, int, int]
    rotulo: str
    valor: str
    vidas: int
    vivo: bool
    dica: str = ""


def desenhar_hud_multi(tela, fontes, placares, setor, nome_galaxia, nivel, centro):
    """HUD de dois jogadores: um em cada canto, informacoes da partida no centro.

    `centro`: linhas extras (texto, cor) abaixo do nivel (tempo, round, total da equipe)."""
    desenhar_cantoneiras(tela)
    for i, placar in enumerate(placares):
        direita = i == 1
        x = LARGURA - MARGEM if direita else MARGEM
        ancora = "topright" if direita else "topleft"
        desenhar_texto(tela, fontes.pequena, f"{placar.nome}  ·  {placar.rotulo}", x, 20, placar.cor, ancora)
        desenhar_texto(tela, fontes.grande, placar.valor, x, 34, ancora=ancora)
        if placar.vivo:
            for k in range(placar.vidas):
                desenhar_icone_nave(tela, x + (-(8 + k * 22) if direita else 8 + k * 22), 84, placar.cor)
        else:
            desenhar_texto(tela, fontes.pequena, "ELIMINADO", x, 76, COR_PERIGO, ancora)
            if placar.dica:
                desenhar_texto(tela, fontes.pequena, placar.dica, x, 94, COR_APAGADA, ancora)

    desenhar_texto(tela, fontes.pequena, f"SETOR {setor:02d}  ·  {nome_galaxia}", LARGURA / 2, 26, COR_APAGADA)
    desenhar_texto(tela, fontes.media, f"NIVEL {nivel:02d}", LARGURA / 2, 48, COR_PRIMARIA)
    for k, (texto, cor) in enumerate(centro):
        desenhar_texto(tela, fontes.pequena, texto, LARGURA / 2, 74 + k * 18, cor)


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


def desenhar_arma(
    tela, fontes, arma, explosiva, municao, municao_max, fracao_recarga,
    lado="esq", cor_nave=COR_PRIMARIA, tecla="Q",
):
    """Canto inferior (esquerdo ou direito): arma atual, tiros explosivos e barra de recarga."""
    direita = lado == "dir"
    x, y = (LARGURA - MARGEM if direita else MARGEM), ALTURA - 72
    ancora = "topright" if direita else "topleft"
    sinal = -1 if direita else 1
    desenhar_texto(tela, fontes.pequena, f"ARMA  [{tecla}]", x, y, COR_APAGADA, ancora)
    cor = COR_EXPLOSIVO if explosiva else cor_nave
    desenhar_texto(tela, fontes.media, arma, x, y + 16, cor, ancora)

    # municao explosiva: um circulo por tiro (cheio = disponivel)
    for i in range(municao_max):
        centro = (x + sinal * (6 + i * 18), y + 48)
        if i < municao:
            pygame.draw.circle(tela, COR_EXPLOSIVO, centro, 5)
        else:
            pygame.draw.circle(tela, grafico.misturar(COR_EXPLOSIVO, 0.4), centro, 5, 1)
    if municao < municao_max:
        largura = 70
        bx = x + municao_max * 18 + 6 if not direita else x - municao_max * 18 - 6 - largura
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


def desenhar_tela_inicio(tela, fontes, recorde, frame, nome_controle=None, dificuldade=""):
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

    _prompt_piscando(tela, fontes, "ESPACO / START PARA ESCOLHER O MODO", cy + 145, frame)
    rotulo = f"RECORDE {dificuldade}" if dificuldade else "RECORDE"
    desenhar_texto(tela, fontes.pequena, f"{rotulo}  {recorde:06d}", LARGURA / 2, cy + 182, COR_APAGADA)
    if nome_controle:
        desenhar_texto(tela, fontes.pequena, f"CONTROLE CONECTADO: {nome_controle}", LARGURA / 2, cy + 204, COR_ITEM)
    else:
        desenhar_texto(tela, fontes.pequena, "NENHUM CONTROLE CONECTADO", LARGURA / 2, cy + 204, COR_APAGADA)


def desenhar_tela_pausa(tela, fontes, listas, tela_cheia, frame):
    """`listas`: [(rotulo ou None, cor, melhorias)] com um item por jogador."""
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
    y = cy + 50
    for rotulo, cor, melhorias_nave in listas:
        titulo = f"MELHORIAS DA NAVE  {total_escolhidas(melhorias_nave)}/{LIMITE_MELHORIAS}"
        if rotulo:
            titulo = f"{rotulo}  ·  {titulo}"
        desenhar_texto(tela, fontes.pequena, espacar(titulo), LARGURA / 2, y, cor)
        itens = [f"{POR_CHAVE[c].nome} {n}" for c, n in melhorias_nave.items() if c in POR_CHAVE]
        if not itens:
            itens = ["NENHUMA AINDA · A CADA 6 NIVEIS E A CADA CHEFE DERROTADO"]
        por_linha = 4 if len(listas) == 1 else 3
        for i in range(0, len(itens), por_linha):
            linha = "   ·   ".join(itens[i:i + por_linha])
            desenhar_texto(tela, fontes.pequena, linha, LARGURA / 2, y + 26 + (i // por_linha) * 20, COR_SECUNDARIA)
        y += 26 + ((len(itens) - 1) // por_linha + 1) * 20 + 16

    _prompt_piscando(tela, fontes, "P / START PARA CONTINUAR", max(cy + 170, y + 24), frame)


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


def desenhar_tela_melhoria(tela, fontes, nivel, opcoes, niveis_atuais, selecionada, pronto, quem=None):
    """`quem`: (nome, cor) do jogador que escolhe, no multiplayer."""
    escurecer_tela(tela, 175)
    cy = ALTURA / 2
    if quem:
        desenhar_texto(tela, fontes.media, espacar(f"VEZ DO {quem[0]}"), LARGURA / 2, cy - 196, quem[1])
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


def desenhar_tela_nome(tela, fontes, rotulo, cor, pontos, nome, tamanho, frame, tem_proximo):
    """Pede o nome do jogador para o ranking."""
    escurecer_tela(tela, 170)
    desenhar_cantoneiras(tela, cor, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.pequena, espacar("RANKING"), LARGURA / 2, cy - 110, COR_APAGADA)
    desenhar_texto(tela, fontes.grande, espacar(rotulo), LARGURA / 2, cy - 78, cor)
    desenhar_texto(tela, fontes.media, f"{pontos:06d} PONTOS", LARGURA / 2, cy - 38, COR_SECUNDARIA)

    desenhar_texto(tela, fontes.pequena, espacar("DIGITE SEU NOME"), LARGURA / 2, cy + 6, COR_APAGADA)
    cursor = "_" if (frame // 30) % 2 == 0 else " "
    campo = f"{nome}{cursor}".ljust(tamanho + 1)
    desenhar_texto(tela, fontes.grande, campo, LARGURA / 2, cy + 40, COR_PRIMARIA)
    largura = 22 * (tamanho + 1)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - largura / 2, cy + 62), (LARGURA / 2 + largura / 2, cy + 62))

    confirmar = "ENTER PARA " + ("CONFIRMAR E PASSAR AO PROXIMO JOGADOR" if tem_proximo else "CONFIRMAR")
    desenhar_texto(tela, fontes.pequena, confirmar, LARGURA / 2, cy + 96, COR_SECUNDARIA)
    desenhar_texto(tela, fontes.pequena, "ESC PARA PULAR  ·  START / A MANTEM O NOME", LARGURA / 2, cy + 118, COR_APAGADA)


def desenhar_ranking(tela, fontes, linhas, y):
    """Top do ranking a partir de `y`. `linhas`: [(posicao, nome, pontos, e_desta_partida)]."""
    if not linhas:
        return
    desenhar_texto(tela, fontes.pequena, espacar("RANKING"), LARGURA / 2, y, COR_APAGADA)
    for k, (posicao, nome, pontos, atual) in enumerate(linhas):
        cor = COR_ITEM if atual else COR_SECUNDARIA
        desenhar_texto(tela, fontes.pequena, f"{posicao}.  {nome:<10}  {pontos:06d}", LARGURA / 2, y + 20 + k * 17, cor)


def desenhar_tela_gameover(
    tela, fontes, pontuacao, recorde, nivel, setor, novo_recorde, frame, dificuldade="", ranking=()
):
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
    if dificuldade:
        desenhar_texto(tela, fontes.pequena, f"DIFICULDADE  {dificuldade}", LARGURA / 2, cy + 46, COR_APAGADA)
    _prompt_piscando(tela, fontes, "ESPACO / START PARA JOGAR NOVAMENTE", cy + 90, frame)
    desenhar_texto(tela, fontes.pequena, "M / SELECT PARA ESCOLHER OUTRO MODO", LARGURA / 2, cy + 122, COR_APAGADA)
    desenhar_ranking(tela, fontes, ranking, cy + 160)


def desenhar_tela_fim_multi(tela, fontes, modo_nome, titulo, cor, colunas, rodape, frame, ranking=()):
    """Fim de partida com dois jogadores.

    `colunas`: [(nome, cor, [linhas])], uma por jogador; `rodape`: linhas extras abaixo."""
    escurecer_tela(tela, 170)
    desenhar_cantoneiras(tela, cor, tamanho=22)

    cy = ALTURA / 2
    desenhar_texto(tela, fontes.pequena, espacar(f"FIM DE JOGO  ·  {modo_nome}"), LARGURA / 2, cy - 150, COR_APAGADA)
    desenhar_texto(tela, fontes.grande, espacar(titulo), LARGURA / 2, cy - 115, cor)
    pygame.draw.line(tela, cor, (LARGURA / 2 - 220, cy - 85), (LARGURA / 2 + 220, cy - 85))

    for i, (nome, cor_jogador, linhas) in enumerate(colunas):
        x = LARGURA / 2 + (-1 if i == 0 else 1) * 170
        desenhar_texto(tela, fontes.media, nome, x, cy - 55, cor_jogador)
        for k, linha in enumerate(linhas):
            desenhar_texto(tela, fontes.pequena, linha, x, cy - 25 + k * 22, COR_SECUNDARIA)

    for k, linha in enumerate(rodape):
        desenhar_texto(tela, fontes.pequena, linha, LARGURA / 2, cy + 62 + k * 20, COR_APAGADA)

    _prompt_piscando(tela, fontes, "ESPACO / START PARA JOGAR NOVAMENTE", cy + 140, frame)
    desenhar_texto(tela, fontes.pequena, "M / SELECT PARA ESCOLHER OUTRO MODO", LARGURA / 2, cy + 172, COR_APAGADA)
    desenhar_ranking(tela, fontes, ranking, cy + 196)


# ---------------------------------------------------------------------------
# Escolha do modo de jogo
# ---------------------------------------------------------------------------
LARGURA_MODO, ALTURA_MODO, VAO_MODO, Y_MODOS = 620, 50, 6, 100
LARGURA_DIFICULDADE, ALTURA_DIFICULDADE, VAO_DIFICULDADE, Y_DIFICULDADE = 120, 26, 10, ALTURA - 96

CONTROLES_JOGADOR1 = "J1:  WASD GIRAR/ACELERAR/FREAR  ·  ESPACO TIRO  ·  CTRL-ESQ IMPULSO  ·  Q ARMA"
CONTROLES_JOGADOR2 = "J2:  SETAS GIRAR/ACELERAR/FREAR  ·  SHIFT-DIR TIRO  ·  CTRL-DIR IMPULSO  ·  / ARMA"
CONTROLES_SOLO = "SETAS OU WASD  ·  ESPACO TIRO  ·  CONTROL IMPULSO  ·  Q ARMA  ·  CLIQUE ATIRA"


def _retangulos_modos(quantidade):
    return [
        pygame.Rect(
            int((LARGURA - LARGURA_MODO) / 2), Y_MODOS + i * (ALTURA_MODO + VAO_MODO), LARGURA_MODO, ALTURA_MODO
        )
        for i in range(quantidade)
    ]


def _retangulos_dificuldades(quantidade):
    total = quantidade * LARGURA_DIFICULDADE + (quantidade - 1) * VAO_DIFICULDADE
    x0 = int(LARGURA / 2 + 60 - total / 2)  # deslocado para a direita: o rotulo fica a esquerda
    return [
        pygame.Rect(x0 + i * (LARGURA_DIFICULDADE + VAO_DIFICULDADE), Y_DIFICULDADE, LARGURA_DIFICULDADE, ALTURA_DIFICULDADE)
        for i in range(quantidade)
    ]


def dificuldade_em(posicao, quantidade):
    """Indice da dificuldade sob o mouse (ou None)."""
    for i, rect in enumerate(_retangulos_dificuldades(quantidade)):
        if rect.collidepoint(posicao):
            return i
    return None


def modo_em(posicao, quantidade):
    """Indice do modo sob o mouse (ou None)."""
    for i, rect in enumerate(_retangulos_modos(quantidade)):
        if rect.collidepoint(posicao):
            return i
    return None


def desenhar_tela_modos(tela, fontes, modos, selecionado, quantidade_controles, dificuldades, dificuldade):
    escurecer_tela(tela, 175)
    desenhar_cantoneiras(tela, COR_PRIMARIA, tamanho=22)

    desenhar_texto(tela, fontes.grande, espacar("ESCOLHA O MODO"), LARGURA / 2, 52, COR_SECUNDARIA)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - 150, 78), (LARGURA / 2 + 150, 78))

    for i, (modo, rect) in enumerate(zip(modos, _retangulos_modos(len(modos)))):
        ativo = i == selecionado
        cor = COR_PRIMARIA if ativo else COR_APAGADA
        if ativo:
            fundo = pygame.Surface(rect.size, pygame.SRCALPHA)
            fundo.fill((*COR_PRIMARIA, 22))
            tela.blit(fundo, rect.topleft)
        pygame.draw.rect(tela, cor, rect, 2 if ativo else 1)
        desenhar_texto(tela, fontes.pequena, f"[{i + 1}]", rect.left + 26, rect.centery, cor)
        desenhar_texto(
            tela, fontes.media, espacar(modo.nome), rect.left + 54, rect.top + 15,
            COR_SECUNDARIA if ativo else COR_APAGADA, "midleft",
        )
        desenhar_texto(tela, fontes.pequena, modo.resumo, rect.left + 54, rect.top + 36, COR_APAGADA, "midleft")
        desenhar_texto(
            tela, fontes.pequena, f"{modo.jogadores}P", rect.right - 20, rect.centery,
            COR_ITEM if modo.multi else COR_APAGADA, "midright",
        )

    modo = modos[selecionado]
    y = Y_MODOS + len(modos) * (ALTURA_MODO + VAO_MODO) + 18
    for k, linha in enumerate(modo.regras):
        desenhar_texto(tela, fontes.pequena, linha, LARGURA / 2, y + k * 18, COR_SECUNDARIA)
    y += len(modo.regras) * 18 + 14
    if modo.multi:
        desenhar_texto(tela, fontes.pequena, CONTROLES_JOGADOR1, LARGURA / 2, y, COR_PRIMARIA)
        desenhar_texto(tela, fontes.pequena, CONTROLES_JOGADOR2, LARGURA / 2, y + 18, COR_JOGADOR2)
        if quantidade_controles:
            texto = f"CONTROLES CONECTADOS: {quantidade_controles}  ·  NA PROXIMA TELA CADA UM ESCOLHE TECLADO OU CONTROLE"
        else:
            texto = "NENHUM CONTROLE CONECTADO  ·  DA PARA JOGAR OS DOIS NO MESMO TECLADO OU COM CONTROLES"
        desenhar_texto(
            tela, fontes.pequena, texto, LARGURA / 2, y + 40, COR_ITEM if quantidade_controles else COR_APAGADA
        )
    else:
        desenhar_texto(tela, fontes.pequena, CONTROLES_SOLO, LARGURA / 2, y, COR_PRIMARIA)

    retangulos = _retangulos_dificuldades(len(dificuldades))
    desenhar_texto(
        tela, fontes.pequena, espacar("DIFICULDADE"), retangulos[0].left - 18, retangulos[0].centery,
        COR_SECUNDARIA, "midright",
    )
    for i, (opcao, rect) in enumerate(zip(dificuldades, retangulos)):
        ativa = i == dificuldade
        cor = COR_ITEM if ativa else COR_APAGADA
        if ativa:
            fundo = pygame.Surface(rect.size, pygame.SRCALPHA)
            fundo.fill((*COR_ITEM, 26))
            tela.blit(fundo, rect.topleft)
        pygame.draw.rect(tela, cor, rect, 2 if ativa else 1)
        desenhar_texto(tela, fontes.pequena, espacar(opcao.nome), rect.centerx, rect.centery, cor)
    desenhar_texto(
        tela, fontes.pequena, dificuldades[dificuldade].resumo, LARGURA / 2, Y_DIFICULDADE + ALTURA_DIFICULDADE + 14,
        COR_APAGADA,
    )

    desenhar_texto(
        tela, fontes.pequena,
        "CIMA / BAIXO MODO   ·   ESQ / DIR DIFICULDADE   ·   ENTER / ESPACO / A CONFIRMAR   ·   ESC / B VOLTAR",
        LARGURA / 2, ALTURA - 26, COR_APAGADA,
    )


# ---------------------------------------------------------------------------
# Escolha dos jogadores (multiplayer): cada um entra com seu controle ou teclado
# ---------------------------------------------------------------------------
LARGURA_PAINEL, ALTURA_PAINEL, Y_PAINEL = 360, 210, 120


def desenhar_tela_jogadores(tela, fontes, modo_nome, vagas, controles_livres, frame):
    """`vagas`: dispositivo de cada jogador (None = vazia); `controles_livres`: nomes dos controles
    conectados que ainda nao entraram."""
    escurecer_tela(tela, 175)
    desenhar_cantoneiras(tela, COR_PRIMARIA, tamanho=22)

    desenhar_texto(tela, fontes.grande, espacar("ESCOLHA OS JOGADORES"), LARGURA / 2, 52, COR_SECUNDARIA)
    pygame.draw.line(tela, COR_PRIMARIA, (LARGURA / 2 - 150, 78), (LARGURA / 2 + 150, 78))
    desenhar_texto(tela, fontes.pequena, espacar(modo_nome), LARGURA / 2, 96, COR_APAGADA)

    cores = (COR_PRIMARIA, COR_JOGADOR2)
    for i, (vaga, cor) in enumerate(zip(vagas, cores)):
        cx = LARGURA / 2 + (-1 if i == 0 else 1) * 200
        rect = pygame.Rect(0, Y_PAINEL, LARGURA_PAINEL, ALTURA_PAINEL)
        rect.centerx = int(cx)
        ocupada = vaga is not None
        pygame.draw.rect(tela, cor if ocupada else COR_APAGADA, rect, 2 if ocupada else 1)
        if ocupada:
            fundo = pygame.Surface(rect.size, pygame.SRCALPHA)
            fundo.fill((*cor, 20))
            tela.blit(fundo, rect.topleft)

        desenhar_icone_nave(tela, cx, rect.top + 56, cor if ocupada else COR_APAGADA, escala=1.6)
        desenhar_texto(tela, fontes.media, espacar(f"JOGADOR {i + 1}"), cx, rect.top + 108, cor if ocupada else COR_APAGADA)
        if ocupada:
            desenhar_texto(tela, fontes.pequena, vaga.nome[:38], cx, rect.top + 140, COR_SECUNDARIA)
            desenhar_texto(tela, fontes.media, espacar("PRONTO"), cx, rect.top + 172, cor)
        elif (frame // 30) % 2 == 0:
            desenhar_texto(tela, fontes.pequena, "APERTE  A  (CONTROLE)", cx, rect.top + 146, COR_SECUNDARIA)
            desenhar_texto(tela, fontes.pequena, "ESPACO / SHIFT-DIR  (TECLADO)", cx, rect.top + 168, COR_APAGADA)

    y = Y_PAINEL + ALTURA_PAINEL + 30
    ajuda = [
        ("CONTROLE", "A ENTRA   ·   DIRECIONAL ESQ / DIR ESCOLHE J1 OU J2   ·   B SAI", COR_ITEM),
        ("TECLADO  WASD", "ESPACO ENTRA   ·   A / D ESCOLHE J1 OU J2   ·   S SAI", COR_PRIMARIA),
        ("TECLADO  SETAS", "SHIFT-DIR ENTRA   ·   SETA ESQ / DIR ESCOLHE J1 OU J2   ·   SETA BAIXO SAI", COR_JOGADOR2),
    ]
    for k, (rotulo, texto, cor) in enumerate(ajuda):
        desenhar_texto(tela, fontes.pequena, rotulo, LARGURA / 2 - 300, y + k * 22, cor, "midleft")
        desenhar_texto(tela, fontes.pequena, texto, LARGURA / 2 - 170, y + k * 22, COR_SECUNDARIA, "midleft")

    if controles_livres:
        texto = "CONTROLES CONECTADOS: " + "  ·  ".join(nome[:24] for nome in controles_livres)
    elif any(vaga is not None and vaga.controle is not None for vaga in vagas):
        texto = "CONTROLES CONECTADOS JA ESTAO NA PARTIDA"
    else:
        texto = "NENHUM CONTROLE CONECTADO  ·  CONECTE POR USB / BLUETOOTH"
    desenhar_texto(tela, fontes.pequena, texto, LARGURA / 2, y + 90, COR_ITEM if controles_livres else COR_APAGADA)

    if all(vaga is not None for vaga in vagas):
        _prompt_piscando(tela, fontes, "ENTER / START PARA COMECAR", ALTURA - 76, frame)
    else:
        desenhar_texto(tela, fontes.media, "AGUARDANDO OS DOIS JOGADORES", LARGURA / 2, ALTURA - 76, COR_APAGADA)
    desenhar_texto(tela, fontes.pequena, "ESC / B VOLTAR", LARGURA / 2, ALTURA - 34, COR_APAGADA)
