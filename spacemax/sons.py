"""Sons gerados proceduralmente (sem depender de arquivos externos)."""

import array
import math
import random

import pygame


def gerar_som(frequencia, duracao=0.12, volume=0.25, tipo="senoide"):
    taxa_amostragem = 44100
    n_amostras = int(taxa_amostragem * duracao)
    buffer = array.array("h", [0] * n_amostras)
    amplitude = int(32767 * volume)

    for i in range(n_amostras):
        t = i / taxa_amostragem
        envelope = 1.0 - (i / n_amostras)  # fade-out simples

        if tipo == "senoide":
            valor = math.sin(2 * math.pi * frequencia * t)
        elif tipo == "quadrada":
            valor = 1.0 if math.sin(2 * math.pi * frequencia * t) >= 0 else -1.0
        elif tipo == "ruido":
            valor = random.uniform(-1.0, 1.0)
        else:
            valor = 0.0

        buffer[i] = int(valor * amplitude * envelope)

    return pygame.mixer.Sound(buffer=buffer)


def criar_sons():
    try:
        pygame.mixer.init(frequency=44100, size=-16, channels=1)
        return {
            "tiro": gerar_som(700, 0.06, 0.12, "quadrada"),
            "explosao": gerar_som(140, 0.18, 0.25, "ruido"),
            "colisao": gerar_som(110, 0.35, 0.3, "quadrada"),
            "item": gerar_som(1200, 0.12, 0.2, "senoide"),
            "nivel": gerar_som(660, 0.20, 0.22, "senoide"),
            "dash": gerar_som(90, 0.16, 0.22, "ruido"),
        }
    except pygame.error:
        return None


def tocar(sons, nome):
    if sons and nome in sons:
        sons[nome].play()
