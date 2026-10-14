"""Loop principal e regras do jogo."""

import random
import sys

import pygame

from . import interface, melhorias
from .controle import (
    BOTAO_CONFIRMAR,
    BOTAO_MENU,
    BOTAO_PAUSA,
    BOTAO_TELA_CHEIA,
    BOTAO_VOLTAR,
    BOTOES_ARMA,
    BOTOES_CONTINUAR,
    BOTOES_DASH,
    BOTOES_INICIAR,
    BOTOES_MENU_BAIXO,
    BOTOES_MENU_CIMA,
    BOTOES_MENU_DIREITA,
    BOTOES_MENU_ESQUERDA,
    BOTOES_TIRO,
    Controles,
)
from .config import (
    ALTURA,
    ARMA_EXPLOSIVA,
    ASTEROIDES_INICIAIS,
    AUMENTO_VELOCIDADE_POR_NIVEL,
    COR_ASTEROIDE,
    COR_EXPLOSIVO,
    COR_ITEM,
    COR_JOGADOR2,
    COR_PERIGO,
    COR_PRIMARIA,
    COR_SECUNDARIA,
    COR_APAGADA,
    DANO_EXPLOSAO_CHEFE,
    DURACAO_AVISO_CHEFE,
    DURACAO_AVISO_NIVEL,
    DURACAO_ESCUDO,
    DURACAO_FIM_ROUND,
    DURACAO_INVENCIVEL,
    ESTADO_GAMEOVER,
    ESTADO_INICIO,
    ESTADO_JOGANDO,
    ESTADO_LOBBY,
    ESTADO_MELHORIA,
    ESTADO_MODOS,
    ESTADO_PAUSADO,
    ESTADO_ROUND,
    FATOR_NIVEL_COOP,
    FPS,
    INTERVALO_SPAWN_INICIAL,
    INTERVALO_ESCUDO,
    INTERVALO_SPAWN_MINIMO,
    LARGURA,
    MAX_ASTEROIDES,
    MAX_ASTEROIDES_CHEFE,
    MAX_ASTEROIDES_ONDA,
    MAX_ESCUDOS_NA_TELA,
    MULTIPLICADOR_SPAWN_CHEFE,
    NIVEIS_POR_CHEFE,
    NIVEIS_POR_MELHORIA,
    PONTOS_CHEFE,
    PONTOS_POR_NIVEL,
    PONTOS_POR_VIDA,
    RAIO_EXPLOSAO,
    REDUCAO_SPAWN_POR_NIVEL,
    ROUNDS_PARA_VENCER,
    VELOCIDADE_ASTEROIDE_INICIAL,
    VELOCIDADE_ASTEROIDE_TETO,
    VIDAS_MAXIMAS,
    VIDAS_REVIVER,
)
from .entidades import CHEFES, Estrela, Item, Meteoro, Nave, Onda, Particula, ProjetilChefe, Tiro
from .entidades.chefes import Chefe
from .dificuldades import DIFICULDADE_PADRAO, DIFICULDADES, Dificuldade, chave_recorde
from .galaxias import PlanoDeFundo, indice_galaxia
from .jogador import TECLADO_JOGADOR1, TECLADO_JOGADOR2, TECLAS_SOLO, Dispositivo, Jogador
from .modos import MODOS, Modo
from .recorde import carregar_recorde, salvar_recorde
from .sons import criar_sons, tocar

DURACAO_AVISO_GALAXIA = 3 * FPS
PONTOS_DRONE = 25
Y_AVISO_CHEFE = ALTURA / 2 - 80  # abaixo do aviso de nivel/galaxia, sem sobrepor
ATRASO_ESCOLHA = 30  # frames antes de aceitar a escolha (evita escolher sem querer atirando)
ATRASO_GAMEOVER = 75  # frames sem aceitar "jogar de novo" (quem estava atirando nao reinicia sem querer)
TECLAS_OPCAO = {pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2}
TECLAS_MODO = {
    pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3, pygame.K_5: 4,
    pygame.K_KP1: 0, pygame.K_KP2: 1, pygame.K_KP3: 2, pygame.K_KP4: 3, pygame.K_KP5: 4,
}
TECLAS_CONFIRMAR = (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)
TECLAS_PAUSA = (pygame.K_ESCAPE, pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER)


class Jogo:
    def __init__(self):
        pygame.init()
        # SCALED: a tela cheia amplia o jogo mantendo a resolucao interna
        self.tela: pygame.Surface = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED)
        self.tela_cheia: bool = False
        pygame.display.set_caption("SpaceMax")
        self.relogio: pygame.time.Clock = pygame.time.Clock()
        self.controles: Controles = Controles()

        self.fontes: interface.Fontes = interface.Fontes()
        self.sons: dict[str, pygame.mixer.Sound] | None = criar_sons()
        self.indice_modo: int = 0
        self.modo: Modo = MODOS[self.indice_modo]
        self.indice_dificuldade: int = DIFICULDADE_PADRAO
        self.dificuldade: Dificuldade = DIFICULDADES[self.indice_dificuldade]
        # recordes por modo e dificuldade (chave de chave_recorde)
        self.recordes: dict[str, int] = {
            chave_recorde(m, d): carregar_recorde(chave_recorde(m, d)) for m in MODOS if m.recorde for d in DIFICULDADES
        }
        # multiplayer: com o que cada jogador joga (None = vaga vazia na tela de jogadores)
        self.vagas: list[Dispositivo | None] = [None, None]
        self.fundo: PlanoDeFundo = PlanoDeFundo()
        self.estrelas: list[Estrela] = [Estrela() for _ in range(90)]
        self.frame: int = 0
        # a cena do jogo e desenhada aqui e copiada na tela com o deslocamento
        # do tremor; o HUD e desenhado depois, direto na tela, e nao treme
        self.cena: pygame.Surface = pygame.Surface((LARGURA, ALTURA))

        self.reiniciar()
        self.estado: str = ESTADO_INICIO

    @property
    def recorde(self) -> int:
        """Recorde do modo e da dificuldade atuais (0 nos modos competitivos, que nao tem recorde)."""
        return self.recordes.get(chave_recorde(self.modo, self.dificuldade), 0)

    @property
    def vidas_maximas(self) -> int:
        return VIDAS_MAXIMAS + self.dificuldade.vidas_extra

    @property
    def duracao_invencivel(self) -> int:
        return int(DURACAO_INVENCIVEL * self.dificuldade.invencivel)

    def intervalo_escudo(self) -> int:
        return int(random.randint(*INTERVALO_ESCUDO) * self.dificuldade.intervalo_escudo)

    @property
    def vivos(self) -> list[Jogador]:
        return [j for j in self.jogadores if j.vivo]

    def pontos_totais(self) -> int:
        return sum(j.pontuacao for j in self.jogadores)

    def reiniciar(self):
        self.jogadores: list[Jogador] = self.criar_jogadores()
        self.meteoros: list[Meteoro] = []
        self.tiros: list[Tiro] = []
        self.itens: list[Item] = []
        self.particulas: list[Particula] = []
        self.ondas: list[Onda] = []
        self.chefe: Chefe | None = None
        self.ultimo_chefe: Chefe | None = None
        self.projeteis: list[ProjetilChefe] = []
        self.chefes_derrotados: int = 0
        self.aviso_chefe: tuple[str, str, tuple[int, int, int]] = ("", "", COR_PRIMARIA)
        self.tempo_aviso_chefe: int = 0
        self.recarga_som_chefe: int = 0
        self.tremor: int = 0
        self.nivel: int = 1
        self.novo_recorde: bool = False
        self.tempo_aviso_nivel: int = 0
        self.tempo_aviso_galaxia: int = DURACAO_AVISO_GALAXIA
        self.frames_ate_proximo_spawn: int = INTERVALO_SPAWN_INICIAL
        self.tempo_ate_proximo_item: int = self.intervalo_escudo() // 2
        self.jogador_melhoria: Jogador | None = None  # de quem e a escolha de melhoria aberta
        self.opcoes_melhoria: list[melhorias.Melhoria] = []
        self.selecao_melhoria: int = 0
        self.tempo_tela_melhoria: int = 0
        # multiplayer
        self.tempo_partida: int = 0  # frames de jogo (no duelo, do round atual)
        self.round: int = 1
        self.tempo_round: int = 0
        self.vencedor: Jogador | None = None  # quem venceu a partida (None = empate / sem vencedor)
        self.vencedor_round: Jogador | None = None
        self.atraso_gameover: int = 0

        self.fundo.ir_para(0, com_transicao=False)
        self.tingir_estrelas()
        self.lancar_onda()

    # ---------------------------------------------------------------- jogadores
    def criar_nave(self, indice) -> Nave:
        cor = COR_JOGADOR2 if indice == 1 else COR_PRIMARIA
        if not self.modo.multi:
            return Nave(cor=cor)
        if self.modo.rounds:  # duelo: um de cada lado, de frente um para o outro
            x = LARGURA * (0.15 if indice == 0 else 0.85)
            return Nave(x, ALTURA / 2, 90 if indice == 0 else 270, cor, indice)
        return Nave(LARGURA * (0.35 if indice == 0 else 0.65), ALTURA / 2, 0.0, cor, indice)

    def criar_jogadores(self) -> list[Jogador]:
        if self.modo.multi:  # sem escolha feita, os dois jogam no teclado
            padrao = (TECLADO_JOGADOR1, TECLADO_JOGADOR2)
            dispositivos = [vaga or padrao[i] for i, vaga in enumerate(self.vagas)]
        else:  # solo: teclado completo e qualquer controle
            dispositivos = [Dispositivo("SOLO", TECLAS_SOLO)]
        jogadores = []
        for indice, dispositivo in enumerate(dispositivos):
            jogador = Jogador(indice, self.criar_nave(indice), dispositivo.teclas, self.vidas_iniciais(), dispositivo.controle)
            jogador.nave.reaparecer(DURACAO_INVENCIVEL // 2)
            jogadores.append(jogador)
        return jogadores

    def vidas_iniciais(self) -> int:
        return self.modo.vidas + self.dificuldade.vidas_extra

    def nome_jogador(self, jogador) -> str:
        return f"JOGADOR {jogador.indice + 1}"

    def alvo_mais_proximo(self, x, y) -> tuple[float, float]:
        """Posicao da nave viva mais perto de (x, y): para onde os chefes e misseis miram."""
        vivos = self.vivos
        if not vivos:
            return LARGURA / 2, ALTURA / 2
        nave = min(vivos, key=lambda j: (j.nave.x - x) ** 2 + (j.nave.y - y) ** 2).nave
        return nave.x, nave.y

    # ------------------------------------------------------------ dificuldade
    def calcular_nivel(self):
        if self.modo.segundos_por_nivel:  # modos competitivos: o nivel sobe com o tempo
            return 1 + self.tempo_partida // (self.modo.segundos_por_nivel * FPS)
        fator = FATOR_NIVEL_COOP if self.modo.multi else 1
        return 1 + int(self.pontos_totais() // (PONTOS_POR_NIVEL * fator))

    def atualizar_nivel(self):
        if self.chefe:  # durante a luta contra o chefe o nivel fica congelado
            return
        novo_nivel = self.calcular_nivel()
        if novo_nivel <= self.nivel:
            return
        if self.modo.progressao:
            # a escolha abre no fim do frame (pode estar no meio das colisoes aqui)
            novas = novo_nivel // NIVEIS_POR_MELHORIA - self.nivel // NIVEIS_POR_MELHORIA
            for jogador in self.vivos:
                jogador.melhorias_pendentes += novas
        self.nivel = novo_nivel
        tocar(self.sons, "nivel")

        # a cada 3 niveis o jogador chega a uma nova galaxia
        if self.fundo.ir_para(indice_galaxia(self.nivel)):
            self.tingir_estrelas()
            self.tempo_aviso_galaxia = DURACAO_AVISO_GALAXIA
            self.tempo_aviso_nivel = 0
        else:
            self.tempo_aviso_nivel = DURACAO_AVISO_NIVEL

        if self.modo.progressao and self.nivel >= NIVEIS_POR_CHEFE * (self.chefes_derrotados + 1):
            self.iniciar_chefe()

    def velocidade_asteroide(self):
        velocidade = VELOCIDADE_ASTEROIDE_INICIAL + (self.nivel - 1) * AUMENTO_VELOCIDADE_POR_NIVEL
        return min(VELOCIDADE_ASTEROIDE_TETO, velocidade) * self.dificuldade.velocidade_asteroide

    def intervalo_spawn(self):
        intervalo = INTERVALO_SPAWN_INICIAL - (self.nivel - 1) * REDUCAO_SPAWN_POR_NIVEL
        return int(max(INTERVALO_SPAWN_MINIMO, intervalo) * self.dificuldade.intervalo_spawn)

    def lancar_onda(self):
        quantidade = min(MAX_ASTEROIDES_ONDA, ASTEROIDES_INICIAIS + (self.nivel - 1) // 2)
        quantidade = max(2, round(quantidade * self.dificuldade.asteroides))
        for _ in range(quantidade):
            self.meteoros.append(Meteoro.na_borda(self.velocidade_asteroide()))

    # ------------------------------------------------------------------ chefes
    def iniciar_chefe(self):
        """Chefe diferente a cada vez, cada um mais forte que o anterior; depois do ultimo vem um sorteado."""
        indice = self.chefes_derrotados
        if indice < len(CHEFES):
            classe = CHEFES[indice]
        else:  # depois do nivel 100: chefe aleatorio, sem repetir o anterior
            anterior = type(self.ultimo_chefe) if self.ultimo_chefe else None
            classe = random.choice([c for c in CHEFES if c is not anterior])
        Chefe.ajuste_vida = self.dificuldade.vida_chefe
        Chefe.ajuste_ritmo = self.dificuldade.ritmo_chefe
        Chefe.ajuste_velocidade = self.dificuldade.velocidade_projetil
        self.chefe = classe(ciclo=indice / len(CHEFES))
        self.ultimo_chefe = self.chefe
        self.mostrar_aviso_chefe(f"ALERTA  ·  CHEFE {indice + 1:02d}", self.chefe.NOME, self.chefe.COR)
        self.tempo_aviso_nivel = 0
        tocar(self.sons, "alerta")

    def mostrar_aviso_chefe(self, subtitulo, titulo, cor):
        """Aviso grande no centro (chefes e tambem rounds, revives...)."""
        self.aviso_chefe = (subtitulo, titulo, cor)
        self.tempo_aviso_chefe = DURACAO_AVISO_CHEFE

    def atualizar_chefe(self):
        novos = []
        for projetil in self.projeteis:
            if projetil.guiado:
                projetil.alvo = self.alvo_mais_proximo(projetil.x, projetil.y)
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
        self.chefe.definir_alvo(*self.alvo_mais_proximo(self.chefe.x, self.chefe.y))
        self.chefe.atualizar()
        if self.chefe.som_pendente:
            tocar(self.sons, self.chefe.som_pendente)
            self.chefe.som_pendente = None
        disparos = self.chefe.atacar()
        if disparos:
            self.projeteis.extend(disparos)
            # espirais disparam quase todo frame: limita o som para nao virar ruido
            if self.recarga_som_chefe <= 0:
                tocar(self.sons, "tiro_chefe")
                self.recarga_som_chefe = 12

    def danificar_chefe(self, quantidade, x, y):
        if not self.chefe.receber_dano(quantidade, x, y):
            return
        self.criar_explosao(x, y, self.chefe.COR, 4)
        tocar(self.sons, "acerto_chefe")
        if self.chefe.morto():
            self.derrotar_chefe()

    def derrotar_chefe(self):
        chefe = self.chefe
        self.chefe = None
        self.chefes_derrotados += 1
        for jogador in self.vivos:  # no coop a recompensa e de cada um
            self.somar_pontos(jogador, PONTOS_CHEFE)

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
        # o nivel estava congelado e pode saltar varios de uma vez agora;
        # a recompensa e uma unica melhoria por jogador, mesmo que o salto passe por um multiplo de 6
        pendentes = [j.melhorias_pendentes for j in self.jogadores]
        self.atualizar_nivel()
        for jogador, antes in zip(self.jogadores, pendentes):
            jogador.melhorias_pendentes = antes + (1 if jogador.vivo else 0)

    # --------------------------------------------------------------- melhorias
    def abrir_melhoria(self):
        """Abre a escolha do proximo jogador vivo com melhoria pendente (um de cada vez)."""
        jogador = next((j for j in self.vivos if j.melhorias_pendentes > 0), None)
        if jogador is None:
            return
        opcoes = melhorias.sortear_opcoes(jogador.nave.melhorias, jogador.vidas < self.vidas_maximas)
        if not opcoes:  # tudo no maximo
            jogador.melhorias_pendentes = 0
            return
        self.jogador_melhoria = jogador
        self.opcoes_melhoria = opcoes
        self.estado = ESTADO_MELHORIA
        self.selecao_melhoria = 0
        self.tempo_tela_melhoria = 0
        tocar(self.sons, "melhoria")

    def mover_selecao(self, direcao):
        self.selecao_melhoria = (self.selecao_melhoria + direcao) % len(self.opcoes_melhoria)
        tocar(self.sons, "selecao")

    def escolher_melhoria(self, indice):
        if self.tempo_tela_melhoria < ATRASO_ESCOLHA or not 0 <= indice < len(self.opcoes_melhoria):
            return
        jogador = self.jogador_melhoria
        melhoria = self.opcoes_melhoria[indice]
        jogador.nave.aplicar_melhoria(melhoria.chave)
        if melhoria.chave == "reparo":
            jogador.vidas = min(self.vidas_maximas, jogador.vidas + 1)
        jogador.melhorias_pendentes -= 1
        self.estado = ESTADO_JOGANDO
        x, y = jogador.nave.x, jogador.nave.y
        self.ondas.append(Onda(x, y, jogador.cor, raio_final=80, duracao=22))
        self.criar_explosao(x, y, jogador.cor, 18)
        tocar(self.sons, "item")

    def tingir_estrelas(self):
        for estrela in self.estrelas:
            estrela.tingir(self.fundo.galaxia.cor_estrelas)

    # ------------------------------------------------------------------- modos
    def mover_modo(self, direcao):
        self.indice_modo = (self.indice_modo + direcao) % len(MODOS)
        tocar(self.sons, "selecao")

    def mover_dificuldade(self, direcao):
        self.indice_dificuldade = (self.indice_dificuldade + direcao) % len(DIFICULDADES)
        tocar(self.sons, "selecao")

    def abrir_menu_modos(self):
        self.estado = ESTADO_MODOS
        tocar(self.sons, "selecao")

    def confirmar_modo(self):
        """Solo comeca direto; os modos de 2 jogadores passam pela escolha de quem joga com o que."""
        if MODOS[self.indice_modo].multi:
            self.abrir_lobby()
        else:
            self.comecar()

    # ------------------------------------------------------ tela de jogadores
    def dispositivo_controle(self, instance_id) -> Dispositivo:
        return Dispositivo(self.controles.nome_de(instance_id), controle=instance_id)

    def vaga_de(self, dispositivo) -> int | None:
        return next((i for i, vaga in enumerate(self.vagas) if vaga == dispositivo), None)

    def vagas_completas(self) -> bool:
        return all(vaga is not None for vaga in self.vagas)

    def vagas_validas(self) -> bool:
        """Todas as vagas preenchidas e nenhum controle escolhido foi desconectado."""
        return self.vagas_completas() and all(
            vaga.controle is None or vaga.controle in self.controles.conectados for vaga in self.vagas
        )

    def abrir_lobby(self):
        self.vagas = [
            vaga if vaga and (vaga.controle is None or vaga.controle in self.controles.conectados) else None
            for vaga in self.vagas
        ]
        self.estado = ESTADO_LOBBY
        tocar(self.sons, "selecao")

    def entrar(self, dispositivo, vaga=None):
        """Poe o dispositivo na vaga (sem `vaga`: na primeira livre). Se ja estiver numa, move ou troca."""
        atual = self.vaga_de(dispositivo)
        if vaga is None:
            if atual is not None:
                return
            vaga = next((i for i, v in enumerate(self.vagas) if v is None), None)
            if vaga is None:
                return
        if atual == vaga:
            return
        if atual is None:
            if self.vagas[vaga] is not None:
                return  # ocupada: quem esta nela tem que sair ou trocar
            self.vagas[vaga] = dispositivo
        else:
            self.vagas[atual], self.vagas[vaga] = self.vagas[vaga], self.vagas[atual]
        tocar(self.sons, "selecao")

    def sair_da_vaga(self, dispositivo):
        atual = self.vaga_de(dispositivo)
        if atual is not None:
            self.vagas[atual] = None
            tocar(self.sons, "troca_arma")

    def iniciar_do_lobby(self):
        if self.vagas_completas():
            self.comecar()

    def jogar_de_novo(self):
        """Mesmo modo e mesmos jogadores; se um controle sumiu, volta a escolher os jogadores."""
        if self.modo.multi and not self.vagas_validas():
            self.abrir_lobby()
        else:
            self.comecar()

    # ----------------------------------------------------------------- eventos
    def processar_eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.sair()

            self.controles.processar_evento(evento)
            if evento.type == pygame.KEYDOWN:
                self.tecla(evento)
            elif evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1:
                self.clique(evento.pos)
            elif evento.type == pygame.CONTROLLERBUTTONDOWN:
                self.botao_controle(evento.button, evento.instance_id)
            elif evento.type in (pygame.CONTROLLERDEVICEREMOVED, pygame.WINDOWFOCUSLOST):
                if evento.type == pygame.CONTROLLERDEVICEREMOVED:
                    self.sair_da_vaga(self.dispositivo_controle(evento.instance_id))
                self.pausar()  # controle desconectou ou a janela perdeu o foco

            if self.estado == ESTADO_MELHORIA:
                direcao = self.controles.navegacao_analogico(evento)
                if direcao:
                    self.mover_selecao(direcao)
            elif self.estado == ESTADO_MODOS:
                direcao = self.controles.navegacao_analogico(evento, vertical=True)
                if direcao:
                    self.mover_modo(direcao)
                direcao = self.controles.navegacao_analogico(evento)
                if direcao:
                    self.mover_dificuldade(direcao)
            elif self.estado == ESTADO_LOBBY:
                direcao = self.controles.navegacao_analogico(evento)
                if direcao:  # analogico para a esquerda = jogador 1, para a direita = jogador 2
                    self.entrar(self.dispositivo_controle(evento.instance_id), 0 if direcao < 0 else 1)

    def tecla(self, evento):
        tecla = evento.key
        if tecla == pygame.K_F11 or (tecla == pygame.K_RETURN and evento.mod & pygame.KMOD_ALT):
            self.alternar_tela_cheia()
            return

        if self.estado == ESTADO_MELHORIA:
            if tecla in TECLAS_OPCAO:
                self.escolher_melhoria(TECLAS_OPCAO[tecla])
            elif tecla in (pygame.K_LEFT, pygame.K_a):
                self.mover_selecao(-1)
            elif tecla in (pygame.K_RIGHT, pygame.K_d):
                self.mover_selecao(1)
            elif tecla in TECLAS_CONFIRMAR:
                self.escolher_melhoria(self.selecao_melhoria)

        elif self.estado == ESTADO_PAUSADO:
            if tecla in (pygame.K_p, pygame.K_RETURN, pygame.K_KP_ENTER):
                self.continuar()
            elif tecla == pygame.K_ESCAPE:
                self.voltar_ao_inicio()

        elif self.estado == ESTADO_JOGANDO:
            if tecla in TECLAS_PAUSA:
                self.pausar()
                return
            for jogador in self.jogadores:
                if jogador.teclas is None:  # joga com controle
                    continue
                if tecla in jogador.teclas.tiro:
                    self.disparar(jogador)
                if tecla in jogador.teclas.dash:
                    self.usar_dash(jogador)
                if tecla in jogador.teclas.arma:
                    self.trocar_arma(jogador)

        elif self.estado == ESTADO_ROUND:
            pass  # intervalo curto entre rounds

        elif self.estado == ESTADO_MODOS:
            if tecla == pygame.K_ESCAPE:
                self.estado = ESTADO_INICIO
            elif tecla in (pygame.K_UP, pygame.K_w):
                self.mover_modo(-1)
            elif tecla in (pygame.K_DOWN, pygame.K_s):
                self.mover_modo(1)
            elif tecla in (pygame.K_LEFT, pygame.K_a):
                self.mover_dificuldade(-1)
            elif tecla in (pygame.K_RIGHT, pygame.K_d):
                self.mover_dificuldade(1)
            elif tecla in TECLAS_MODO:
                self.indice_modo = TECLAS_MODO[tecla]
                tocar(self.sons, "selecao")
            elif tecla in TECLAS_CONFIRMAR:
                self.confirmar_modo()

        elif self.estado == ESTADO_LOBBY:
            if tecla == pygame.K_ESCAPE:
                self.estado = ESTADO_MODOS
            elif tecla == pygame.K_SPACE:
                self.entrar(TECLADO_JOGADOR1)
            elif tecla == pygame.K_RSHIFT:
                self.entrar(TECLADO_JOGADOR2)
            elif tecla == pygame.K_a:
                self.entrar(TECLADO_JOGADOR1, 0)
            elif tecla == pygame.K_d:
                self.entrar(TECLADO_JOGADOR1, 1)
            elif tecla == pygame.K_LEFT:
                self.entrar(TECLADO_JOGADOR2, 0)
            elif tecla == pygame.K_RIGHT:
                self.entrar(TECLADO_JOGADOR2, 1)
            elif tecla == pygame.K_s:
                self.sair_da_vaga(TECLADO_JOGADOR1)
            elif tecla == pygame.K_DOWN:
                self.sair_da_vaga(TECLADO_JOGADOR2)
            elif tecla in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.iniciar_do_lobby()

        elif self.estado == ESTADO_GAMEOVER:
            if tecla == pygame.K_ESCAPE:
                self.sair()
            elif self.atraso_gameover <= 0:
                if tecla in TECLAS_CONFIRMAR:
                    self.jogar_de_novo()
                elif tecla == pygame.K_m:
                    self.voltar_ao_menu_modos()

        else:  # tela inicial
            if tecla == pygame.K_ESCAPE:
                self.sair()
            elif tecla in TECLAS_CONFIRMAR:
                self.abrir_menu_modos()

    def clique(self, posicao):
        if self.estado == ESTADO_JOGANDO:
            if not self.modo.multi:  # no multiplayer o mouse nao atira (cada um tem as suas teclas)
                self.disparar(self.jogadores[0])
        elif self.estado == ESTADO_MELHORIA:
            indice = interface.carta_em(posicao, len(self.opcoes_melhoria))
            if indice is not None:
                self.escolher_melhoria(indice)
        elif self.estado == ESTADO_MODOS:
            dificuldade = interface.dificuldade_em(posicao, len(DIFICULDADES))
            if dificuldade is not None:
                self.indice_dificuldade = dificuldade
                tocar(self.sons, "selecao")
                return
            indice = interface.modo_em(posicao, len(MODOS))
            if indice is not None:
                self.indice_modo = indice
                self.confirmar_modo()
        elif self.estado == ESTADO_INICIO:
            self.abrir_menu_modos()
        elif self.estado == ESTADO_GAMEOVER and self.atraso_gameover <= 0:
            self.jogar_de_novo()

    def jogador_do_controle(self, instance_id) -> Jogador | None:
        """Solo: qualquer controle e o jogador 1. Multi: cada controle e de quem o escolheu na tela de jogadores."""
        if not self.modo.multi:
            return self.jogadores[0]
        return next((j for j in self.jogadores if j.controle == instance_id), None)

    def botao_controle(self, botao, instance_id=None):
        if self.estado == ESTADO_MELHORIA:
            if botao in BOTOES_MENU_ESQUERDA:
                self.mover_selecao(-1)
            elif botao in BOTOES_MENU_DIREITA:
                self.mover_selecao(1)
            elif botao == BOTAO_CONFIRMAR:
                self.escolher_melhoria(self.selecao_melhoria)

        elif self.estado == ESTADO_PAUSADO:
            if botao in BOTOES_CONTINUAR:
                self.continuar()
            elif botao == BOTAO_MENU:
                self.voltar_ao_inicio()
            elif botao == BOTAO_TELA_CHEIA:
                self.alternar_tela_cheia()

        elif self.estado == ESTADO_JOGANDO:
            if botao == BOTAO_PAUSA:
                self.pausar()
                return
            jogador = self.jogador_do_controle(instance_id)
            if jogador is None:
                return
            if botao in BOTOES_TIRO:
                self.disparar(jogador)
            if botao in BOTOES_DASH:
                self.usar_dash(jogador)
            if botao in BOTOES_ARMA:
                self.trocar_arma(jogador)

        elif self.estado == ESTADO_ROUND:
            pass

        elif self.estado == ESTADO_MODOS:
            if botao in BOTOES_MENU_CIMA:
                self.mover_modo(-1)
            elif botao in BOTOES_MENU_BAIXO:
                self.mover_modo(1)
            elif botao in BOTOES_MENU_ESQUERDA:
                self.mover_dificuldade(-1)
            elif botao in BOTOES_MENU_DIREITA:
                self.mover_dificuldade(1)
            elif botao in BOTOES_INICIAR:
                self.confirmar_modo()
            elif botao in (BOTAO_VOLTAR, BOTAO_MENU):
                self.estado = ESTADO_INICIO
            elif botao == BOTAO_TELA_CHEIA:
                self.alternar_tela_cheia()

        elif self.estado == ESTADO_LOBBY:
            dispositivo = self.dispositivo_controle(instance_id)
            if botao in BOTOES_MENU_ESQUERDA:
                self.entrar(dispositivo, 0)  # direcional: esquerda = jogador 1, direita = jogador 2
            elif botao in BOTOES_MENU_DIREITA:
                self.entrar(dispositivo, 1)
            elif botao == BOTAO_CONFIRMAR:
                self.entrar(dispositivo)
            elif botao == BOTAO_PAUSA:  # START: comeca se ja estiver tudo pronto, senao entra
                if self.vagas_completas():
                    self.comecar()
                else:
                    self.entrar(dispositivo)
            elif botao in (BOTAO_VOLTAR, BOTAO_MENU):  # B: sai da vaga; sem vaga, volta
                if self.vaga_de(dispositivo) is not None:
                    self.sair_da_vaga(dispositivo)
                else:
                    self.estado = ESTADO_MODOS
            elif botao == BOTAO_TELA_CHEIA:
                self.alternar_tela_cheia()

        elif self.estado == ESTADO_GAMEOVER:
            if botao == BOTAO_TELA_CHEIA:
                self.alternar_tela_cheia()
            elif self.atraso_gameover <= 0:
                if botao in BOTOES_INICIAR:
                    self.jogar_de_novo()
                elif botao == BOTAO_MENU:
                    self.voltar_ao_menu_modos()

        else:  # tela inicial
            if botao == BOTAO_TELA_CHEIA:
                self.alternar_tela_cheia()
            elif botao in BOTOES_INICIAR:
                self.abrir_menu_modos()

    def comecar(self):
        self.modo = MODOS[self.indice_modo]
        self.dificuldade = DIFICULDADES[self.indice_dificuldade]
        self.reiniciar()
        if self.modo.rounds:
            self.mostrar_aviso_chefe(f"ROUND {self.round}", "LUTEM", COR_ITEM)
        self.estado = ESTADO_JOGANDO

    def pausar(self):
        if self.estado == ESTADO_JOGANDO:
            self.estado = ESTADO_PAUSADO
            tocar(self.sons, "pausa")

    def continuar(self):
        self.estado = ESTADO_JOGANDO
        tocar(self.sons, "pausa")

    def voltar_ao_inicio(self):
        """Abandona a partida (o recorde e salvo se tiver sido batido)."""
        self.registrar_recorde()
        self.reiniciar()
        self.estado = ESTADO_INICIO

    def voltar_ao_menu_modos(self):
        self.reiniciar()
        self.abrir_menu_modos()

    def alternar_tela_cheia(self):
        pygame.display.toggle_fullscreen()
        self.tela_cheia = not self.tela_cheia

    def disparar(self, jogador):
        nave = jogador.nave
        if jogador.vivo and nave.pode_atirar():
            tiros = nave.atirar()
            self.tiros.extend(tiros)
            tocar(self.sons, "tiro_explosivo" if tiros[0].EXPLOSIVO else "tiro")

    def trocar_arma(self, jogador):
        if self.estado == ESTADO_JOGANDO and jogador.vivo:
            jogador.nave.trocar_arma()
            tocar(self.sons, "troca_arma")

    def usar_dash(self, jogador):
        if self.estado == ESTADO_JOGANDO and jogador.vivo:
            jogador.nave.dash()
            tocar(self.sons, "dash")

    def sair(self):
        pygame.quit()
        sys.exit()

    # --------------------------------------------------------------- atualizar
    def atualizar(self):
        self.frame += 1
        if self.atraso_gameover > 0:
            self.atraso_gameover -= 1
        if self.estado == ESTADO_MELHORIA:
            self.tempo_tela_melhoria += 1
        if self.estado in (ESTADO_PAUSADO, ESTADO_MELHORIA):
            return  # tudo congelado
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

        if self.estado == ESTADO_ROUND:
            self.atualizar_intervalo_round()
            return
        if self.estado != ESTADO_JOGANDO:
            return

        self.tempo_partida += 1
        self.ler_controles()
        for jogador in self.vivos:
            nave = jogador.nave
            if self.chefe:  # ex.: gravidade da singularidade
                ax, ay = self.chefe.forca_sobre(nave)
                nave.vx += ax
                nave.vy += ay
            nave.atualizar()
            self.particulas.extend(nave.emitir_rastro())

        if self.tempo_aviso_nivel > 0:
            self.tempo_aviso_nivel -= 1
        if self.tempo_aviso_galaxia > 0:
            self.tempo_aviso_galaxia -= 1
        if self.tempo_aviso_chefe > 0:
            self.tempo_aviso_chefe -= 1

        if self.modo.segundos_por_nivel:
            self.atualizar_nivel()
        self.gerar_asteroides()
        self.gerar_itens()

        for tiro in self.tiros:
            tiro.atualizar()
            if tiro.EXPLOSIVO and tiro.expirou():
                self.explodir(tiro.x, tiro.y, tiro.dono)  # explode sozinho ao fim do alcance
        self.tiros = [t for t in self.tiros if not t.expirou()]

        for item in self.itens:
            item.atualizar()

        self.atualizar_chefe()

        self.checar_colisoes_tiro_meteoro()
        self.checar_tiros_drones()
        self.checar_colisoes_tiro_chefe()
        self.checar_tiros_jogadores()
        self.checar_colisao_nave()
        self.checar_ataques_chefe()

        self.itens = [i for i in self.itens if not i.expirou() and not i.coletado]

        self.verificar_fim()
        if self.estado == ESTADO_JOGANDO and any(j.melhorias_pendentes > 0 for j in self.vivos):
            self.abrir_melhoria()

    def ler_controles(self):
        teclas = pygame.key.get_pressed()
        for jogador in self.vivos:
            mapa, nave = jogador.teclas, jogador.nave

            def apertada(chaves):
                return mapa is not None and any(teclas[k] for k in getattr(mapa, chaves))

            giro_c, acelerando_c, freando_c, atirando_c = self.leitura_controle(jogador)
            giro = max(-1.0, min(1.0, (apertada("direita") - apertada("esquerda")) + giro_c))
            nave.girar(giro)  # 0 = soltou: o giro freia sozinho
            if apertada("cima") or acelerando_c:
                nave.acelerar()
            if apertada("baixo") or freando_c:
                nave.frear()
            if apertada("tiro") or atirando_c:
                self.disparar(jogador)

    def leitura_controle(self, jogador) -> tuple[float, bool, bool, bool]:
        """(giro, acelerando, freando, atirando) do controle do jogador. Solo: qualquer controle serve."""
        if self.modo.multi:
            if jogador.controle is None:  # joga no teclado
                return 0.0, False, False, False
            id_controle = jogador.controle
        else:
            id_controle = None
        c = self.controles
        return c.giro(id_controle), c.acelerando(id_controle), c.freando(id_controle), c.atirando(id_controle)

    def gerar_asteroides(self):
        # durante a luta contra o chefe os asteroides seguem vindo, um a um e mais espacados
        if self.chefe:
            intervalo = int(self.intervalo_spawn() * MULTIPLICADOR_SPAWN_CHEFE)
            limite = MAX_ASTEROIDES_CHEFE * self.dificuldade.asteroides
        else:
            if not self.meteoros:
                self.lancar_onda()
                self.frames_ate_proximo_spawn = self.intervalo_spawn()
                return
            intervalo = self.intervalo_spawn()
            limite = MAX_ASTEROIDES * self.dificuldade.asteroides

        self.frames_ate_proximo_spawn -= 1
        if self.frames_ate_proximo_spawn <= 0:
            self.frames_ate_proximo_spawn = intervalo
            if len(self.meteoros) < limite:
                self.meteoros.append(Meteoro.na_borda(self.velocidade_asteroide()))

    def gerar_itens(self):
        self.tempo_ate_proximo_item -= 1
        if self.tempo_ate_proximo_item <= 0:
            self.tempo_ate_proximo_item = self.intervalo_escudo()
            if len(self.itens) < MAX_ESCUDOS_NA_TELA:
                self.itens.append(Item())

    # ---------------------------------------------------------------- colisoes
    def checar_colisoes_tiro_meteoro(self):
        for tiro in self.tiros[:]:
            for meteoro in self.meteoros:
                if tiro.colide_com(meteoro):
                    self.tiros.remove(tiro)
                    if tiro.EXPLOSIVO:
                        self.explodir(tiro.x, tiro.y, tiro.dono)
                    else:
                        self.destruir_asteroide(meteoro, self.jogadores[tiro.dono])
                    break

    def checar_colisoes_tiro_chefe(self):
        for tiro in self.tiros[:]:
            if not self.chefe:
                return
            if tiro.EXPLOSIVO and (self.chefe.bloqueia(tiro) or self.chefe.atinge(tiro)):
                self.tiros.remove(tiro)
                self.explodir(tiro.x, tiro.y, tiro.dono)
            elif self.chefe.bloqueia(tiro):
                self.tiros.remove(tiro)
                self.criar_explosao(tiro.x, tiro.y, self.chefe.COR, 3)
                self.chefe.ao_bloquear(tiro)
            elif self.chefe.atinge(tiro):
                self.tiros.remove(tiro)
                self.danificar_chefe(1, tiro.x, tiro.y)

    def checar_tiros_drones(self):
        """Tiros da nave abatem os drones (projeteis destrutiveis) dos chefes."""
        for tiro in self.tiros[:]:
            for projetil in self.projeteis:
                if projetil.destrutivel and tiro.colide_com(projetil):
                    self.tiros.remove(tiro)
                    self.projeteis.remove(projetil)
                    projetil.abatido = True
                    self.criar_explosao(projetil.x, projetil.y, projetil.cor, 10)
                    self.somar_pontos(self.jogadores[tiro.dono], PONTOS_DRONE)
                    tocar(self.sons, "explosao")
                    if tiro.EXPLOSIVO:
                        self.explodir(tiro.x, tiro.y, tiro.dono)
                    break

    def checar_tiros_jogadores(self):
        """Duelo: tiros acertam a nave do outro jogador (o escudo segura, a invencibilidade deixa passar)."""
        if not self.modo.pvp:
            return
        for tiro in self.tiros[:]:
            for jogador in self.vivos:
                nave = jogador.nave
                if jogador.indice == tiro.dono or not tiro.colide_com(nave):
                    continue
                if nave.tempo_escudo > 0:
                    self.tiros.remove(tiro)
                    self.ondas.append(Onda(tiro.x, tiro.y, COR_ITEM, raio_final=18, duracao=12))
                    nave.impacto_no_escudo()
                    tocar(self.sons, "impacto_escudo")
                    if tiro.EXPLOSIVO:
                        self.explodir(tiro.x, tiro.y, tiro.dono)
                elif nave.tempo_invencivel <= 0:
                    self.tiros.remove(tiro)
                    if tiro.EXPLOSIVO:
                        self.explodir(tiro.x, tiro.y, tiro.dono)  # a explosao e que fere
                    else:
                        self.perder_vida(jogador)
                else:
                    continue
                break

    def explodir(self, x, y, dono=None):
        """Tiro explosivo: quebra asteroides, apaga projeteis e fere o chefe dentro da area.

        `dono`: indice do jogador que atirou (leva os pontos; no duelo a explosao fere o outro)."""
        atirador = self.jogadores[dono] if dono is not None else None
        self.ondas.append(Onda(x, y, COR_EXPLOSIVO, raio_final=RAIO_EXPLOSAO, duracao=22))
        self.ondas.append(Onda(x, y, (255, 230, 200), raio_final=RAIO_EXPLOSAO * 0.6, duracao=14))
        self.criar_explosao(x, y, COR_EXPLOSIVO, 40)
        self.tremor = max(self.tremor, 10)
        tocar(self.sons, "explosao_grande")

        def na_area(entidade):
            return ((entidade.x - x) ** 2 + (entidade.y - y) ** 2) ** 0.5 < RAIO_EXPLOSAO + entidade.raio

        for meteoro in [m for m in self.meteoros if na_area(m)]:
            self.destruir_asteroide(meteoro, atirador)
        for projetil in [p for p in self.projeteis if na_area(p)]:
            self.projeteis.remove(projetil)
            projetil.abatido = True
            self.criar_explosao(projetil.x, projetil.y, projetil.cor, 2)
        if self.chefe and na_area(self.chefe):
            self.danificar_chefe(DANO_EXPLOSAO_CHEFE, x, y)
        if self.modo.pvp:
            for jogador in self.vivos:
                nave = jogador.nave
                if jogador is atirador or not na_area(nave):
                    continue
                if nave.tempo_escudo > 0:
                    nave.impacto_no_escudo()
                    self.ondas.append(Onda(nave.x, nave.y, COR_ITEM, raio_final=34, duracao=14))
                elif nave.tempo_invencivel <= 0:
                    self.perder_vida(jogador)

    def checar_ataques_chefe(self):
        """Projeteis e corpo do chefe contra as naves (o escudo protege dos dois)."""
        if self.estado != ESTADO_JOGANDO:
            return
        for jogador in self.vivos:
            self.ataques_chefe_sobre(jogador)

    def ataques_chefe_sobre(self, jogador):
        nave = jogador.nave
        for projetil in self.projeteis[:]:
            if not nave.colide_com(projetil):
                continue
            self.projeteis.remove(projetil)
            projetil.abatido = True
            if nave.tempo_escudo > 0:
                self.ondas.append(Onda(projetil.x, projetil.y, COR_ITEM, raio_final=18, duracao=12))
                nave.impacto_no_escudo()
            elif nave.tempo_invencivel <= 0:
                self.perder_vida(jogador)
                return

        chefe = self.chefe
        if not chefe:
            return
        if chefe.ataque_continuo(nave):  # laser: o escudo segura, sem escudo custa uma vida
            if nave.tempo_escudo > 0:
                if self.frame % 4 == 0:
                    self.criar_explosao(nave.x, nave.y, chefe.COR, 3)
                    nave.impacto_no_escudo()
            elif nave.tempo_invencivel <= 0:
                self.perder_vida(jogador)
                return
        if not chefe.atinge(nave):
            return
        if nave.tempo_escudo > 0:
            # o escudo empurra a nave para fora e causa dano no chefe
            self.efeito_impacto_escudo(jogador, chefe, 3)
            self.empurrar_nave(chefe, nave)
            self.danificar_chefe(3, nave.x, nave.y)
        elif nave.tempo_invencivel <= 0:
            self.perder_vida(jogador)

    def empurrar_nave(self, chefe, nave):
        # empurra para fora da parte tocada (corpo, satelite, gemeo...)
        cx, cy, raio = chefe.ponto_contato(nave)
        dx, dy = nave.x - cx, nave.y - cy
        distancia = max(1.0, (dx * dx + dy * dy) ** 0.5)
        ux, uy = dx / distancia, dy / distancia
        afastamento = raio + nave.raio + 4
        nave.x, nave.y = cx + ux * afastamento, cy + uy * afastamento
        nave.vx, nave.vy = ux * 7, uy * 7

    def somar_pontos(self, jogador, pontos):
        """Soma pontos e da uma vida extra a cada PONTOS_POR_VIDA (ate o maximo de vidas)."""
        if not self.modo.pontua:
            return
        jogador.pontuacao += pontos
        while jogador.pontuacao >= jogador.pontos_proxima_vida:
            jogador.pontos_proxima_vida += PONTOS_POR_VIDA
            if jogador.vivo and jogador.vidas < self.vidas_maximas:
                jogador.vidas += 1
                self.ondas.append(Onda(jogador.nave.x, jogador.nave.y, jogador.cor, raio_final=60, duracao=20))
                tocar(self.sons, "item")

    def destruir_asteroide(self, meteoro, jogador=None):
        """Remove o asteroide, da os pontos a `jogador` (se houver) e coloca os fragmentos no lugar."""
        self.meteoros.remove(meteoro)
        self.meteoros.extend(meteoro.quebrar())
        if jogador is not None:
            self.somar_pontos(jogador, meteoro.pontos)
        self.criar_explosao(meteoro.x, meteoro.y, COR_ASTEROIDE, 6 + meteoro.tamanho * 5)
        tocar(self.sons, "explosao")
        self.atualizar_nivel()

    def checar_colisao_nave(self):
        for jogador in self.vivos:
            nave = jogador.nave
            for item in self.itens:
                if not item.coletado and nave.colide_com(item):
                    item.coletado = True
                    nave.ativar_escudo(DURACAO_ESCUDO + nave.bonus_escudo)
                    self.efeito_pegar_escudo(jogador)
                    tocar(self.sons, "item")
                    self.reviver_parceiro(jogador)

            for meteoro in self.meteoros:
                if not nave.colide_com(meteoro):
                    continue
                if nave.tempo_escudo > 0:
                    # com escudo ativo, a nave destroi o que tocar
                    self.efeito_impacto_escudo(jogador, meteoro, meteoro.tamanho)
                    self.destruir_asteroide(meteoro, jogador)
                elif nave.tempo_invencivel <= 0:
                    self.destruir_asteroide(meteoro)
                    self.perder_vida(jogador)
                break

    def reviver_parceiro(self, coletor):
        """Coop: o escudo coletado traz de volta o parceiro eliminado."""
        if not self.modo.reviver:
            return
        for outro in self.jogadores:
            if outro is coletor or outro.vivo:
                continue
            outro.vidas = VIDAS_REVIVER
            outro.tempo_eliminado = None
            outro.nave.tempo_escudo = 0
            outro.nave.reaparecer(self.duracao_invencivel)
            x, y = outro.nave.x, outro.nave.y
            self.ondas.append(Onda(x, y, outro.cor, raio_final=90, duracao=26))
            self.ondas.append(Onda(x, y, (255, 255, 255), raio_final=50, duracao=16))
            self.criar_explosao(x, y, outro.cor, 30)
            self.mostrar_aviso_chefe("O ESCUDO REVIVEU", f"{self.nome_jogador(outro)} VOLTOU", outro.cor)
            tocar(self.sons, "melhoria")

    def efeito_pegar_escudo(self, jogador):
        x, y = jogador.nave.x, jogador.nave.y
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=70, duracao=20))
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=120, duracao=34, raio_inicial=20))
        self.criar_explosao(x, y, COR_ITEM, 26)
        self.tremor = max(self.tremor, 6)

    def efeito_impacto_escudo(self, jogador, alvo, forca):
        """`alvo`: asteroide ou chefe atingido pelo escudo; `forca`: 1 (leve) a 3 (forte)."""
        nave = jogador.nave
        # o ponto de impacto fica na borda do escudo, entre a nave e o alvo
        dx, dy = alvo.x - nave.x, alvo.y - nave.y
        distancia = max(1.0, (dx * dx + dy * dy) ** 0.5)
        x = nave.x + dx / distancia * 26
        y = nave.y + dy / distancia * 26
        self.ondas.append(Onda(x, y, COR_ITEM, raio_final=alvo.raio * 2.2, duracao=18))
        self.ondas.append(Onda(alvo.x, alvo.y, (255, 255, 255), raio_final=alvo.raio * 1.4, duracao=12))
        self.criar_explosao(x, y, COR_ITEM, 12 + forca * 4)
        nave.impacto_no_escudo()
        self.tremor = max(self.tremor, 4 + forca * 3)
        tocar(self.sons, "impacto_escudo")

    def perder_vida(self, jogador):
        nave = jogador.nave
        jogador.vidas -= 1
        self.criar_explosao(nave.x, nave.y, jogador.cor, 30)
        self.ondas.append(Onda(nave.x, nave.y, jogador.cor, raio_final=90, duracao=26))
        self.tremor = max(self.tremor, 14)
        tocar(self.sons, "colisao")
        if jogador.vidas <= 0:
            # eliminado: o fim da partida / do round e decidido no fim do frame (verificar_fim)
            jogador.tempo_eliminado = self.tempo_partida
            nave.tempo_escudo = 0
        else:
            nave.reaparecer(self.duracao_invencivel)

    def criar_explosao(self, x, y, cor, quantidade):
        for _ in range(quantidade):
            self.particulas.append(Particula(x, y, cor))

    # --------------------------------------------------------- fim de partida
    def verificar_fim(self):
        """Regras de fim de cada modo; chamado no fim de cada frame de jogo."""
        modo = self.modo
        vivos = self.vivos
        if not modo.multi or modo.reviver:  # solo e coop: acabou quando ninguem restar
            if not vivos:
                self.fim_de_jogo()
        elif modo.rounds:  # duelo: o round acaba quando so um sobra
            if len(vivos) < 2:
                self.fim_do_round(vivos[0] if vivos else None)
        elif modo.duracao:  # corrida de pontos
            lider = self.lider_em_pontos()
            if not vivos or self.tempo_partida >= modo.duracao:
                self.fim_de_jogo(lider)
            elif len(vivos) == 1 and lider is vivos[0]:
                self.fim_de_jogo(lider)  # o ultimo vivo ja esta na frente: nao precisa esperar o tempo
        elif len(vivos) < 2:  # sobrevivencia: quem sobrar (ou durar mais) vence
            if vivos:
                self.fim_de_jogo(vivos[0])
            else:
                a, b = self.jogadores
                self.fim_de_jogo(None if a.tempo_eliminado == b.tempo_eliminado
                                 else max(self.jogadores, key=lambda j: j.tempo_eliminado))

    def lider_em_pontos(self) -> Jogador | None:
        """Quem tem mais pontos (None se empatados)."""
        a, b = self.jogadores
        if a.pontuacao == b.pontuacao:
            return None
        return a if a.pontuacao > b.pontuacao else b

    def fim_do_round(self, vencedor):
        self.estado = ESTADO_ROUND
        self.tempo_round = DURACAO_FIM_ROUND
        self.vencedor_round = vencedor
        self.tiros.clear()
        self.projeteis.clear()
        self.tempo_aviso_nivel = 0
        self.tempo_aviso_galaxia = 0
        if vencedor is None:
            self.mostrar_aviso_chefe(f"ROUND {self.round}", "EMPATE", COR_ITEM)
            return
        vencedor.rounds_ganhos += 1
        partida = vencedor.rounds_ganhos >= ROUNDS_PARA_VENCER
        self.mostrar_aviso_chefe(
            f"ROUND {self.round}", f"{self.nome_jogador(vencedor)} {'VENCE A PARTIDA' if partida else 'VENCE'}",
            vencedor.cor,
        )
        tocar(self.sons, "nivel")

    def atualizar_intervalo_round(self):
        if self.tempo_aviso_chefe > 0:
            self.tempo_aviso_chefe -= 1
        for jogador in self.vivos:  # a nave vencedora segue com a inercia
            jogador.nave.atualizar()
            self.particulas.extend(jogador.nave.emitir_rastro())
        self.tempo_round -= 1
        if self.tempo_round > 0:
            return
        vencedor = self.vencedor_round
        if vencedor and vencedor.rounds_ganhos >= ROUNDS_PARA_VENCER:
            self.fim_de_jogo(vencedor)
        else:
            if vencedor:
                self.round += 1
            self.iniciar_round()

    def iniciar_round(self):
        """Novo round do duelo: naves novas nas posicoes iniciais e arena limpa."""
        for jogador in self.jogadores:
            jogador.nave = self.criar_nave(jogador.indice)
            jogador.nave.reaparecer(DURACAO_INVENCIVEL // 2)
            jogador.vidas = self.vidas_iniciais()
            jogador.tempo_eliminado = None
        self.meteoros.clear()
        self.tiros.clear()
        self.itens.clear()
        self.projeteis.clear()
        self.tempo_partida = 0
        self.nivel = 1
        self.frames_ate_proximo_spawn = INTERVALO_SPAWN_INICIAL
        self.tempo_ate_proximo_item = self.intervalo_escudo() // 2
        self.lancar_onda()
        self.estado = ESTADO_JOGANDO
        self.mostrar_aviso_chefe(f"ROUND {self.round}", "LUTEM", COR_ITEM)

    def fim_de_jogo(self, vencedor=None):
        self.vencedor = vencedor
        self.estado = ESTADO_GAMEOVER
        self.atraso_gameover = ATRASO_GAMEOVER
        self.tiros.clear()
        self.itens.clear()
        self.projeteis.clear()
        self.registrar_recorde()

    def registrar_recorde(self):
        """Modos com recorde guardam os pontos da partida (no coop, da equipe)."""
        if not self.modo.recorde:
            return
        pontos = self.pontos_totais()
        if pontos > self.recorde:
            chave = chave_recorde(self.modo, self.dificuldade)
            self.recordes[chave] = pontos
            self.novo_recorde = True
            salvar_recorde(pontos, chave)

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

        if self.estado in (ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_MELHORIA, ESTADO_ROUND):
            for jogador in self.vivos:
                jogador.nave.desenhar(cena)

        self.tela.fill(self.fundo.galaxia.cor_fundo)
        self.tela.blit(cena, self.deslocamento_tremor())

        if self.estado == ESTADO_INICIO:
            interface.desenhar_tela_inicio(
                self.tela, self.fontes, self.recordes[chave_recorde(MODOS[0], DIFICULDADES[self.indice_dificuldade])],
                self.frame, self.controles.nome(), DIFICULDADES[self.indice_dificuldade].nome,
            )
        elif self.estado == ESTADO_MODOS:
            interface.desenhar_tela_modos(
                self.tela, self.fontes, MODOS, self.indice_modo, len(self.controles.conectados),
                DIFICULDADES, self.indice_dificuldade,
            )
        elif self.estado == ESTADO_LOBBY:
            livres = [
                self.controles.nome_de(i) for i in self.controles.conectados
                if self.dispositivo_controle(i) not in self.vagas
            ]
            interface.desenhar_tela_jogadores(
                self.tela, self.fontes, MODOS[self.indice_modo].nome, self.vagas, livres, self.frame
            )
        else:
            self.desenhar_hud()
            if self.estado == ESTADO_PAUSADO:
                interface.desenhar_tela_pausa(
                    self.tela, self.fontes, self.listas_melhorias(), self.tela_cheia, self.frame
                )
            if self.estado == ESTADO_MELHORIA:
                jogador = self.jogador_melhoria
                interface.desenhar_tela_melhoria(
                    self.tela, self.fontes, self.nivel, self.opcoes_melhoria, jogador.nave.melhorias,
                    self.selecao_melhoria, self.tempo_tela_melhoria >= ATRASO_ESCOLHA,
                    (self.nome_jogador(jogador), jogador.cor) if self.modo.multi else None,
                )
            if self.estado == ESTADO_GAMEOVER:
                self.desenhar_fim_de_jogo()

        pygame.display.flip()

    def deslocamento_tremor(self):
        if self.tremor <= 0:
            return (0, 0)
        forca = min(6, self.tremor * 0.6)
        return (random.uniform(-forca, forca), random.uniform(-forca, forca))

    def listas_melhorias(self):
        """Melhorias de cada jogador para a tela de pausa (nenhuma nos modos sem progressao)."""
        if not self.modo.progressao:
            return []
        if not self.modo.multi:
            return [(None, COR_PRIMARIA, self.jogadores[0].nave.melhorias)]
        return [(f"J{j.indice + 1}", j.cor, j.nave.melhorias) for j in self.jogadores]

    def desenhar_hud(self):
        galaxia = self.fundo.galaxia
        setor = self.fundo.indice + 1
        if self.modo.multi:
            interface.desenhar_hud_multi(
                self.tela, self.fontes, self.placares(), setor, galaxia.nome, self.nivel, self.linhas_centro_hud(),
            )
        else:
            jogador = self.jogadores[0]
            interface.desenhar_hud(
                self.tela,
                self.fontes,
                jogador.pontuacao,
                self.recorde,
                self.nivel,
                jogador.vidas,
                setor,
                galaxia.nome,
            )
        if self.estado not in (ESTADO_JOGANDO, ESTADO_PAUSADO, ESTADO_MELHORIA, ESTADO_ROUND):
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
        for jogador in self.vivos:
            nave = jogador.nave
            direita = self.modo.multi and jogador.indice == 1
            interface.desenhar_arma(
                self.tela, self.fontes, nave.arma, nave.arma == ARMA_EXPLOSIVA,
                nave.municao_explosiva, nave.municao_max, nave.fracao_recarga,
                "dir" if direita else "esq", jogador.cor,
                "X" if jogador.teclas is None else ("/" if direita else "Q"),
            )
        if self.chefe:
            interface.desenhar_barra_chefe(
                self.tela, self.fontes, self.chefes_derrotados + 1, self.chefe.NOME,
                self.chefe.fracao_barra, self.chefe.COR,
            )

    def placares(self) -> list[interface.Placar]:
        placares = []
        for jogador in self.jogadores:
            if self.modo.rounds:
                rotulo, valor = "VITORIAS", str(jogador.rounds_ganhos)
            else:
                rotulo, valor = "PONTOS", f"{jogador.pontuacao:06d}"
            dica = "O PARCEIRO REVIVE COM UM ESCUDO" if self.modo.reviver else ""
            placares.append(interface.Placar(
                f"J{jogador.indice + 1}", jogador.cor, rotulo, valor, jogador.vidas, jogador.vivo, dica,
            ))
        return placares

    def linhas_centro_hud(self) -> list[tuple[str, tuple[int, int, int]]]:
        modo = self.modo
        if modo.reviver:
            return [
                (f"EQUIPE  {self.pontos_totais():06d}", COR_SECUNDARIA),
                (f"DIFICULDADE  {self.dificuldade.nome}", COR_APAGADA),
                (f"RECORDE  {self.recorde:06d}", COR_APAGADA),
            ]
        if modo.rounds:
            a, b = self.jogadores
            return [(f"ROUND {self.round}  ·  {a.rounds_ganhos} x {b.rounds_ganhos}", COR_ITEM)]
        if modo.duracao:
            restante = max(0, modo.duracao - self.tempo_partida) // FPS
            return [(f"TEMPO  {restante // 60:02d}:{restante % 60:02d}", COR_PERIGO if restante <= 10 else COR_ITEM)]
        decorrido = self.tempo_partida // FPS
        return [(f"TEMPO  {decorrido // 60:02d}:{decorrido % 60:02d}", COR_ITEM)]

    def desenhar_fim_de_jogo(self):
        if not self.modo.multi:
            jogador = self.jogadores[0]
            interface.desenhar_tela_gameover(
                self.tela,
                self.fontes,
                jogador.pontuacao,
                self.recorde,
                self.nivel,
                self.fundo.indice + 1,
                self.novo_recorde,
                self.frame,
                self.dificuldade.nome,
            )
            return

        modo = self.modo
        colunas = []
        for jogador in self.jogadores:
            if modo.rounds:
                linhas = [f"ROUNDS  {jogador.rounds_ganhos}"]
            else:
                linhas = [f"PONTOS  {jogador.pontuacao:06d}"]
            if modo.segundos_por_nivel and not modo.rounds:
                fim = jogador.tempo_eliminado if jogador.tempo_eliminado is not None else self.tempo_partida
                linhas.append(f"DUROU  {fim // FPS // 60:02d}:{fim // FPS % 60:02d}")
            colunas.append((self.nome_jogador(jogador), jogador.cor, linhas))

        if modo.reviver:
            titulo, cor = "EQUIPE ELIMINADA", COR_PERIGO
            rodape = [
                f"EQUIPE  {self.pontos_totais():06d}",
                "NOVO RECORDE" if self.novo_recorde else f"RECORDE  {self.recorde:06d}",
                f"NIVEL {self.nivel:02d}   ·   SETOR {self.fundo.indice + 1:02d}   ·   {self.dificuldade.nome}",
            ]
        else:
            if self.vencedor:
                titulo, cor = f"{self.nome_jogador(self.vencedor)} VENCEU", self.vencedor.cor
            else:
                titulo, cor = "EMPATE", COR_ITEM
            rodape = []
        interface.desenhar_tela_fim_multi(self.tela, self.fontes, modo.nome, titulo, cor, colunas, rodape, self.frame)

    # ------------------------------------------------------------------- loop
    def executar(self):
        while True:
            self.processar_eventos()
            self.atualizar()
            self.desenhar()
            self.relogio.tick(FPS)
