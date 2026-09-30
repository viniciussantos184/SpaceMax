"""Configuracoes gerais do jogo (tela, paleta, fisica, dificuldade)."""

import os

# ---------------------------------------------------------------------------
# Tela
# ---------------------------------------------------------------------------
LARGURA, ALTURA = 960, 640
FPS = 60

# ---------------------------------------------------------------------------
# Paleta tech minimalista
# ---------------------------------------------------------------------------
COR_FUNDO = (9, 11, 16)
COR_GRADE = (18, 22, 30)
COR_ESTRELA = (70, 80, 95)
COR_PRIMARIA = (92, 225, 230)  # ciano: nave, tiros, destaques
COR_SECUNDARIA = (235, 240, 245)  # branco suave: textos principais
COR_APAGADA = (95, 105, 120)  # cinza: rotulos e textos secundarios
COR_ASTEROIDE = (170, 178, 190)
COR_PERIGO = (255, 84, 112)  # vermelho: vidas, colisao
COR_ITEM = (255, 200, 87)  # ambar: escudo
COR_CHAMA = (255, 150, 70)
COR_EXPLOSIVO = (255, 110, 50)  # laranja: tiro explosivo

# ---------------------------------------------------------------------------
# Nave
# ---------------------------------------------------------------------------
ROTACAO_MAX_NAVE = 5.6  # graus por frame (velocidade maxima de giro)
ACELERACAO_ROTACAO = 0.85  # quanto o giro ganha por frame segurando a tecla
AMORTECIMENTO_ROTACAO = 0.55  # ao soltar, o giro para rapido (sem "patinar")

ACELERACAO_NAVE = 0.24
RAMPA_PROPULSOR = 0.14  # potencia do motor sobe de 0 a 1 em ~7 frames
FREIO_NAVE = 0.9  # multiplicador de velocidade ao frear
ATRITO_NAVE = 0.987  # arrasto: a nave desliza, mas continua controlavel
VELOCIDADE_MAX_NAVE = 8.0

IMPULSO_DASH = 7.5  # velocidade extra do impulso (CONTROL, sem recarga)
VELOCIDADE_MAX_DASH = 13.0  # limite de velocidade logo apos o impulso
DURACAO_DASH = 14  # frames em que o limite de velocidade fica mais alto

VELOCIDADE_TIRO = 10.5
ALCANCE_TIRO = 52  # frames de vida do tiro
COOLDOWN_TIRO = 9  # frames entre disparos

# arma explosiva (troca com Q / TAB): poucos tiros, recarga lenta
ARMA_NORMAL, ARMA_EXPLOSIVA = "NORMAL", "EXPLOSIVA"
MUNICAO_EXPLOSIVA = 3
RECARGA_EXPLOSIVA = 30 * FPS  # 30 s para recarregar os 3 tiros
COOLDOWN_TIRO_EXPLOSIVO = 30
VELOCIDADE_TIRO_EXPLOSIVO = 7.5
ALCANCE_TIRO_EXPLOSIVO = 70  # frames; explode sozinho ao fim do alcance
RAIO_EXPLOSAO = 95
DANO_EXPLOSAO_CHEFE = 6

VIDAS_INICIAIS = 5
VIDAS_MAXIMAS = 5
PONTOS_POR_VIDA = 1000  # uma vida extra a cada 1000 pontos (ate VIDAS_MAXIMAS)
DURACAO_INVENCIVEL = 2 * FPS  # apos ser atingido
DURACAO_ESCUDO = 6 * FPS  # item de escudo
INTERVALO_ESCUDO = (6 * FPS, 10 * FPS)  # um escudo novo a cada 6-10 s
MAX_ESCUDOS_NA_TELA = 2

# ---------------------------------------------------------------------------
# Asteroides: tamanho -> (raio, pontos, multiplicador de velocidade)
# ---------------------------------------------------------------------------
ASTEROIDE_GRANDE, ASTEROIDE_MEDIO, ASTEROIDE_PEQUENO = 3, 2, 1
DADOS_ASTEROIDE = {
    ASTEROIDE_GRANDE: (44, 20, 1.0),
    ASTEROIDE_MEDIO: (25, 50, 1.45),
    ASTEROIDE_PEQUENO: (13, 100, 1.9),
}
FRAGMENTOS_POR_QUEBRA = 2

# ---------------------------------------------------------------------------
# Dificuldade
# ---------------------------------------------------------------------------
PONTOS_POR_NIVEL = 1000

ASTEROIDES_INICIAIS = 4
VELOCIDADE_ASTEROIDE_INICIAL = 1.1
AUMENTO_VELOCIDADE_POR_NIVEL = 0.12
VELOCIDADE_ASTEROIDE_TETO = 3.2

INTERVALO_SPAWN_INICIAL = 260  # frames entre novos asteroides grandes
INTERVALO_SPAWN_MINIMO = 90
REDUCAO_SPAWN_POR_NIVEL = 20
MAX_ASTEROIDES = 22  # limite de asteroides na tela (inclui fragmentos)

DURACAO_AVISO_NIVEL = 120  # frames que o aviso "LEVEL X" fica visivel

# ---------------------------------------------------------------------------
# Chefes
# ---------------------------------------------------------------------------
NIVEIS_POR_CHEFE = 5  # um chefe no nivel 5, 10, 15...
PONTOS_CHEFE = 1500
DURACAO_AVISO_CHEFE = 3 * FPS

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
