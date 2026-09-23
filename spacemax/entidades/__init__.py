"""Entidades do jogo: nave, tiros, meteoros, itens, estrelas e particulas."""

from .base import Entidade, EntidadeColidivel
from .estrela import Estrela
from .item import Item
from .meteoro import Meteoro
from .nave import Nave
from .onda import Onda
from .particula import Particula
from .tiro import Tiro

__all__ = [
    "Entidade",
    "EntidadeColidivel",
    "Estrela",
    "Item",
    "Meteoro",
    "Nave",
    "Onda",
    "Particula",
    "Tiro",
]
