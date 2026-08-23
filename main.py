"""
SpaceMax - jogo 2D de acao e pontuacao infinita feito com pygame.

O jogador controla uma nave que se move para os lados na parte inferior da
tela e atira para cima para destruir meteoros que caem continuamente. Cada
meteoro destruido aumenta a pontuacao. A dificuldade cresce com o tempo:
mais meteoros, mais rapidos.

Controles:
    SETA ESQUERDA / A  -> move a nave para a esquerda
    SETA DIREITA  / D  -> move a nave para a direita
    ESPACO              -> atira
    ESC                 -> sai do jogo
    Na tela inicial / game over -> ESPACO ou clique para (re)comecar

Requisitos: pip install -r requirements.txt (pygame ou pygame-ce)
Executar:   python main.py
"""

import array
import math
import os
import random
import sys

import pygame

# ---------------------------------------------------------------------------
# Configuracoes gerais
# ---------------------------------------------------------------------------
LARGURA, ALTURA = 480, 720
FPS = 60

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

VELOCIDADE_NAVE = 6.5
VELOCIDADE_TIRO = 11
COOLDOWN_TIRO = 14  # frames entre disparos

VIDAS_INICIAIS = 3

PONTOS_POR_NIVEL = 8  # a cada N pontos o jogador sobe de nivel

VELOCIDADE_METEORO_MIN_INICIAL = 2.0
VELOCIDADE_METEORO_MAX_INICIAL = 3.5
AUMENTO_VELOCIDADE_POR_NIVEL = 0.35
VELOCIDADE_METEORO_TETO = 9.5

INTERVALO_SPAWN_INICIAL = 65  # frames entre meteoros
INTERVALO_SPAWN_MINIMO = 16
REDUCAO_SPAWN_POR_NIVEL = 6

DURACAO_AVISO_NIVEL = 120  # frames que o aviso "NIVEL X" fica visivel

CAMINHO_RECORDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recorde.txt")

ESTADO_INICIO = "inicio"
ESTADO_JOGANDO = "jogando"
ESTADO_GAMEOVER = "gameover"


# ---------------------------------------------------------------------------
# Sons gerados proceduralmente (sem depender de arquivos externos)
# ---------------------------------------------------------------------------
def gerar_som(frequencia, duracao=0.12, volume=0.25, tipo="senoide"):
    taxa_amostragem = 44100
    n_amostras = int(taxa_amostragem * duracao)
    buffer = array.array("h", [0] * n_amostras)
    amplitude = int(32767 * volume)

    for i in range(n_amostras):
        t = i / taxa_amostragem
        envelope = 1.0 - (i / n_amostras)  # fade-out simples

        if tipo == "senoide":
            valor = math.sin(2 * math.pi * frequencia * t)
        elif tipo == "quadrada":
            valor = 1.0 if math.sin(2 * math.pi * frequencia * t) >= 0 else -1.0
        elif tipo == "ruido":
            valor = random.uniform(-1.0, 1.0)
        else:
            valor = 0.0

        buffer[i] = int(valor * amplitude * envelope)

    return pygame.mixer.Sound(buffer=buffer)


def criar_sons():
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        return {
            "tiro": gerar_som(700, 0.06, 0.12, "quadrada"),
            "explosao": gerar_som(140, 0.18, 0.25, "ruido"),
            "colisao": gerar_som(110, 0.35, 0.3, "quadrada"),
            "item": gerar_som(1200, 0.12, 0.2, "senoide"),
            "nivel": gerar_som(660, 0.20, 0.22, "senoide"),
        }
    except pygame.error:
        return None


def tocar(sons, nome):
    if sons and nome in sons:
        sons[nome].play()


# ---------------------------------------------------------------------------
# Recorde persistente
# ---------------------------------------------------------------------------
def carregar_recorde():
    try:
        with open(CAMINHO_RECORDE, "r") as arquivo:
            return int(arquivo.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def salvar_recorde(valor):
    try:
        with open(CAMINHO_RECORDE, "w") as arquivo:
            arquivo.write(str(valor))
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Cenario com estrelas (paralaxe vertical, ja que a acao agora e vertical)
# ---------------------------------------------------------------------------
class Estrela:
    def __init__(self):
        self.x = random.uniform(0, LARGURA)
        self.y = random.uniform(0, ALTURA)
        self.tamanho = random.choice([1, 1, 1, 2, 2, 3])
        self.velocidade = self.tamanho * 0.5 + 0.3

    def atualizar(self):
        self.y += self.velocidade
        if self.y > ALTURA + 2:
            self.y = -2
            self.x = random.uniform(0, LARGURA)

    def desenhar(self, tela):
        pygame.draw.circle(tela, COR_ESTRELA, (int(self.x), int(self.y)), self.tamanho)


# ---------------------------------------------------------------------------
# Personagem principal (nave que se move para os lados)
# ---------------------------------------------------------------------------
class Nave:
    LARGURA = 40
    ALTURA = 28

    def __init__(self):
        self.x = LARGURA / 2
        self.y = ALTURA - 60
        self.escudo = False
        self.cooldown_atual = 0

    def mover(self, direcao):
        self.x += direcao * VELOCIDADE_NAVE
        margem = self.LARGURA / 2
        self.x = max(margem, min(LARGURA - margem, self.x))

    def atualizar(self):
        if self.cooldown_atual > 0:
            self.cooldown_atual -= 1

    def pode_atirar(self):
        return self.cooldown_atual <= 0

    def atirar(self):
        self.cooldown_atual = COOLDOWN_TIRO
        return Tiro(self.x, self.y - self.ALTURA / 2)

    def rect(self):
        return pygame.Rect(
            int(self.x - self.LARGURA / 2),
            int(self.y - self.ALTURA / 2),
            self.LARGURA,
            self.ALTURA,
        )

    def desenhar(self, tela):
        pontos = [
            (0, -self.ALTURA / 2),
            (-self.LARGURA / 2, self.ALTURA / 2),
            (0, self.ALTURA / 4),
            (self.LARGURA / 2, self.ALTURA / 2),
        ]
        pontos_tela = [(self.x + px, self.y + py) for px, py in pontos]

        cor = (255, 215, 60) if self.escudo else COR_NAVE
        pygame.draw.polygon(tela, cor, pontos_tela)
        pygame.draw.polygon(tela, COR_NAVE_BORDA, pontos_tela, 2)

        if self.escudo:
            pygame.draw.circle(tela, (255, 230, 130), (int(self.x), int(self.y)), 28, 2)


# ---------------------------------------------------------------------------
# Tiro disparado pela nave
# ---------------------------------------------------------------------------
class Tiro:
    LARGURA = 4
    ALTURA = 14

    def __init__(self, x, y):
        self.x = x
        self.y = y

    def atualizar(self):
        self.y -= VELOCIDADE_TIRO

    def fora_da_tela(self):
        return self.y + self.ALTURA < 0

    def rect(self):
        return pygame.Rect(
            int(self.x - self.LARGURA / 2),
            int(self.y - self.ALTURA / 2),
            self.LARGURA,
            self.ALTURA,
        )

    def desenhar(self, tela):
        pygame.draw.rect(tela, COR_TIRO, self.rect(), border_radius=2)


# ---------------------------------------------------------------------------
# Meteoros que caem do topo
# ---------------------------------------------------------------------------
class Meteoro:
    def __init__(self, velocidade_min, velocidade_max):
        self.raio = random.randint(16, 30)
        self.x = random.uniform(self.raio, LARGURA - self.raio)
        self.y = -self.raio
        self.velocidade_y = random.uniform(velocidade_min, velocidade_max)
        self.velocidade_x = random.uniform(-1.0, 1.0)
        self.angulo = 0
        self.velocidade_angular = random.uniform(-3, 3)
        # vida proporcional ao tamanho: meteoros grandes exigem mais de 1 tiro
        self.vida = 1 if self.raio < 23 else 2

        pontos = random.randint(7, 10)
        self.forma = []
        for i in range(pontos):
            ang = (2 * math.pi / pontos) * i
            variacao = random.uniform(0.75, 1.0)
            self.forma.append((ang, variacao))

    def atualizar(self):
        self.y += self.velocidade_y
        self.x += self.velocidade_x
        self.angulo += self.velocidade_angular

        if self.x - self.raio < 0 or self.x + self.raio > LARGURA:
            self.velocidade_x *= -1
            self.x = max(self.raio, min(LARGURA - self.raio, self.x))

    def fora_da_tela(self):
        return self.y - self.raio > ALTURA

    def levar_dano(self):
        self.vida -= 1
        return self.vida <= 0

    def rect(self):
        return pygame.Rect(
            int(self.x - self.raio), int(self.y - self.raio), self.raio * 2, self.raio * 2
        )

    def desenhar(self, tela):
        angulo_rad = math.radians(self.angulo)
        pontos_tela = []
        for ang, variacao in self.forma:
            a = ang + angulo_rad
            r = self.raio * variacao
            pontos_tela.append((self.x + r * math.cos(a), self.y + r * math.sin(a)))

        pygame.draw.polygon(tela, COR_METEORO, pontos_tela)
        pygame.draw.polygon(tela, COR_METEORO_BORDA, pontos_tela, 2)


# ---------------------------------------------------------------------------
# Particulas de explosao (efeito visual simples)
# ---------------------------------------------------------------------------
class Particula:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        angulo = random.uniform(0, 2 * math.pi)
        velocidade = random.uniform(1.5, 4.5)
        self.vx = math.cos(angulo) * velocidade
        self.vy = math.sin(angulo) * velocidade
        self.vida = random.randint(15, 30)
        self.vida_max = self.vida
        self.raio = random.randint(2, 4)

    def atualizar(self):
        self.x += self.vx
        self.y += self.vy
        self.vida -= 1

    def morta(self):
        return self.vida <= 0

    def desenhar(self, tela):
        alpha = max(0, self.vida / self.vida_max)
        cor = (
            int(255 * alpha + 90 * (1 - alpha)),
            int(180 * alpha + 60 * (1 - alpha)),
            int(60 * alpha),
        )
        pygame.draw.circle(tela, cor, (int(self.x), int(self.y)), self.raio)


# ---------------------------------------------------------------------------
# Item especial (escudo temporario)
# ---------------------------------------------------------------------------
class Item:
    RAIO = 12

    def __init__(self):
        self.x = random.uniform(self.RAIO, LARGURA - self.RAIO)
        self.y = -self.RAIO
        self.velocidade_y = 2.5
        self.coletado = False

    def atualizar(self):
        self.y += self.velocidade_y

    def fora_da_tela(self):
        return self.y - self.RAIO > ALTURA

    def rect(self):
        return pygame.Rect(
            int(self.x - self.RAIO), int(self.y - self.RAIO), self.RAIO * 2, self.RAIO * 2
        )

    def desenhar(self, tela):
        pygame.draw.circle(tela, COR_ITEM, (int(self.x), int(self.y)), self.RAIO)
        pygame.draw.circle(tela, (255, 255, 255), (int(self.x), int(self.y)), self.RAIO, 2)


# ---------------------------------------------------------------------------
# Funcoes de desenho auxiliares
# ---------------------------------------------------------------------------
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


# ---------------------------------------------------------------------------
# Jogo principal
# ---------------------------------------------------------------------------
class Jogo:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("SpaceMax")
        self.relogio = pygame.time.Clock()

        self.fonte_titulo = pygame.font.SysFont("arial", 54, bold=True)
        self.fonte_grande = pygame.font.SysFont("arial", 36, bold=True)
        self.fonte_media = pygame.font.SysFont("arial", 24)
        self.fonte_pequena = pygame.font.SysFont("arial", 18)

        self.sons = criar_sons()
        self.recorde = carregar_recorde()

        self.estrelas = [Estrela() for _ in range(70)]

        self.reiniciar()
        self.estado = ESTADO_INICIO

    def reiniciar(self):
        self.nave = Nave()
        self.meteoros = []
        self.tiros = []
        self.itens = []
        self.particulas = []
        self.pontuacao = 0
        self.vidas = VIDAS_INICIAIS
        self.nivel = 1
        self.tempo_aviso_nivel = DURACAO_AVISO_NIVEL
        self.frames_ate_proximo_spawn = INTERVALO_SPAWN_INICIAL
        self.tempo_escudo = 0
        self.tempo_ate_proximo_item = random.randint(500, 800)

    def calcular_nivel(self):
        return 1 + self.pontuacao // PONTOS_POR_NIVEL

    def atualizar_nivel(self):
        novo_nivel = self.calcular_nivel()
        if novo_nivel > self.nivel:
            self.nivel = novo_nivel
            self.tempo_aviso_nivel = DURACAO_AVISO_NIVEL
            tocar(self.sons, "nivel")

    def velocidade_meteoro(self):
        bonus = (self.nivel - 1) * AUMENTO_VELOCIDADE_POR_NIVEL
        vel_min = min(VELOCIDADE_METEORO_TETO, VELOCIDADE_METEORO_MIN_INICIAL + bonus)
        vel_max = min(VELOCIDADE_METEORO_TETO, VELOCIDADE_METEORO_MAX_INICIAL + bonus)
        return vel_min, vel_max

    def intervalo_spawn(self):
        intervalo = INTERVALO_SPAWN_INICIAL - (self.nivel - 1) * REDUCAO_SPAWN_POR_NIVEL
        return max(INTERVALO_SPAWN_MINIMO, intervalo)

    # -----------------------------------------------------------------
    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.sair()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.sair()

                if evento.key == pygame.K_SPACE:
                    self.acao_principal()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.acao_principal()

    def acao_principal(self):
        if self.estado == ESTADO_INICIO:
            self.estado = ESTADO_JOGANDO
        elif self.estado == ESTADO_JOGANDO:
            self.disparar()
        elif self.estado == ESTADO_GAMEOVER:
            self.reiniciar()
            self.estado = ESTADO_JOGANDO

    def disparar(self):
        if self.nave.pode_atirar():
            self.tiros.append(self.nave.atirar())
            tocar(self.sons, "tiro")

    def sair(self):
        pygame.quit()
        sys.exit()

    # -----------------------------------------------------------------
    def atualizar(self):
        for estrela in self.estrelas:
            estrela.atualizar()

        for particula in self.particulas:
            particula.atualizar()
        self.particulas = [p for p in self.particulas if not p.morta()]

        if self.estado != ESTADO_JOGANDO:
            return

        teclas = pygame.key.get_pressed()
        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            self.nave.mover(-1)
        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            self.nave.mover(1)
        if teclas[pygame.K_SPACE]:
            self.disparar()

        self.nave.atualizar()

        if self.tempo_aviso_nivel > 0:
            self.tempo_aviso_nivel -= 1

        if self.tempo_escudo > 0:
            self.tempo_escudo -= 1
            self.nave.escudo = True
        else:
            self.nave.escudo = False

        # geracao de meteoros
        self.frames_ate_proximo_spawn -= 1
        if self.frames_ate_proximo_spawn <= 0:
            self.frames_ate_proximo_spawn = self.intervalo_spawn()
            vel_min, vel_max = self.velocidade_meteoro()
            self.meteoros.append(Meteoro(vel_min, vel_max))

        # geracao de itens especiais (raros)
        self.tempo_ate_proximo_item -= 1
        if self.tempo_ate_proximo_item <= 0:
            self.tempo_ate_proximo_item = random.randint(600, 900)
            self.itens.append(Item())

        for tiro in self.tiros:
            tiro.atualizar()
        self.tiros = [t for t in self.tiros if not t.fora_da_tela()]

        for meteoro in self.meteoros:
            meteoro.atualizar()

        for item in self.itens:
            item.atualizar()

        self.checar_colisoes_tiro_meteoro()
        self.checar_colisao_nave()

        self.meteoros = [m for m in self.meteoros if not m.fora_da_tela()]
        self.itens = [i for i in self.itens if not i.fora_da_tela() and not i.coletado]

    def checar_colisoes_tiro_meteoro(self):
        for tiro in self.tiros[:]:
            rect_tiro = tiro.rect()
            for meteoro in self.meteoros[:]:
                if rect_tiro.colliderect(meteoro.rect()):
                    if tiro in self.tiros:
                        self.tiros.remove(tiro)
                    destruido = meteoro.levar_dano()
                    if destruido:
                        self.meteoros.remove(meteoro)
                        self.pontuacao += 1
                        self.atualizar_nivel()
                        self.criar_explosao(meteoro.x, meteoro.y)
                        tocar(self.sons, "explosao")
                    break

    def checar_colisao_nave(self):
        rect_jogador = self.nave.rect()

        for item in self.itens:
            if not item.coletado and rect_jogador.colliderect(item.rect()):
                item.coletado = True
                self.tempo_escudo = FPS * 5
                tocar(self.sons, "item")

        if self.nave.escudo:
            return

        for meteoro in self.meteoros[:]:
            if rect_jogador.colliderect(meteoro.rect()):
                self.meteoros.remove(meteoro)
                self.criar_explosao(meteoro.x, meteoro.y)
                self.perder_vida()
                return

    def perder_vida(self):
        self.vidas -= 1
        tocar(self.sons, "colisao")
        if self.vidas <= 0:
            self.fim_de_jogo()
        else:
            self.tempo_escudo = FPS * 2  # breve invencibilidade apos ser atingido

    def criar_explosao(self, x, y):
        for _ in range(14):
            self.particulas.append(Particula(x, y))

    def fim_de_jogo(self):
        self.estado = ESTADO_GAMEOVER
        if self.pontuacao > self.recorde:
            self.recorde = self.pontuacao
            salvar_recorde(self.recorde)

    # -----------------------------------------------------------------
    def desenhar(self):
        self.tela.fill(COR_FUNDO)

        for estrela in self.estrelas:
            estrela.desenhar(self.tela)

        for item in self.itens:
            item.desenhar(self.tela)

        for meteoro in self.meteoros:
            meteoro.desenhar(self.tela)

        for tiro in self.tiros:
            tiro.desenhar(self.tela)

        for particula in self.particulas:
            particula.desenhar(self.tela)

        self.nave.desenhar(self.tela)

        if self.estado == ESTADO_INICIO:
            self.desenhar_tela_inicio()
        elif self.estado == ESTADO_JOGANDO:
            self.desenhar_hud()
        elif self.estado == ESTADO_GAMEOVER:
            self.desenhar_hud()
            self.desenhar_tela_gameover()

        pygame.display.flip()

    def desenhar_hud(self):
        desenhar_texto(self.tela, self.fonte_grande, str(self.pontuacao), LARGURA / 2, 40)
        desenhar_texto(
            self.tela,
            self.fonte_pequena,
            f"Nivel {self.nivel}",
            LARGURA - 50,
            30,
            cor=(200, 220, 255),
        )

        for i in range(self.vidas):
            cx = 24 + i * 26
            cy = 30
            pygame.draw.polygon(
                self.tela,
                COR_VIDA,
                [(cx, cy - 10), (cx - 10, cy + 10), (cx, cy + 4), (cx + 10, cy + 10)],
            )

        if self.tempo_aviso_nivel > 0 and self.nivel > 1:
            alpha = min(255, int(255 * (self.tempo_aviso_nivel / 40)))
            superficie = self.fonte_titulo.render(f"NIVEL {self.nivel}", True, (255, 230, 120))
            superficie.set_alpha(alpha)
            rect = superficie.get_rect(center=(LARGURA / 2, ALTURA / 2 - 200))
            self.tela.blit(superficie, rect)

    def desenhar_tela_inicio(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.tela.blit(overlay, (0, 0))

        desenhar_texto(self.tela, self.fonte_titulo, "SpaceMax", LARGURA / 2, ALTURA / 2 - 140)
        desenhar_texto(
            self.tela,
            self.fonte_media,
            "Toque ESPACO ou clique para comecar",
            LARGURA / 2,
            ALTURA / 2 - 60,
        )
        desenhar_texto(
            self.tela,
            self.fonte_pequena,
            "Setas/A-D: mover   ESPACO: atirar",
            LARGURA / 2,
            ALTURA / 2 - 20,
        )
        desenhar_texto(
            self.tela,
            self.fonte_pequena,
            "Destrua os meteoros antes que colidam com sua nave",
            LARGURA / 2,
            ALTURA / 2 + 12,
        )
        desenhar_texto(
            self.tela,
            self.fonte_pequena,
            f"Recorde: {self.recorde}",
            LARGURA / 2,
            ALTURA / 2 + 50,
        )

    def desenhar_tela_gameover(self):
        overlay = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.tela.blit(overlay, (0, 0))

        desenhar_texto(self.tela, self.fonte_titulo, "Game Over", LARGURA / 2, ALTURA / 2 - 100)
        desenhar_texto(
            self.tela,
            self.fonte_grande,
            f"Pontuacao: {self.pontuacao}",
            LARGURA / 2,
            ALTURA / 2 - 30,
        )
        desenhar_texto(
            self.tela, self.fonte_media, f"Recorde: {self.recorde}", LARGURA / 2, ALTURA / 2 + 10
        )
        desenhar_texto(
            self.tela,
            self.fonte_pequena,
            "Toque ESPACO ou clique para jogar novamente",
            LARGURA / 2,
            ALTURA / 2 + 70,
        )

    # -----------------------------------------------------------------
    def executar(self):
        while True:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)


if __name__ == "__main__":
    Jogo().executar()
