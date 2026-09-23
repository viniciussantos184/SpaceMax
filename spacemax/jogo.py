"""Loop principal e regras do jogo."""

import random
import sys

import pygame

from . import interface
from .config import (
    ALTURA,
    ASTEROIDES_INICIAIS,
    AUMENTO_VELOCIDADE_POR_NIVEL,
    COR_ASTEROIDE,
    COR_PRIMARIA,
    DURACAO_AVISO_NIVEL,
    DURACAO_ESCUDO,
    DURACAO_INVENCIVEL,
    ESTADO_GAMEOVER,
    ESTADO_INICIO,
    ESTADO_JOGANDO,
    FPS,
    INTERVALO_SPAWN_INICIAL,
    INTERVALO_SPAWN_MINIMO,
    LARGURA,
    MAX_ASTEROIDES,
    PONTOS_POR_NIVEL,
    REDUCAO_SPAWN_POR_NIVEL,
    VELOCIDADE_ASTEROIDE_INICIAL,
    VELOCIDADE_ASTEROIDE_TETO,
    VIDAS_INICIAIS,
)
from .entidades import Estrela, Item, Meteoro, Nave, Particula, Tiro
from .galaxias import PlanoDeFundo, indice_galaxia
from .recorde import carregar_recorde, salvar_recorde
from .sons import criar_sons, tocar

DURACAO_AVISO_GALAXIA = 3 * FPS


class Jogo:
    def __init__(self):
        pygame.init()
        self.tela: pygame.Surface = pygame.display.set_mode((LARGURA, ALTURA))
        pygame.display.set_caption("SpaceMax")
        self.relogio: pygame.time.Clock = pygame.time.Clock()

        self.fontes: interface.Fontes = interface.Fontes()
        self.sons: dict[str, pygame.mixer.Sound] | None = criar_sons()
        self.recorde: int = carregar_recorde()
        self.fundo: PlanoDeFundo = PlanoDeFundo()
        self.estrelas: list[Estrela] = [Estrela() for _ in range(90)]
        self.frame: int = 0

        self.reiniciar()
        self.estado: str = ESTADO_INICIO

    def reiniciar(self):
        self.nave: Nave = Nave()
        self.nave.reaparecer(DURACAO_INVENCIVEL // 2)
        self.meteoros: list[Meteoro] = []
        self.tiros: list[Tiro] = []
        self.itens: list[Item] = []
        self.particulas: list[Particula] = []
        self.pontuacao: int = 0
        self.vidas: int = VIDAS_INICIAIS
        self.nivel: int = 1
        self.novo_recorde: bool = False
        self.tempo_aviso_nivel: int = 0
        self.tempo_aviso_galaxia: int = DURACAO_AVISO_GALAXIA
        self.frames_ate_proximo_spawn: int = INTERVALO_SPAWN_INICIAL
        self.tempo_ate_proximo_item: int = random.randint(600, 900)

        self.fundo.ir_para(0, com_transicao=False)
        self.tingir_estrelas()
        self.lancar_onda()

    # ------------------------------------------------------------ dificuldade
    def calcular_nivel(self):
        return 1 + self.pontuacao // PONTOS_POR_NIVEL

    def atualizar_nivel(self):
        novo_nivel = self.calcular_nivel()
        if novo_nivel <= self.nivel:
            return
        self.nivel = novo_nivel
        tocar(self.sons, "nivel")

        # a cada 3 niveis o jogador chega a uma nova galaxia
        if self.fundo.ir_para(indice_galaxia(self.nivel)):
            self.tingir_estrelas()
            self.tempo_aviso_galaxia = DURACAO_AVISO_GALAXIA
            self.tempo_aviso_nivel = 0
        else:
            self.tempo_aviso_nivel = DURACAO_AVISO_NIVEL

    def velocidade_asteroide(self):
        velocidade = VELOCIDADE_ASTEROIDE_INICIAL + (self.nivel - 1) * AUMENTO_VELOCIDADE_POR_NIVEL
        return min(VELOCIDADE_ASTEROIDE_TETO, velocidade)

    def intervalo_spawn(self):
        intervalo = INTERVALO_SPAWN_INICIAL - (self.nivel - 1) * REDUCAO_SPAWN_POR_NIVEL
        return max(INTERVALO_SPAWN_MINIMO, intervalo)

    def lancar_onda(self):
        quantidade = min(8, ASTEROIDES_INICIAIS + (self.nivel - 1) // 2)
        for _ in range(quantidade):
            self.meteoros.append(Meteoro.na_borda(self.velocidade_asteroide()))

    def tingir_estrelas(self):
        for estrela in self.estrelas:
            estrela.tingir(self.fundo.galaxia.cor_estrelas)

    # ----------------------------------------------------------------- eventos
    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.sair()

            if evento.type == pygame.KEYDOWN:
                if evento.key == pygame.K_ESCAPE:
                    self.sair()

                if evento.key == pygame.K_SPACE:
                    self.acao_principal()

                if evento.key in (pygame.K_LSHIFT, pygame.K_RSHIFT):
                    self.usar_dash()

            if evento.type == pygame.MOUSEBUTTONDOWN:
                self.acao_principal()

    def acao_principal(self):
        if self.estado == ESTADO_JOGANDO:
            self.disparar()
        else:
            self.reiniciar()
            self.estado = ESTADO_JOGANDO

    def disparar(self):
        if self.nave.pode_atirar():
            self.tiros.append(self.nave.atirar())
            tocar(self.sons, "tiro")

    def usar_dash(self):
        if self.estado == ESTADO_JOGANDO and self.nave.pode_dash():
            self.nave.dash()
            tocar(self.sons, "dash")

    def sair(self):
        pygame.quit()
        sys.exit()

    # --------------------------------------------------------------- atualizar
    def atualizar(self):
        self.frame += 1
        self.fundo.atualizar()

        for estrela in self.estrelas:
            estrela.atualizar()

        for particula in self.particulas:
            particula.atualizar()
        self.particulas = [p for p in self.particulas if not p.morta()]

        # asteroides continuam flutuando ao fundo nas telas de inicio / game over
        for meteoro in self.meteoros:
            meteoro.atualizar()

        if self.estado != ESTADO_JOGANDO:
            return

        self.ler_controles()
        self.nave.atualizar()
        self.particulas.extend(self.nave.emitir_rastro())

        if self.tempo_aviso_nivel > 0:
            self.tempo_aviso_nivel -= 1
        if self.tempo_aviso_galaxia > 0:
            self.tempo_aviso_galaxia -= 1

        self.gerar_asteroides()
        self.gerar_itens()

        for tiro in self.tiros:
            tiro.atualizar()
        self.tiros = [t for t in self.tiros if not t.expirou()]

        for item in self.itens:
            item.atualizar()

        self.checar_colisoes_tiro_meteoro()
        self.checar_colisao_nave()

        self.itens = [i for i in self.itens if not i.expirou() and not i.coletado]

    def ler_controles(self):
        teclas = pygame.key.get_pressed()
        esquerda = teclas[pygame.K_LEFT] or teclas[pygame.K_a]
        direita = teclas[pygame.K_RIGHT] or teclas[pygame.K_d]
        self.nave.girar(direita - esquerda)  # 0 = soltou: o giro freia sozinho
        if teclas[pygame.K_UP] or teclas[pygame.K_w]:
            self.nave.acelerar()
        if teclas[pygame.K_DOWN] or teclas[pygame.K_s]:
            self.nave.frear()
        if teclas[pygame.K_SPACE]:
            self.disparar()

    def gerar_asteroides(self):
        if not self.meteoros:
            self.lancar_onda()
            self.frames_ate_proximo_spawn = self.intervalo_spawn()
            return

        self.frames_ate_proximo_spawn -= 1
        if self.frames_ate_proximo_spawn <= 0:
            self.frames_ate_proximo_spawn = self.intervalo_spawn()
            if len(self.meteoros) < MAX_ASTEROIDES:
                self.meteoros.append(Meteoro.na_borda(self.velocidade_asteroide()))

    def gerar_itens(self):
        self.tempo_ate_proximo_item -= 1
        if self.tempo_ate_proximo_item <= 0:
            self.tempo_ate_proximo_item = random.randint(900, 1400)
            if not self.itens:
                self.itens.append(Item())

    # ---------------------------------------------------------------- colisoes
    def checar_colisoes_tiro_meteoro(self):
        for tiro in self.tiros[:]:
            for meteoro in self.meteoros:
                if tiro.colide_com(meteoro):
                    self.tiros.remove(tiro)
                    self.destruir_asteroide(meteoro)
                    break

    def destruir_asteroide(self, meteoro):
        """Remove o asteroide, soma os pontos e coloca os fragmentos no lugar."""
        self.meteoros.remove(meteoro)
        self.meteoros.extend(meteoro.quebrar())
        self.pontuacao += meteoro.pontos
        self.criar_explosao(meteoro.x, meteoro.y, COR_ASTEROIDE, 6 + meteoro.tamanho * 5)
        tocar(self.sons, "explosao")
        self.atualizar_nivel()

    def checar_colisao_nave(self):
        for item in self.itens:
            if not item.coletado and self.nave.colide_com(item):
                item.coletado = True
                self.nave.ativar_escudo(DURACAO_ESCUDO)
                tocar(self.sons, "item")

        for meteoro in self.meteoros:
            if not self.nave.colide_com(meteoro):
                continue
            if self.nave.tempo_escudo > 0:
                # com escudo ativo, a nave destroi o que tocar
                self.destruir_asteroide(meteoro)
            elif self.nave.tempo_invencivel <= 0:
                self.destruir_asteroide(meteoro)
                self.perder_vida()
            return

    def perder_vida(self):
        self.vidas -= 1
        self.criar_explosao(self.nave.x, self.nave.y, COR_PRIMARIA, 30)
        tocar(self.sons, "colisao")
        if self.vidas <= 0:
            self.fim_de_jogo()
        else:
            self.nave.reaparecer(DURACAO_INVENCIVEL)

    def criar_explosao(self, x, y, cor, quantidade):
        for _ in range(quantidade):
            self.particulas.append(Particula(x, y, cor))

    def fim_de_jogo(self):
        self.estado = ESTADO_GAMEOVER
        self.tiros.clear()
        self.itens.clear()
        if self.pontuacao > self.recorde:
            self.recorde = self.pontuacao
            self.novo_recorde = True
            salvar_recorde(self.recorde)

    # ---------------------------------------------------------------- desenhar
    def desenhar(self):
        self.fundo.desenhar(self.tela)

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

        if self.estado == ESTADO_JOGANDO:
            self.nave.desenhar(self.tela)

        if self.estado == ESTADO_INICIO:
            interface.desenhar_tela_inicio(self.tela, self.fontes, self.recorde, self.frame)
        else:
            self.desenhar_hud()
            if self.estado == ESTADO_GAMEOVER:
                interface.desenhar_tela_gameover(
                    self.tela,
                    self.fontes,
                    self.pontuacao,
                    self.recorde,
                    self.nivel,
                    self.fundo.indice + 1,
                    self.novo_recorde,
                    self.frame,
                )

        pygame.display.flip()

    def desenhar_hud(self):
        galaxia = self.fundo.galaxia
        setor = self.fundo.indice + 1
        interface.desenhar_hud(
            self.tela,
            self.fontes,
            self.pontuacao,
            self.recorde,
            self.nivel,
            self.vidas,
            setor,
            galaxia.nome,
            self.nave.carga_dash,
        )
        if self.estado != ESTADO_JOGANDO:
            return
        interface.desenhar_aviso(
            self.tela,
            self.fontes,
            f"SETOR {setor:02d}",
            galaxia.nome,
            self.tempo_aviso_galaxia,
            DURACAO_AVISO_GALAXIA,
            galaxia.cor_espiral,
        )
        interface.desenhar_aviso(
            self.tela,
            self.fontes,
            "NIVEL",
            f"{self.nivel:02d}",
            self.tempo_aviso_nivel,
            DURACAO_AVISO_NIVEL,
        )

    # ------------------------------------------------------------------- loop
    def executar(self):
        while True:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)
