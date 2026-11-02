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
COR_JOGADOR2 = (255, 138, 216)  # rosa: nave do jogador 2

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
PONTOS_POR_VIDA = 3000  # uma vida extra a cada 3000 pontos (ate VIDAS_MAXIMAS)
DURACAO_INVENCIVEL = 2 * FPS  # apos ser atingido
DURACAO_ESCUDO = 5 * FPS  # item de escudo
INTERVALO_ESCUDO = (9 * FPS, 14 * FPS)  # um escudo novo a cada 9-14 s
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

ASTEROIDES_INICIAIS = 5
MAX_ASTEROIDES_ONDA = 10  # teto de asteroides grandes numa onda nova
VELOCIDADE_ASTEROIDE_INICIAL = 1.3
AUMENTO_VELOCIDADE_POR_NIVEL = 0.16
VELOCIDADE_ASTEROIDE_TETO = 3.8

INTERVALO_SPAWN_INICIAL = 200  # frames entre novos asteroides grandes
INTERVALO_SPAWN_MINIMO = 60
REDUCAO_SPAWN_POR_NIVEL = 22
MAX_ASTEROIDES = 26  # limite de asteroides na tela (inclui fragmentos)

# durante a luta contra o chefe os asteroides continuam vindo, mas com menos frequencia
MULTIPLICADOR_SPAWN_CHEFE = 2.0  # intervalo de spawn x2
MAX_ASTEROIDES_CHEFE = 12

DURACAO_AVISO_NIVEL = 120  # frames que o aviso "LEVEL X" fica visivel

# ---------------------------------------------------------------------------
# Chefes
# ---------------------------------------------------------------------------
NIVEIS_POR_CHEFE = 5  # um chefe no nivel 5, 10, 15...
NIVEIS_POR_MELHORIA = 6  # escolha de melhoria no nivel 6, 12, 18... (e ao derrotar um chefe)
PONTOS_CHEFE = 1500
DURACAO_AVISO_CHEFE = 3 * FPS

# ---------------------------------------------------------------------------
# Multiplayer local (os modos em si ficam em modos.py)
# ---------------------------------------------------------------------------
VIDAS_REVIVER = 2  # coop: vidas de quem e revivido pelo escudo do parceiro
ROUNDS_PARA_VENCER = 2  # duelo: melhor de 3
DURACAO_FIM_ROUND = 3 * FPS
FATOR_NIVEL_COOP = 1.5  # coop: os dois somam pontos, entao cada nivel pede mais pontos

# ---------------------------------------------------------------------------
# Arquivos
# ---------------------------------------------------------------------------
PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_RECORDE = os.path.join(PASTA_PROJETO, "recorde.txt")  # recorde do modo solo
CAMINHO_RANKING = os.path.join(PASTA_PROJETO, "ranking.json")  # pontuacao de cada jogador por partida

# ---------------------------------------------------------------------------
# Estados do jogo
# ---------------------------------------------------------------------------
ESTADO_INICIO = "inicio"
ESTADO_MODOS = "modos"  # escolha do modo de jogo
ESTADO_LOBBY = "jogadores"  # multiplayer: cada jogador entra com seu controle / teclado
ESTADO_ROUND = "round"  # intervalo entre os rounds do duelo
ESTADO_JOGANDO = "jogando"
ESTADO_GAMEOVER = "gameover"
ESTADO_NOME = "nome"  # fim de partida: cada jogador com pontos digita o nome para o ranking
ESTADO_PAUSADO = "pausado"
ESTADO_MELHORIA = "melhoria"  # escolhendo a melhoria do nivel novo
