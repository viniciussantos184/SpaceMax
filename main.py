"""
SpaceMax - jogo 2D de acao e pontuacao infinita feito com pygame.

Ponto de entrada do jogo. Toda a logica fica no pacote `spacemax/`.

Controles:
    SETAS / WASD       -> movem a nave em qualquer direcao
    ESPACO              -> atira
    CONTROL             -> impulso
    ESC                 -> sai do jogo
    Na tela inicial / game over -> ESPACO ou clique para (re)comecar

Requisitos: pip install -r requirements.txt (pygame ou pygame-ce)
Executar:   python main.py
"""

from spacemax.jogo import Jogo


if __name__ == "__main__":
    Jogo().executar()
