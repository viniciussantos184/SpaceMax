"""Loop principal e regras do jogo."""

import random
import sys

import pygame

from . import interface
from .config import (
    ALTURA,
    ARMA_EXPLOSIVA,
    ASTEROIDES_INICIAIS,
    AUMENTO_VELOCIDADE_POR_NIVEL,
    COR_ASTEROIDE,
    COR_EXPLOSIVO,
    COR_ITEM,
    COR_PRIMARIA,
    DANO_EXPLOSAO_CHEFE,
    DURACAO_AVISO_CHEFE,
    DURACAO_AVISO_NIVEL,
    DURACAO_ESCUDO,
    DURACAO_INVENCIVEL,
    ESTADO_GAMEOVER,
    ESTADO_INICIO,
    ESTADO_JOGANDO,
    FPS,
    INTERVALO_SPAWN_INICIAL,
    INTERVALO_ESCUDO,
    INTERVALO_SPAWN_MINIMO,
    LARGURA,
    MAX_ASTEROIDES,
    MAX_ESCUDOS_NA_TELA,
    MUNICAO_EXPLOSIVA,
    NIVEIS_POR_CHEFE,
    PONTOS_CHEFE,
    PONTOS_POR_NIVEL,
    PONTOS_POR_VIDA,
    RAIO_EXPLOSAO,
    REDUCAO_SPAWN_POR_NIVEL,
    VELOCIDADE_ASTEROIDE_INICIAL,
    VELOCIDADE_ASTEROIDE_TETO,
    VIDAS_INICIAIS,
    VIDAS_MAXIMAS,
)
from .entidades import CHEFES, Estrela, Item, Meteoro, Nave, Onda, Particula, ProjetilChefe, Tiro
from .entidades.chefes import Chefe
from .galaxias import PlanoDeFundo, indice_galaxia
from .recorde import carregar_recorde, salvar_recorde
from .sons import criar_sons, tocar

DURACAO_AVISO_GALAXIA = 3 * FPS
Y_AVISO_CHEFE = ALTURA / 2 - 80  # abaixo do aviso de nivel/galaxia, sem sobrepor


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
        # a cena do jogo e desenhada aqui e copiada na tela com o deslocamento
        # do tremor; o HUD e desenhado depois, direto na tela, e nao treme
        self.cena: pygame.Surface = pygame.Surface((LARGURA, ALTURA))

        self.reiniciar()
        self.estado: str = ESTADO_INICIO

    def reiniciar(self):
        self.nave: Nave = Nave()
        self.nave.reaparecer(DURACAO_INVENCIVEL // 2)
        self.meteoros: list[Meteoro] = []
        self.tiros: list[Tiro] = []
        self.itens: list[Item] = []
        self.particulas: list[Particula] = []
        self.ondas: list[Onda] = []
        self.chefe: Chefe | None = None
        self.projeteis: list[ProjetilChefe] = []
        self.chefes_derrotados: int = 0
        self.aviso_chefe: tuple[str, str, tuple[int, int, int]] = ("", "", COR_PRIMARIA)
        self.tempo_aviso_chefe: int = 0
        self.recarga_som_chefe: int = 0
        self.tremor: int = 0
        self.pontuacao: int = 0
        self.vidas: int = VIDAS_INICIAIS
        self.pontos_proxima_vida: int = PONTOS_POR_VIDA
        self.nivel: int = 1
        self.novo_recorde: bool = False
        self.tempo_aviso_nivel: int = 0
        self.tempo_aviso_galaxia: int = DURACAO_AVISO_GALAXIA
        self.frames_ate_proximo_spawn: int = INTERVALO_SPAWN_INICIAL
        self.tempo_ate_proximo_item: int = random.randint(*INTERVALO_ESCUDO) // 2

        self.fundo.ir_para(0, com_transicao=False)
        self.tingir_estrelas()
        self.lancar_onda()

    # ------------------------------------------------------------ dificuldade
    def calcular_nivel(self):
        return 1 + self.pontuacao // PONTOS_POR_NIVEL

    def atualizar_nivel(self):
        if self.chefe:  # durante a luta contra o chefe o nivel fica congelado
            return
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

        if self.nivel >= NIVEIS_POR_CHEFE * (self.chefes_derrotados + 1):
            self.iniciar_chefe()

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

    # ------------------------------------------------------------------ chefes
    def iniciar_chefe(self):
        """Chefe diferente a cada vez; depois do ultimo a lista recomeca mais forte."""
        indice = self.chefes_derrotados
        classe = CHEFES[indice % len(CHEFES)]
        self.chefe = classe(ciclo=indice // len(CHEFES))
        self.mostrar_aviso_chefe(f"ALERTA  ·  CHEFE {indice + 1:02d}", self.chefe.NOME, self.chefe.COR)
        self.tempo_aviso_nivel = 0
        tocar(self.sons, "alerta")

    def mostrar_aviso_chefe(self, subtitulo, titulo, cor):
        self.aviso_chefe = (subtitulo, titulo, cor)
        self.tempo_aviso_chefe = DURACAO_AVISO_CHEFE

    def atualizar_chefe(self):
        novos = []
        for projetil in self.projeteis:
            projetil.atualizar()
            estilhacos = projetil.detonar()
            if estilhacos:
                self.ondas.append(Onda(projetil.x, projetil.y, projetil.cor, raio_final=34, duracao=16))
                novos.extend(estilhacos)
        self.projeteis = [p for p in self.projeteis if not p.expirou()] + novos

        if self.recarga_som_chefe > 0:
            self.recarga_som_chefe -= 1
        if not self.chefe:
            return
        self.chefe.definir_alvo(self.nave.x, self.nave.y)
        self.chefe.atualizar()
        disparos = self.chefe.atacar()
        if disparos:
            self.projeteis.extend(disparos)
            # espirais disparam quase todo frame: limita o som para nao virar ruido
            if self.recarga_som_chefe <= 0:
                tocar(self.sons, "tiro_chefe")
                self.recarga_som_chefe = 12

    def danificar_chefe(self, quantidade, x, y):
        if not self.chefe.receber_dano(quantidade):
            return
        self.criar_explosao(x, y, self.chefe.COR, 4)
        tocar(self.sons, "acerto_chefe")
        if self.chefe.morto():
            self.derrotar_chefe()

    def derrotar_chefe(self):
        chefe = self.chefe
        self.chefe = None
        self.chefes_derrotados += 1
        self.somar_pontos(PONTOS_CHEFE)

        x, y = chefe.x, chefe.y
        self.ondas.append(Onda(x, y, chefe.COR, raio_final=90, duracao=24))
        self.ondas.append(Onda(x, y, chefe.COR, raio_final=170, duracao=40, raio_inicial=20))
        self.ondas.append(Onda(x, y, (255, 255, 255), raio_final=260, duracao=56, raio_inicial=40))
        self.criar_explosao(x, y, chefe.COR, 70)
        self.criar_explosao(x, y, (255, 255, 255), 30)
        # os projeteis que sobraram viram faiscas
        for projetil in self.projeteis:
            self.criar_explosao(projetil.x, projetil.y, projetil.cor, 2)
        self.projeteis.clear()
        self.tremor = max(self.tremor, 26)
        tocar(self.sons, "chefe_derrotado")

        self.mostrar_aviso_chefe("CHEFE DERROTADO", f"+{PONTOS_CHEFE}", chefe.COR)
        self.frames_ate_proximo_spawn = self.intervalo_spawn()
        self.atualizar_nivel()

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

                if evento.key in (pygame.K_LCTRL, pygame.K_RCTRL):
                    self.usar_dash()

                if evento.key in (pygame.K_q, pygame.K_TAB):
                    self.trocar_arma()

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
            tiro = self.nave.atirar()
            self.tiros.append(tiro)
            tocar(self.sons, "tiro_explosivo" if tiro.EXPLOSIVO else "tiro")

    def trocar_arma(self):
        if self.estado == ESTADO_JOGANDO:
            self.nave.trocar_arma()
            tocar(self.sons, "troca_arma")

    def usar_dash(self):
        if self.estado == ESTADO_JOGANDO:
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

        for onda in self.ondas:
            onda.atualizar()
        self.ondas = [o for o in self.ondas if not o.terminou()]
        if self.tremor > 0:
            self.tremor -= 1

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
        if self.tempo_aviso_chefe > 0:
            self.tempo_aviso_chefe -= 1

        self.gerar_asteroides()
        self.gerar_itens()

        for tiro in self.tiros:
            tiro.atualizar()
            if tiro.EXPLOSIVO and tiro.expirou():
                self.explodir(tiro.x, tiro.y)  # explode sozinho ao fim do alcance
        self.tiros = [t for t in self.tiros if not t.expirou()]

        for item in self.itens:
            item.atualizar()

        self.atualizar_chefe()

        self.checar_colisoes_tiro_meteoro()
        self.checar_colisoes_tiro_chefe()
        self.checar_colisao_nave()
        self.checar_ataques_chefe()

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
        if self.chefe:  # durante a luta nao surgem asteroides novos
            return
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
            self.tempo_ate_proximo_item = random.randint(*INTERVALO_ESCUDO)
            if len(self.itens) < MAX_ESCUDOS_NA_TELA:
                self.itens.append(Item())

    # ---------------------------------------------------------------- colisoes
    def checar_colisoes_tiro_meteoro(self):
        for tiro in self.tiros[:]:
            for meteoro in self.meteoros:
                if tiro.colide_com(meteoro):
                    self.tiros.remove(tiro)
                    if tiro.EXPLOSIVO:
                        self.explodir(tiro.x, tiro.y)
                    else:
                        self.destruir_asteroide(meteoro)
                    break

    def checar_colisoes_tiro_chefe(self):
        for tiro in self.tiros[:]:
            if not self.chefe:
                return
            if tiro.EXPLOSIVO and (self.chefe.bloqueia(tiro) or self.chefe.atinge(tiro)):
                self.tiros.remove(tiro)
                self.explodir(tiro.x, tiro.y)
            elif self.chefe.bloqueia(tiro):
                self.tiros.remove(tiro)
                self.criar_explosao(tiro.x, tiro.y, self.chefe.COR, 3)
            elif self.chefe.atinge(tiro):
                self.tiros.remove(tiro)
                self.danificar_chefe(1, tiro.x, tiro.y)

    def explodir(self, x, y):
        """Tiro explosivo: quebra asteroides, apaga projeteis e fere o chefe dentro da area."""
        self.ondas.append(Onda(x, y, COR_EXPLOSIVO, raio_final=RAIO_EXPLOSAO, duracao=22))
        self.ondas.append(Onda(x, y, (255, 230, 200), raio_final=RAIO_EXPLOSAO * 0.6, duracao=14))
        self.criar_explosao(x, y, COR_EXPLOSIVO, 40)
        self.tremor = max(self.tremor, 10)
        tocar(self.sons, "explosao_grande")

        def na_area(entidade):
            return ((entidade.x - x) ** 2 + (entidade.y - y) ** 2) ** 0.5 < RAIO_EXPLOSAO + entidade.raio

        for meteoro in [m for m in self.meteoros if na_area(m)]:
            self.destruir_asteroide(meteoro)
        for projetil in [p for p in self.projeteis if na_area(p)]:
            self.projeteis.remove(projetil)
            self.criar_explosao(projetil.x, projetil.y, projetil.cor, 2)
        if self.chefe and na_area(self.chefe):
            self.danificar_chefe(DANO_EXPLOSAO_CHEFE, x, y)

    def checar_ataques_chefe(self):
        """Projeteis e corpo do chefe contra a nave (o escudo protege dos dois)."""
        if self.estado != ESTADO_JOGANDO:
            return
        nave = self.nave
        for projetil in self.projeteis[:]:
            if not nave.colide_com(projetil):
                continue
            self.projeteis.remove(projetil)
            if nave.tempo_escudo > 0:
                self.ondas.append(Onda(projetil.x, projetil.y, COR_ITEM, raio_final=18, duracao=12))
                nave.impacto_no_escudo()
            elif nave.tempo_invencivel <= 0:
                self.perder_vida()
                return

        chefe = self.chefe
        if not chefe or not chefe.atinge(nave):
            return
        if nave.tempo_escudo > 0:
            # o escudo empurra a nave para fora e causa dano no chefe
            self.efeito_impacto_escudo(chefe, 3)
            self.empurrar_nave(chefe)
            self.danificar_chefe(3, nave.x, nave.y)
        elif nave.tempo_invencivel <= 0:
            self.perder_vida()

    def empurrar_nave(self, chefe):
        dx, dy = self.nave.x - chefe.x, self.nave.y - chefe.y
        distancia = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / distancia, dy / distancia
        afastamento = chefe.raio + self.nave.raio + 4
        self.nave.x, self.nave.y = chefe.x + ux * afastamento, chefe.y + uy * afastamento
        self.nave.vx, self.nave.vy = ux * 7, uy * 7

    def somar_pontos(self, pontos):
        """Soma pontos e da uma vida extra a cada PONTOS_POR_VIDA (ate VIDAS_MAXIMAS)."""
        self.pontuacao += pontos
        while self.pontuacao >= self.pontos_proxima_vida:
            self.pontos_proxima_vida += PONTOS_POR_VIDA
            if self.vidas < VIDAS_MAXIMAS:
                self.vidas += 1
                self.ondas.append(Onda(self.nave.x, self.nave.y, COR_PRIMARIA, raio_final=60, duracao=20))
                tocar(self.sons, "item")

    def destruir_asteroide(self, meteoro):
        """Remove o asteroide, soma os pontos e coloca os fragmentos no lugar."""
        self.meteoros.remove(meteoro)
        self.meteoros.extend(meteoro.quebrar())
        self.somar_pontos(meteoro.pontos)
        self.criar_explosao(meteoro.x, meteoro.y, COR_ASTEROIDE, 6 + meteoro.tamanho * 5)
        tocar(self.sons, "explosao")
        self.atualizar_nivel()

    def checar_colisao_nave(self):
        for item in self.itens:
            if not item.coletado and self.nave.colide_com(item):
                item.coletado = True
                self.nave.ativar_escudo(DURACAO_ESCUDO)
                self.efeito_pegar_escudo()
                tocar(self.sons, "item")

        for meteoro in self.meteoros:
            if not self.nave.colide_com(meteoro):
                continue
            if self.nave.tempo_escudo > 0:
                # com escudo ativo, a nave destroi o que tocar
                self.efeito_impacto_escudo(meteoro, meteoro.tamanho)
                self.destruir_asteroide(meteoro)
            elif self.nave.tempo_invencivel <= 0:
                self.destruir_asteroide(meteoro)
                self.perder_vida()
            return

    def efeito_pegar_escudo(self):
        x, y = self.nave.x, self.nave.y
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=70, duracao=20))
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=120, duracao=34, raio_inicial=20))
        self.criar_explosao(x, y, COR_ITEM, 26)
        self.tremor = max(self.tremor, 6)

    def efeito_impacto_escudo(self, alvo, forca):
        """`alvo`: asteroide ou chefe atingido pelo escudo; `forca`: 1 (leve) a 3 (forte)."""
        # o ponto de impacto fica na borda do escudo, entre a nave e o alvo
        dx, dy = alvo.x - self.nave.x, alvo.y - self.nave.y
        distancia = max(1.0, (dx * dx + dy * dy) ** 0.5)
        x = self.nave.x + dx / distancia * 26
        y = self.nave.y + dy / distancia * 26
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=alvo.raio * 2.2, duracao=18))
        self.ondas.append(Onda(alvo.x, alvo.y, (255, 255, 255), raio_final=alvo.raio * 1.4, duracao=12))
        self.criar_explosao(x, y, COR_ITEM, 12 + forca * 4)
        self.nave.impacto_no_escudo()
        self.tremor = max(self.tremor, 4 + forca * 3)
        tocar(self.sons, "impacto_escudo")

    def perder_vida(self):
        self.vidas -= 1
        self.criar_explosao(self.nave.x, self.nave.y, COR_PRIMARIA, 30)
        self.ondas.append(Onda(self.nave.x, self.nave.y, COR_PRIMARIA, raio_final=90, duracao=26))
        self.tremor = max(self.tremor, 14)
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
        self.projeteis.clear()
        if self.pontuacao > self.recorde:
            self.recorde = self.pontuacao
            self.novo_recorde = True
            salvar_recorde(self.recorde)

    # ---------------------------------------------------------------- desenhar
    def desenhar(self):
        cena = self.cena
        self.fundo.desenhar(cena)

        for estrela in self.estrelas:
            estrela.desenhar(cena)
        for item in self.itens:
            item.desenhar(cena)
        for meteoro in self.meteoros:
            meteoro.desenhar(cena)
        if self.chefe:
            self.chefe.desenhar(cena)
        for projetil in self.projeteis:
            projetil.desenhar(cena)
        for tiro in self.tiros:
            tiro.desenhar(cena)
        for particula in self.particulas:
            particula.desenhar(cena)
        for onda in self.ondas:
            onda.desenhar(cena)

        if self.estado == ESTADO_JOGANDO:
            self.nave.desenhar(cena)

        self.tela.fill(self.fundo.galaxia.cor_fundo)
        self.tela.blit(cena, self.deslocamento_tremor())

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

    def deslocamento_tremor(self):
        if self.tremor <= 0:
            return (0, 0)
        forca = min(6, self.tremor * 0.6)
        return (random.uniform(-forca, forca), random.uniform(-forca, forca))

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
        subtitulo, titulo, cor = self.aviso_chefe
        interface.desenhar_aviso(
            self.tela, self.fontes, subtitulo, titulo, self.tempo_aviso_chefe, DURACAO_AVISO_CHEFE, cor,
            y=Y_AVISO_CHEFE,
        )
        nave = self.nave
        interface.desenhar_arma(
            self.tela, self.fontes, nave.arma, nave.arma == ARMA_EXPLOSIVA,
            nave.municao_explosiva, MUNICAO_EXPLOSIVA, nave.fracao_recarga,
        )
        if self.chefe:
            interface.desenhar_barra_chefe(
                self.tela, self.fontes, self.chefes_derrotados + 1, self.chefe.NOME,
                self.chefe.fracao_barra, self.chefe.COR,
            )

    # ------------------------------------------------------------------- loop
    def executar(self):
        while True:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)
