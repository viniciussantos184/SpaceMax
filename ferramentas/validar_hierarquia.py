"""
Valida a hierarquia de classes das entidades do SpaceMax.

Verifica, por introspeccao, que:
  - toda classe exportada por `spacemax.entidades` herda de `Entidade`;
  - nenhuma classe concreta deixou metodo abstrato sem implementar;
  - toda `EntidadeColidivel` implementa `rect()` retornando um `pygame.Rect`;
  - as classes base nao podem ser instanciadas diretamente.

Tambem imprime a arvore de heranca encontrada.

Executar: python ferramentas/validar_hierarquia.py   (sai com codigo 1 se falhar)
"""

import inspect
import os
import sys

os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pygame  # noqa: E402

from spacemax import entidades  # noqa: E402
from spacemax.entidades import Entidade, EntidadeColidivel  # noqa: E402

# argumentos para instanciar as classes que exigem parametros no construtor
ARGUMENTOS_TESTE = {
    "Tiro": (100, 100),
    "Particula": (100, 100),
    "Meteoro": (2.0, 3.5),
}


def classes_do_pacote():
    return [
        obj
        for nome, obj in vars(entidades).items()
        if inspect.isclass(obj) and nome in entidades.__all__
    ]


def imprimir_arvore(classe, nivel=0):
    abstrata = " (abstrata)" if inspect.isabstract(classe) else ""
    print("    " * nivel + ("+-- " if nivel else "") + classe.__name__ + abstrata)
    for filha in sorted(classe.__subclasses__(), key=lambda c: c.__name__):
        imprimir_arvore(filha, nivel + 1)


def validar():
    erros = []

    for classe in classes_do_pacote():
        nome = classe.__name__

        if not issubclass(classe, Entidade):
            erros.append(f"{nome} nao herda de Entidade")
            continue

        if classe in (Entidade, EntidadeColidivel):
            try:
                classe(0, 0)
                erros.append(f"{nome} deveria ser abstrata, mas foi instanciada")
            except TypeError:
                pass
            continue

        if inspect.isabstract(classe):
            faltando = ", ".join(sorted(classe.__abstractmethods__))
            erros.append(f"{nome} nao implementa: {faltando}")
            continue

        instancia = classe(*ARGUMENTOS_TESTE.get(nome, ()))
        if not (hasattr(instancia, "x") and hasattr(instancia, "y")):
            erros.append(f"{nome} nao inicializa x/y (faltou super().__init__?)")

        if isinstance(instancia, EntidadeColidivel) and not isinstance(
            instancia.rect(), pygame.Rect
        ):
            erros.append(f"{nome}.rect() nao retorna pygame.Rect")

    return erros


if __name__ == "__main__":
    print("Hierarquia de classes:")
    imprimir_arvore(Entidade)
    print()

    erros = validar()
    if erros:
        print("FALHOU:")
        for erro in erros:
            print(f"  - {erro}")
        sys.exit(1)

    print(f"OK: {len(classes_do_pacote())} classes validadas.")
