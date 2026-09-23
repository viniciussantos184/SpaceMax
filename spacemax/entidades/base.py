"""Classes base das entidades do jogo."""

from abc import ABC, abstractmethod

import pygame


class Entidade(ABC):
    """Qualquer objeto com posicao que e atualizado e desenhado a cada frame."""

    def __init__(self, x: float, y: float):
        self.x: float = x
        self.y: float = y

    @abstractmethod
    def atualizar(self):
        ...

    @abstractmethod
    def desenhar(self, tela):
        ...


class EntidadeColidivel(Entidade):
    """Entidade que participa do sistema de colisao."""

    @abstractmethod
    def rect(self) -> pygame.Rect:
        ...

    def colide_com(self, outra: "EntidadeColidivel") -> bool:
        return self.rect().colliderect(outra.rect())
