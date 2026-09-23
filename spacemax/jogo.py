"""Loop principal e regras do jogo."""

import random
import sys

import pygame

from . import interface
from .config import (
    ALTURA,
    AUMENTO_VELOCIDADE_POR_NIVEL,
    COR_FUNDO,
    DURACAO_AVISO_NIVEL,
    ESTADO_GAMEOVER,
    ESTADO_INICIO,
    ESTADO_JOGANDO,
    FPS,
    INTERVALO_SPAWN_INICIAL,
    INTERVALO_SPAWN_MINIMO,
    LARGURA,
    PONTOS_POR_NIVEL,
    REDUCAO_SPAWN_POR_NIVEL,
    VELOCIDADE_METEORO_MAX_INICIAL,
    VELOCIDADE_METEORO_MIN_INICIAL,
    VELOCIDADE_METEORO_TETO,
    VIDAS_INICIAIS,
)
from .entidades import Estrela, Item, Meteoro, Nave, Particula, Tiro
from .recorde import carregar_recorde, salvar_recorde
from .sons import criar_sons, tocar


class Jogo:
    def __init__(self):
        pygame.init()
        self.tela: pygame.Surface = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("SpaceMax")
        self.relogio: pygame.time.Clock = pygame.time.Clock()

        self.fontes: interface.Fontes = interface.Fontes()
        self.sons: dict[str, pygame.mixer.Sound] | None = criar_sons()
        self.recorde: int = carregar_recorde()

        self.estrelas: list[Estrela] = [Estrela() for _ in range(70)]

        self.reiniciar()
        self.estado: str = ESTADO_INICIO

    def reiniciar(self):
        self.nave: Nave = Nave()
        self.meteoros: list[Meteoro] = []
        self.tiros: list[Tiro] = []
        self.itens: list[Item] = []
        self.particulas: list[Particula] = []
        self.pontuacao: int = 0
        self.vidas: int = VIDAS_INICIAIS
        self.nivel: int = 1
        self.tempo_aviso_nivel: int = DURACAO_AVISO_NIVEL
        self.frames_ate_proximo_spawn: int = INTERVALO_SPAWN_INICIAL
        self.tempo_escudo: int = 0
        self.tempo_ate_proximo_item: int = random.randint(500, 800)

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
            for meteoro in self.meteoros[:]:
                if tiro.colide_com(meteoro):
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
        for item in self.itens:
            if not item.coletado and self.nave.colide_com(item):
                item.coletado = True
                self.tempo_escudo = FPS * 5
                tocar(self.sons, "item")

        if self.nave.escudo:
            return

        for meteoro in self.meteoros[:]:
            if self.nave.colide_com(meteoro):
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
            interface.desenhar_tela_inicio(self.tela, self.fontes, self.recorde)
        else:
            interface.desenhar_hud(
                self.tela,
                self.fontes,
                self.pontuacao,
                self.nivel,
                self.vidas,
                self.tempo_aviso_nivel,
            )
            if self.estado == ESTADO_GAMEOVER:
                interface.desenhar_tela_gameover(
                    self.tela, self.fontes, self.pontuacao, self.recorde
                )

        pygame.display.flip()

    # -----------------------------------------------------------------
    def executar(self):
        while True:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)
