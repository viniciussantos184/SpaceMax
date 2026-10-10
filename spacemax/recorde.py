"""Recordes persistentes salvos em arquivo (um por modo que tem recorde)."""

import os

from .config import CAMINHO_RECORDE, PASTA_PROJETO


def caminho(modo="solo"):
    # o recorde do solo continua em recorde.txt (compativel com versoes antigas)
    if modo == "solo":
        return CAMINHO_RECORDE
    return os.path.join(PASTA_PROJETO, f"recorde_{modo}.txt")


def carregar_recorde(modo="solo"):
    try:
        with open(caminho(modo), "r") as arquivo:
            return int(arquivo.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def salvar_recorde(valor, modo="solo"):
    try:
        with open(caminho(modo), "w") as arquivo:
            arquivo.write(str(valor))
    except OSError:
        pass
