# SpaceMax

Jogo 2D de acao e pontuacao infinita feito em Python com pygame. Controle uma
nave espacial que se move para os lados, atire nos meteoros que caem do topo
da tela e tente bater o recorde de pontuacao antes que suas vidas acabem.

## Como jogar

- **Seta esquerda / A**: move a nave para a esquerda
- **Seta direita / D**: move a nave para a direita
- **ESPACO**: atira
- **ESC**: sai do jogo
- Na tela inicial ou de Game Over, pressione ESPACO/clique para (re)comecar

Cada meteoro destruido soma 1 ponto. Meteoros maiores exigem mais de um tiro
para serem destruidos. Se um meteoro colidir com a nave, uma vida e perdida
(voce comeca com 3); ao perder a ultima vida, o jogo termina. De vez em
quando aparece um item dourado que concede um escudo temporario (5 segundos
de imunidade a colisao).

## Sistema de niveis e dificuldade

A cada 8 pontos o jogador sobe de nivel (aviso "NIVEL X" aparece na tela). A
cada nivel, os meteoros ficam mais rapidos e aparecem com mais frequencia,
deixando o jogo progressivamente mais dificil.

## Elementos implementados

- Personagem principal (nave) que se move horizontalmente e atira
- Cenario com estrelas em paralaxe vertical
- Meteoros gerados continuamente, com tamanho, vida e trajetoria variaveis
- Sistema de pontuacao (pontuacao atual + recorde salvo em `recorde.txt`)
- Sistema de niveis com dificuldade progressiva (velocidade e frequencia dos meteoros)
- Sistema de vidas (3 vidas, com breve invencibilidade apos ser atingido)
- Sistema de colisao (tiro-meteoro e nave-meteoro)
- Tela inicial e tela de Game Over
- Efeitos sonoros gerados por codigo (sem precisar de arquivos de audio)
- Efeito visual de explosao (particulas) ao destruir meteoros
- Item especial (escudo temporario)

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
    ├── config.py           # constantes: tela, cores, velocidades, dificuldade
    ├── jogo.py             # classe Jogo: loop principal, regras e colisoes
    ├── interface.py        # textos, HUD, tela inicial e de Game Over
    ├── sons.py             # efeitos sonoros gerados por codigo
    ├── recorde.py          # leitura/gravacao do recorde
    └── entidades/
        ├── nave.py         # nave do jogador
        ├── tiro.py         # tiros
        ├── meteoro.py      # meteoros
        ├── item.py         # item de escudo
        ├── particula.py    # particulas de explosao
        └── estrela.py      # estrelas do cenario
```

## Diagramas UML (py2puml + PlantUML)

Os diagramas ficam em `docs/uml/`:

| Arquivo | Conteudo |
| --- | --- |
| `classes.puml` | diagrama de classes completo (atributos, metodos e relacoes) |
| `estados.puml` | maquina de estados do jogo (Inicio, Jogando, Game Over) |
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
    +-- EntidadeColidivel (abstrata)   rect(), colide_com()
        +-- Item
        +-- Meteoro
        +-- Nave
        +-- Tiro
    +-- Estrela
    +-- Particula
```

![Diagrama de classes](docs/uml/imagens/classes.png)

## Instalacao

Requer Python 3.8+.

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
