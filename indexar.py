import os
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PASTA = Path(__file__).parent
DADOS = PASTA / "dados"
BANCO = PASTA / ".chroma"
MODELO = "intfloat/multilingual-e5-small"
COLECAO = "cantina_lume"


def ler_texto(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8").strip()


def documentos() -> list[dict]:
    itens = []

    for arquivo in sorted((DADOS / "cardapio").glob("*.md")):
        texto = ler_texto(arquivo)
        if not texto:
            continue
        itens.append(
            {
                "id": f"cardapio:{arquivo.stem}",
                "texto": texto,
                "metadata": {
                    "tipo": "cardapio",
                    "arquivo": arquivo.name,
                    "titulo": arquivo.stem,
                },
            }
        )

    politicas = DADOS / "politicas.md"
    texto = ler_texto(politicas)
    # Um bloco por título. Política inteira num único vetor mistura taxa com reembolso.
    blocos = []
    atual_titulo = "politicas"
    atual_linhas: list[str] = []
    for linha in texto.splitlines():
        if linha.startswith("## "):
            if atual_linhas:
                blocos.append((atual_titulo, "\n".join(atual_linhas).strip()))
            atual_titulo = linha.removeprefix("## ").strip().lower().replace(" ", "-")
            atual_linhas = [linha]
        else:
            atual_linhas.append(linha)
    if atual_linhas:
        blocos.append((atual_titulo, "\n".join(atual_linhas).strip()))

    for titulo, bloco in blocos:
        if len(bloco) < 20:
            continue
        itens.append(
            {
                "id": f"politica:{titulo}",
                "texto": bloco,
                "metadata": {
                    "tipo": "politica",
                    "arquivo": "politicas.md",
                    "titulo": titulo,
                },
            }
        )

    return itens


def main() -> None:
    itens = documentos()
    if len(itens) < 17:
        raise SystemExit(
            f"só achei {len(itens)} documentos. Esperava 16 pratos + políticas. Confere a pasta dados."
        )

    embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=MODELO
    )
    cliente = chromadb.PersistentClient(path=str(BANCO))

    # Recria a coleção. Rodar de novo depois de editar um preço não deixa o preço velho no índice.
    try:
        cliente.delete_collection(COLECAO)
    except Exception:
        pass

    colecao = cliente.create_collection(
        name=COLECAO,
        embedding_function=embeddings,
        metadata={"hnsw:space": "cosine"},
    )

    colecao.add(
        ids=[item["id"] for item in itens],
        documents=[item["texto"] for item in itens],
        metadatas=[item["metadata"] for item in itens],
    )

    print(f"indexados {colecao.count()} documentos em {BANCO}")
    print("tipos:", sorted({item['metadata']['tipo'] for item in itens}))


if __name__ == "__main__":
    main()