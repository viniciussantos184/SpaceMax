"""Mostra no terminal o que o jogo le do controle (botoes e eixos).

Uso: python ferramentas/testar_controle.py   (Ctrl+C para sair)

Se algum botao sair com o nome errado, anote o numero "bruto" (b0, b1...) e
ajuste MAPEAMENTOS_EXTRAS em spacemax/controle.py.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from spacemax.controle import Controles  # noqa: E402

NOMES_BOTOES = {v: k[18:] for k, v in vars(pygame).items() if k.startswith("CONTROLLER_BUTTON_")}

pygame.init()
pygame.display.set_mode((320, 120))
pygame.display.set_caption("Teste de controle")
controles = Controles()
relogio = pygame.time.Clock()
print("Aperte os botoes do controle (feche a janela para sair)...")

while True:
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            sys.exit()
        controles.processar_evento(evento)
        if evento.type == pygame.CONTROLLERDEVICEADDED:
            print("controle conectado:", [c.name for c in controles.conectados.values()])
        elif evento.type == pygame.CONTROLLERBUTTONDOWN:
            print("botao do jogo:", NOMES_BOTOES.get(evento.button, evento.button))
        elif evento.type == pygame.JOYBUTTONDOWN:
            print(f"  (bruto: b{evento.button})")
        elif evento.type == pygame.JOYHATMOTION and evento.value != (0, 0):
            print(f"  (bruto: direcional {evento.value})")
    giro, acel, freio = controles.giro(), controles.acelerando(), controles.freando()
    if giro or acel or freio:
        print(f"giro={giro:+.2f} acelera={acel} freia={freio}", end="\r")
    relogio.tick(30)
