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
            "impacto_escudo": gerar_som(260, 0.14, 0.22, "quadrada"),
            "alerta": gerar_som(180, 0.6, 0.25, "quadrada"),
            "tiro_chefe": gerar_som(320, 0.07, 0.08, "senoide"),
            "acerto_chefe": gerar_som(900, 0.03, 0.08, "quadrada"),
            "chefe_derrotado": gerar_som(70, 0.9, 0.35, "ruido"),
            "tiro_explosivo": gerar_som(240, 0.12, 0.2, "quadrada"),
            "explosao_grande": gerar_som(60, 0.45, 0.32, "ruido"),
            "troca_arma": gerar_som(1000, 0.05, 0.12, "senoide"),
            "laser": gerar_som(150, 0.5, 0.2, "quadrada"),
            "teleporte": gerar_som(520, 0.22, 0.15, "senoide"),
            "pausa": gerar_som(440, 0.08, 0.15, "senoide"),
            "melhoria": gerar_som(880, 0.25, 0.2, "senoide"),
            "selecao": gerar_som(600, 0.03, 0.1, "quadrada"),
            "trovao": gerar_som(55, 0.4, 0.3, "ruido"),
            "reflexo": gerar_som(1400, 0.05, 0.1, "senoide"),
        }
    except pygame.error:
        return None


def tocar(sons, nome):
    if sons and nome in sons:
        sons[nome].play()
