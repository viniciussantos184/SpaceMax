"""
SpaceMax - jogo 2D de acao e pontuacao infinita feito com pygame.

Ponto de entrada do jogo. Toda a logica fica no pacote `spacemax/`.

Controles:
    SETAS / WASD       -> movem a nave em qualquer direcao
    ESPACO              -> atira
    CONTROL             -> impulso
    Q / TAB             -> troca de arma
    P / ENTER / ESC     -> pausa (no pause, ESC volta ao menu inicial)
    F11 / ALT+ENTER     -> tela cheia
    ESC (no menu)       -> sai do jogo
    Tela inicial -> ESPACO ou clique abre a escolha de modo (solo, coop, duelo...)
    Game over    -> ESPACO joga de novo, M escolhe outro modo
    2 jogadores  -> tela de jogadores: cada um entra com controle (A) ou teclado
                    teclado J1: WASD, ESPACO, CTRL esq., Q | teclado J2: setas, SHIFT dir., CTRL dir., /
    Controle (USB/bluetooth)    -> veja spacemax/controle.py

Requisitos: pip install -r requirements.txt (pygame ou pygame-ce)
Executar:   python main.py
"""

from spacemax.jogo import Jogo


if __name__ == "__main__":
    Jogo().executar()
