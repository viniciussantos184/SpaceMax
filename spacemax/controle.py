"""Suporte a controles (Xbox, PlayStation, Switch... por USB ou bluetooth).

Usa a API GameController do SDL, que entrega o mesmo layout de botoes para
qualquer controle reconhecido (A/B/X/Y na posicao do controle de Xbox).

Mapeamento:
    analogico esquerdo / direcional -> gira, acelera (cima) e freia (baixo)
    A / RB                          -> atira (segurar dispara continuo)
    RT                              -> acelera
    LT                              -> freia
    B                               -> impulso
    X / Y / LB                      -> troca de arma
    START                           -> pausa / continua
    START / A                       -> (re)comeca na tela inicial / game over
    Nos menus: direcional / analogico escolhem, A confirma, Y alterna tela cheia,
    SELECT (no pause) volta ao menu inicial
"""

import os

import pygame
from pygame._sdl2 import controller

# Controles que o SDL ainda nao conhece. O 8BitDo Ultimate 2 Wireless no
# bluetooth (modo DirectInput) aparece como "gamepad generico"; o layout e o
# mesmo dos outros 8BitDo Ultimate. Precisa estar no ambiente antes de
# controller.init(), que e quando o SDL le os mapeamentos.
MAPEAMENTOS_EXTRAS = [
    "03000000c82d00001260000000000000,8BitDo Ultimate 2 Wireless,"
    "a:b0,b:b1,x:b3,y:b4,back:b10,start:b11,guide:b12,"
    "leftshoulder:b6,rightshoulder:b7,lefttrigger:b8,righttrigger:b9,"
    "leftstick:b13,rightstick:b14,leftx:a0,lefty:a1,"
    "dpup:h0.1,dpright:h0.2,dpdown:h0.4,dpleft:h0.8,platform:Windows,",
]
_existentes = os.environ.get("SDL_GAMECONTROLLERCONFIG", "")
os.environ["SDL_GAMECONTROLLERCONFIG"] = "\n".join(filter(None, [_existentes, *MAPEAMENTOS_EXTRAS]))

ZONA_MORTA = 0.25  # ignora pequenas folgas do analogico
LIMIAR_DIRECAO = 0.5  # quanto o analogico precisa ir para cima/baixo para acelerar/frear
LIMIAR_GATILHO = 0.3

BOTOES_TIRO = (pygame.CONTROLLER_BUTTON_A, pygame.CONTROLLER_BUTTON_RIGHTSHOULDER)
BOTOES_DASH = (pygame.CONTROLLER_BUTTON_B,)
BOTOES_ARMA = (
    pygame.CONTROLLER_BUTTON_X,
    pygame.CONTROLLER_BUTTON_Y,
    pygame.CONTROLLER_BUTTON_LEFTSHOULDER,
)
BOTOES_INICIAR = (pygame.CONTROLLER_BUTTON_START, pygame.CONTROLLER_BUTTON_A)
BOTAO_PAUSA = pygame.CONTROLLER_BUTTON_START
BOTOES_CONTINUAR = (pygame.CONTROLLER_BUTTON_START, pygame.CONTROLLER_BUTTON_B)
BOTAO_MENU = pygame.CONTROLLER_BUTTON_BACK
BOTAO_TELA_CHEIA = pygame.CONTROLLER_BUTTON_Y
BOTAO_CONFIRMAR = pygame.CONTROLLER_BUTTON_A
BOTOES_MENU_ESQUERDA = (pygame.CONTROLLER_BUTTON_DPAD_LEFT,)
BOTOES_MENU_DIREITA = (pygame.CONTROLLER_BUTTON_DPAD_RIGHT,)


class Controles:
    """Mantem a lista de controles conectados (entram e saem a qualquer momento)."""

    def __init__(self):
        controller.init()
        self.conectados: dict[int, controller.Controller] = {}
        self.analogico_centrado: bool = True  # para o analogico mover 1 opcao por vez nos menus
        # os controles ja pareados chegam como eventos CONTROLLERDEVICEADDED

    def processar_evento(self, evento):
        if evento.type == pygame.CONTROLLERDEVICEADDED:
            self.conectar(evento.device_index)
        elif evento.type == pygame.CONTROLLERDEVICEREMOVED:
            self.conectados.pop(evento.instance_id, None)

    def conectar(self, indice):
        if not controller.is_controller(indice):
            return
        try:
            ctrl = controller.Controller(indice)
        except pygame.error:
            return
        self.conectados[ctrl.as_joystick().get_instance_id()] = ctrl

    def nome(self) -> str | None:
        """Nome do primeiro controle conectado (para mostrar na tela inicial)."""
        for ctrl in self.conectados.values():
            return ctrl.name
        return None

    def navegacao_analogico(self, evento) -> int:
        """-1/1 quando o analogico e empurrado para esquerda/direita (uma vez por empurrao)."""
        if evento.type != pygame.CONTROLLERAXISMOTION or evento.axis != pygame.CONTROLLER_AXIS_LEFTX:
            return 0
        valor = evento.value / 32767
        if abs(valor) < ZONA_MORTA:
            self.analogico_centrado = True
        elif abs(valor) > LIMIAR_DIRECAO and self.analogico_centrado:
            self.analogico_centrado = False
            return 1 if valor > 0 else -1
        return 0

    # ------------------------------------------------------------- leitura
    def _eixo(self, ctrl, eixo):
        valor = ctrl.get_axis(eixo) / 32767
        return 0.0 if abs(valor) < ZONA_MORTA else max(-1.0, min(1.0, valor))

    def _botao(self, botao):
        return any(ctrl.get_button(botao) for ctrl in self.conectados.values())

    def giro(self):
        """-1 (esquerda) a 1 (direita); analogico da giro proporcional."""
        valor = 0.0
        for ctrl in self.conectados.values():
            valor += self._eixo(ctrl, pygame.CONTROLLER_AXIS_LEFTX)
            valor += ctrl.get_button(pygame.CONTROLLER_BUTTON_DPAD_RIGHT)
            valor -= ctrl.get_button(pygame.CONTROLLER_BUTTON_DPAD_LEFT)
        return max(-1.0, min(1.0, valor))

    def acelerando(self):
        return any(
            ctrl.get_button(pygame.CONTROLLER_BUTTON_DPAD_UP)
            or self._eixo(ctrl, pygame.CONTROLLER_AXIS_LEFTY) < -LIMIAR_DIRECAO
            or self._eixo(ctrl, pygame.CONTROLLER_AXIS_TRIGGERRIGHT) > LIMIAR_GATILHO
            for ctrl in self.conectados.values()
        )

    def freando(self):
        return any(
            ctrl.get_button(pygame.CONTROLLER_BUTTON_DPAD_DOWN)
            or self._eixo(ctrl, pygame.CONTROLLER_AXIS_LEFTY) > LIMIAR_DIRECAO
            or self._eixo(ctrl, pygame.CONTROLLER_AXIS_TRIGGERLEFT) > LIMIAR_GATILHO
            for ctrl in self.conectados.values()
        )

    def atirando(self):
        return any(self._botao(botao) for botao in BOTOES_TIRO)
