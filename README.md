# SpaceMax

Jogo 2D de acao e pontuacao infinita feito em Python com pygame, no estilo do
Asteroids classico e com visual tech minimalista (graficos vetoriais em linhas
finas, fonte monoespacada, grade tecnica ao fundo). Pilote uma nave que gira
360 graus e voa com inercia, quebre os asteroides em pedacos cada vez menores e
viaje por galaxias diferentes a cada 3 niveis.

## Como jogar

- **Seta esquerda/direita ou A/D**: gira a nave (o giro acelera suavemente e para rapido ao soltar)
- **Seta para cima ou W**: acelera (o motor ganha potencia aos poucos e a nave mantem o embalo)
- **Seta para baixo ou S**: freia
- **CONTROL**: impulso, uma arrancada rapida para frente (ilimitado, sem recarga)
- **ESPACO**: atira na direcao em que a nave aponta
- **ESC**: sai do jogo
- Na tela inicial ou de Game Over, pressione ESPACO/clique para (re)comecar

A nave, os tiros e os asteroides atravessam as bordas da tela e reaparecem do
lado oposto. Os asteroides chegam por todos os lados.

## Asteroides que se quebram

| Tamanho | Ao ser atingido | Pontos |
| --- | --- | --- |
| Grande | quebra em 2 medios | 20 |
| Medio | quebra em 2 pequenos (mais rapidos) | 50 |
| Pequeno | e destruido | 100 |

Se um asteroide colidir com a nave, uma vida e perdida (voce comeca com 3) e a
nave reaparece no centro, piscando e invencivel por 2 segundos. De vez em
a cada 6-10 segundos surge um item ambar em forma de losango (ate 2 na tela):
ele da um escudo de 6 segundos que destroi os asteroides em que a nave
encostar. Pegar o escudo solta uma onda de choque ambar, e cada asteroide
esmagado pelo escudo gera onda de impacto, faiscas e um tremor na tela.

## Niveis e galaxias

A cada 1000 pontos o jogador sobe de nivel: os asteroides ficam mais rapidos e
aparecem com mais frequencia. **A cada 3 niveis a nave chega a uma nova
galaxia** (novo "setor"), com plano de fundo, nebulosas e cores proprios:

| Setor | Niveis | Galaxia |
| --- | --- | --- |
| 01 | 1-3 | Via Lactea (azul) |
| 02 | 4-6 | Andromeda (violeta) |
| 03 | 7-9 | Nuvem de Magalhaes (ambar) |
| 04 | 10-12 | Triangulo (verde) |
| 05 | 13-15 | Sombrero (vermelho) |
| 06 | 16-18 | Redemoinho (gelo) |

Depois do setor 06 o ciclo recomeca. Os fundos sao gerados por codigo
(`spacemax/galaxias.py`), sem arquivos de imagem.

## Chefes

**A cada 5 niveis (5, 10, 15...) aparece um chefe.** Durante a luta nao surgem
asteroides novos e o nivel fica congelado ate o chefe ser derrotado, o que vale
1500 pontos. Uma barra de vida aparece na base da tela. Abaixo de metade da
vida o chefe fica "furioso" e ataca mais rapido. Encostar nele sem escudo custa
uma vida; com escudo, a nave e empurrada para longe e causa dano.

| # | Nivel | Chefe | Forma | Ataque |
| --- | --- | --- | --- | --- |
| 01 | 5 | Sentinela (vermelho) | hexagono com anel segmentado | rajadas em circulo |
| 02 | 10 | Arpao (violeta) | ponta de flecha que vira para a nave | leque de tiros mirados |
| 03 | 15 | Orbita (verde) | losango com 3 satelites | espiral; os satelites bloqueiam tiros e tambem atiram |
| 04 | 20 | Prisma (rosa) | quadrado duplo | mira (linha tracejada), investe contra a nave e solta um anel |
| 05 | 25 | Nucleo (laranja) | aneis concentricos | espiral dupla e minas que explodem em estilhacos |

Depois do 5o chefe a lista recomeca com os chefes mais fortes (mais vida,
tiros mais rapidos e frequentes).

## Elementos implementados

- Nave vetorial que gira 360 graus com giro progressivo, acelera com inercia, freia, usa impulso (CONTROL) e atira na direcao em que aponta
- Rastro de exaustao do motor, jatos laterais ao girar e rastro fantasma durante o impulso
- Asteroides que se quebram em pedacos menores (grande -> medio -> pequeno)
- Tela sem bordas: tudo atravessa as laterais e reaparece do outro lado
- Planos de fundo procedurais com uma galaxia diferente a cada 3 niveis, com transicao suave
- Sistema de pontuacao por tamanho de asteroide + recorde salvo em `recorde.txt`
- Niveis com dificuldade progressiva (velocidade e frequencia dos asteroides)
- Sistema de vidas com reaparecimento e invencibilidade temporaria
- Colisao circular (tiro-asteroide, nave-asteroide, nave-item)
- HUD minimalista (pontos, vidas, nivel, setor/galaxia, recorde) e avisos animados
- Tela inicial (com asteroides flutuando ao fundo) e tela de Game Over
- Efeitos sonoros gerados por codigo (sem precisar de arquivos de audio)
- Faiscas de explosao, ondas de choque e tremor de tela (ao pegar escudo, bater com escudo e ser atingido)
- Cinco chefes diferentes, um a cada 5 niveis, com barra de vida e aviso de entrada

## Estrutura do projeto

```
SpaceMax/
├── main.py                 # ponto de entrada (apenas inicia o jogo)
├── requirements.txt
├── requirements-dev.txt    # dependencias de desenvolvimento (py2puml)
├── docs/uml/               # diagramas PlantUML (.puml) e imagens geradas
├── ferramentas/
│   └── gerar_uml.py        # gera os diagramas com py2puml + PlantUML
└── spacemax/
    ├── config.py           # constantes: tela, paleta, fisica, dificuldade
    ├── jogo.py             # classe Jogo: loop principal, regras e colisoes
    ├── galaxias.py         # planos de fundo: uma galaxia a cada 3 niveis
    ├── grafico.py          # primitivas de desenho vetorial (linhas com brilho)
    ├── interface.py        # HUD, avisos, tela inicial e de Game Over
    ├── sons.py             # efeitos sonoros gerados por codigo
    ├── recorde.py          # leitura/gravacao do recorde
    └── entidades/
        ├── base.py         # classes base Entidade e EntidadeColidivel
        ├── nave.py         # nave do jogador
        ├── tiro.py         # tiros
        ├── meteoro.py      # asteroides (quebram em pedacos menores)
        ├── item.py         # item de escudo
        ├── chefes.py       # chefes (um a cada 5 niveis) e a ordem em que aparecem
        ├── projetil.py     # projeteis e minas dos chefes
        ├── particula.py    # particulas de explosao
        └── estrela.py      # estrelas do cenario
```

## Diagramas UML (py2puml + PlantUML)

Os diagramas ficam em `docs/uml/`:

| Arquivo | Conteudo |
| --- | --- |
| `classes.puml` | diagrama de classes completo (atributos, metodos e relacoes) |
| `estados.puml` | maquina de estados do jogo (Inicio, Jogando, Game Over) |
| `sequencia_partida.puml` | sequencia de uma partida completa (inicio, jogo, game over, reinicio) |
| `sequencia_frame.puml` | sequencia de chamadas em um frame do jogo |
| `pacotes.puml` | dependencias entre os modulos |
| `gerado/classes_py2puml.puml` | diagrama gerado automaticamente a partir do codigo pelo **py2puml** |

As imagens PNG ficam em `docs/uml/imagens/`. Para gerar tudo de novo depois
de mudar o codigo (precisa de Java instalado; o `plantuml.jar` e baixado
automaticamente na primeira vez):

```bash
pip install -r requirements-dev.txt
python ferramentas/gerar_uml.py
```

Antes de gerar os diagramas, o script valida a hierarquia de classes
(`ferramentas/validar_hierarquia.py`, que tambem pode ser executado sozinho).
Se alguma entidade nao herdar de `Entidade`, ou deixar um metodo abstrato sem
implementar, nenhum diagrama e gerado.

```
Entidade (abstrata)            x, y, atualizar(), desenhar()
    +-- EntidadeColidivel (abstrata)   raio, vx, vy, mover(), colide_com()
        +-- Item
        +-- Meteoro
        +-- Nave
        +-- Tiro
    +-- Estrela
    +-- Particula
```

![Diagrama de classes](docs/uml/imagens/classes.png)

## Instalacao

Requer Python 3.10+.

```bash
pip install -r requirements.txt
```

> Observacao: em Python 3.13/3.14, o pacote `pygame` classico ainda nao tem
> build pre-compilado no PyPI. Por isso o `requirements.txt` usa
> `pygame-ce` (Community Edition), que e 100% compativel — o `import pygame`
> continua igual. Se voce estiver usando Python 3.12 ou anterior, pode trocar
> por `pygame` normalmente.

## Executar

```bash
python main.py
```
