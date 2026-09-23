"""
Gera a documentacao UML do SpaceMax.

0. Valida a hierarquia de classes (ferramentas/validar_hierarquia.py);
   se estiver invalida, nenhum diagrama e gerado.
1. py2puml: le o pacote `spacemax/` e gera `docs/uml/gerado/classes_py2puml.puml`
   (diagrama de classes extraido automaticamente do codigo).
2. PlantUML: renderiza todos os `.puml` de `docs/uml/` (manuais + gerado)
   para PNG em `docs/uml/imagens/`.

O PlantUML roda localmente via Java (`plantuml.jar`). Se o jar nao existir em
`ferramentas/`, ele e baixado automaticamente na primeira execucao.

Requisitos: pip install -r requirements-dev.txt  (e Java 8+ no PATH)
Executar:   python ferramentas/gerar_uml.py
"""

import glob
import os
import shutil
import subprocess
import sys
import urllib.request

PASTA_PROJETO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PASTA_UML = os.path.join(PASTA_PROJETO, "docs", "uml")
PASTA_GERADO = os.path.join(PASTA_UML, "gerado")
PASTA_IMAGENS = os.path.join(PASTA_UML, "imagens")
CAMINHO_JAR = os.path.join(PASTA_PROJETO, "ferramentas", "plantuml.jar")
URL_JAR = "https://github.com/plantuml/plantuml/releases/latest/download/plantuml.jar"


def gerar_com_py2puml():
    # o import de pygame (feito pelos modulos do jogo) nao deve abrir janela nem som
    os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")
    sys.path.insert(0, PASTA_PROJETO)

    from py2puml.py2puml import py2puml

    os.makedirs(PASTA_GERADO, exist_ok=True)
    destino = os.path.join(PASTA_GERADO, "classes_py2puml.puml")
    conteudo = "".join(py2puml("spacemax", "spacemax"))
    # nomeia o diagrama para a imagem sair como classes_py2puml.png
    conteudo = conteudo.replace("@startuml spacemax", "@startuml classes_py2puml", 1)
    with open(destino, "w", encoding="utf-8") as arquivo:
        arquivo.write(conteudo)

    print(f"[py2puml] {os.path.relpath(destino, PASTA_PROJETO)}")


def garantir_plantuml_jar():
    if os.path.exists(CAMINHO_JAR):
        return
    print(f"[plantuml] baixando {URL_JAR}")
    urllib.request.urlretrieve(URL_JAR, CAMINHO_JAR)


def renderizar_com_plantuml():
    if shutil.which("java") is None:
        print("[plantuml] Java nao encontrado no PATH; imagens nao foram geradas.")
        return

    garantir_plantuml_jar()

    arquivos = sorted(
        glob.glob(os.path.join(PASTA_UML, "*.puml"))
        + glob.glob(os.path.join(PASTA_GERADO, "*.puml"))
    )
    os.makedirs(PASTA_IMAGENS, exist_ok=True)
    subprocess.run(
        ["java", "-jar", CAMINHO_JAR, "-tpng", "-charset", "UTF-8", "-o", PASTA_IMAGENS]
        + arquivos,
        check=True,
    )

    for arquivo in arquivos:
        print(f"[plantuml] {os.path.relpath(arquivo, PASTA_PROJETO)}")


def validar_hierarquia():
    script = os.path.join(PASTA_PROJETO, "ferramentas", "validar_hierarquia.py")
    resultado = subprocess.run([sys.executable, script])
    if resultado.returncode != 0:
        sys.exit("[validacao] hierarquia invalida; diagramas nao foram gerados.")


if __name__ == "__main__":
    validar_hierarquia()
    gerar_com_py2puml()
    renderizar_com_plantuml()
