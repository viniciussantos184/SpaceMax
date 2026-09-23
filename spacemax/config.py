"""Configuracoes gerais do jogo (tela, cores, velocidades, dificuldade)."""

import os

# ---------------------------------------------------------------------------
# Tela
# ---------------------------------------------------------------------------
LARGURA, ALTURA = 480, 720
FPS = 60

# ---------------------------------------------------------------------------
# Cores
# ---------------------------------------------------------------------------
COR_FUNDO = (8, 10, 30)
COR_ESTRELA = (255, 255, 255)
COR_NAVE = (60, 200, 255)
COR_NAVE_BORDA = (255, 255, 255)
COR_METEORO = (150, 110, 90)
COR_METEORO_BORDA = (90, 60, 45)
COR_TIRO = (255, 230, 90)
COR_TEXTO = (255, 255, 255)
COR_TEXTO_SOMBRA = (0, 0, 0)
COR_ITEM = (255, 215, 60)
COR_VIDA = (255, 90, 90)

# ---------------------------------------------------------------------------
# Jogador
# ---------------------------------------------------------------------------
VELOCIDADE_NAVE = 6.5
VELOCIDADE_TIRO = 11
COOLDOWN_TIRO = 14  # frames entre disparos

VIDAS_INICIAIS = 3

# ---------------------------------------------------------------------------
# Dificuldade
# ---------------------------------------------------------------------------
PONTOS_POR_NIVEL = 8  # a cada N pontos o jogador sobe de nivel

VELOCIDADE_METEORO_MIN_INICIAL = 2.0
VELOCIDADE_METEORO_MAX_INICIAL = 3.5
AUMENTO_VELOCIDADE_POR_NIVEL = 0.35
VELOCIDADE_METEORO_TETO = 9.5

INTERVALO_SPAWN_INICIAL = 65  # frames entre meteoros
INTERVALO_SPAWN_MINIMO = 16
REDUCAO_SPAWN_POR_NIVEL = 6

DURACAO_AVISO_NIVEL = 120  # frames que o aviso "NIVEL X" fica visivel

# ---------------------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------------------
PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_RECORDE = os.path.join(PASTA_PROJETO, "recorde.txt")

# ---------------------------------------------------------------------------
# Estados do jogo
# ---------------------------------------------------------------------------
ESTADO_INICIO = "inicio"
ESTADO_JOGANDO = "jogando"
ESTADO_GAMEOVER = "gameover"
