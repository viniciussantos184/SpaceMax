"""Recorde persistente salvo em arquivo."""

from .config import CAMINHO_RECORDE


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
