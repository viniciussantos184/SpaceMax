"""Modos de jogo: solo, cooperativo e os modos competitivos para dois jogadores."""

from dataclasses import dataclass

from .config import FPS, VIDAS_INICIAIS

VIDAS_COMPETITIVO = 3


@dataclass(frozen=True)
class Modo:
    chave: str
    nome: str
    resumo: str
    regras: tuple[str, ...]
    jogadores: int
    vidas: int
    progressao: bool  # chefes e melhorias; o nivel sobe com os pontos
    pvp: bool = False  # tiros e explosoes ferem o outro jogador
    recorde: bool = False  # tem recorde salvo (pontos da partida / da equipe)
    segundos_por_nivel: int | None = None  # None = o nivel sobe com os pontos
    duracao: int | None = None  # limite de tempo da partida, em frames
    rounds: bool = False
    reviver: bool = False  # um escudo coletado revive o parceiro eliminado
    pontua: bool = True  # False: os pontos nao contam (duelo)

    @property
    def multi(self) -> bool:
        return self.jogadores > 1


MODOS = [
    Modo(
        "solo", "SOLO", "um jogador contra os asteroides e os chefes",
        ("Voce contra os asteroides e os 20 chefes.", "Recorde salvo."),
        jogadores=1, vidas=VIDAS_INICIAIS, progressao=True, recorde=True,
    ),
    Modo(
        "coop", "COOPERATIVO", "os dois juntos contra os asteroides e os chefes",
        (
            "Os dois contra os asteroides e os chefes. Cada um tem 5 vidas",
            "e as proprias melhorias. Quem zera as vidas fica fora: um escudo",
            "coletado pelo parceiro revive o eliminado. Os pontos somam.",
        ),
        jogadores=2, vidas=VIDAS_INICIAIS, progressao=True, recorde=True, reviver=True,
    ),
    Modo(
        "duelo", "DUELO", "um atira no outro; melhor de 3 rounds",
        (
            "Tiros e explosoes ferem o outro jogador. 3 vidas por round,",
            "com asteroides atrapalhando. Vence o round quem sobrar;",
            "vence a partida quem ganhar 2 rounds. Escudo protege dos tiros.",
        ),
        jogadores=2, vidas=VIDAS_COMPETITIVO, progressao=False, pvp=True,
        segundos_por_nivel=20, rounds=True, pontua=False,
    ),
    Modo(
        "corrida", "CORRIDA DE PONTOS", "quem fizer mais pontos em 3 minutos",
        (
            "Os dois quebram asteroides: os pontos vao para quem acertou",
            "o tiro. Vence quem tiver mais pontos em 3 minutos. Quem perde",
            "as 3 vidas fica fora; se o outro passar na frente, a partida acaba.",
        ),
        jogadores=2, vidas=VIDAS_COMPETITIVO, progressao=False,
        segundos_por_nivel=30, duracao=180 * FPS,
    ),
    Modo(
        "sobrevivencia", "SOBREVIVENCIA", "asteroides cada vez mais rapidos; vence quem durar",
        (
            "Os dois contra asteroides que aceleram a cada 12 segundos.",
            "Sem tiro amigo. Cada um tem 3 vidas: vence quem durar mais,",
            "ou seja, quem ainda estiver vivo quando o outro for eliminado.",
        ),
        jogadores=2, vidas=VIDAS_COMPETITIVO, progressao=False, segundos_por_nivel=12,
    ),
]
