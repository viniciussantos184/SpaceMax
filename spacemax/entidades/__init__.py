"""Entidades do jogo: nave, tiros, meteoros, chefes, itens, estrelas e particulas."""

from .base import Entidade, EntidadeColidivel
from .chefes import Arpao, Espectro, Farol, Gemeos, Nucleo, Orbita, Prisma, Sentinela, Vespa
from .chefes_elite import (
    CHEFES,
    Bastiao,
    Ciclone,
    Colmeia,
    Espelho,
    Hidra,
    Imperador,
    Miragem,
    Pulsar,
    Serpente,
    Singularidade,
    Tempestade,
)
from .estrela import Estrela
from .item import Item
from .meteoro import Meteoro
from .nave import Nave
from .onda import Onda
from .particula import Particula
from .projetil import ProjetilChefe
from .tiro import Tiro, TiroExplosivo

__all__ = [
    "Arpao",
    "Bastiao",
    "Ciclone",
    "Colmeia",
    "Entidade",
    "EntidadeColidivel",
    "Espectro",
    "Espelho",
    "Estrela",
    "Farol",
    "Gemeos",
    "Hidra",
    "Imperador",
    "Item",
    "Meteoro",
    "Miragem",
    "Nave",
    "Nucleo",
    "Onda",
    "Orbita",
    "Particula",
    "Prisma",
    "ProjetilChefe",
    "Pulsar",
    "Sentinela",
    "Serpente",
    "Singularidade",
    "Tempestade",
    "Tiro",
    "TiroExplosivo",
    "Vespa",
]
