"""
SpaceMax - jogo 2D de acao e pontuacao infinita feito com pygame.

Ponto de entrada do jogo. Toda a logica fica no pacote `spacemax/`.

Controles:
    SETA ESQUERDA / A  -> move a nave para a esquerda
    SETA DIREITA  / D  -> move a nave para a direita
    ESPACO              -> atira
    ESC                 -> sai do jogo
    Na tela inicial / game over -> ESPACO ou clique para (re)comecar

Requisitos: pip install -r requirements.txt (pygame ou pygame-ce)
Executar:   python main.py
"""

from spacemax.jogo import Jogo


if __name__ == "__main__":
    Jogo().executar()
