import sys
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

PASTA = Path(__file__).parent
BANCO = PASTA / ".chroma"
MODELO = "intfloat/multilingual-e5-small"
COLECAO = "cantina_lume"


def buscar(pergunta: str, k: int = 3) -> list[dict]:
    embeddings = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=MODELO
    )
    cliente = chromadb.PersistentClient(path=str(BANCO))
    colecao = cliente.get_collection(
        name=COLECAO,
        embedding_function=embeddings,
    )
    # e5 pede "query: " na pergunta e "passage: " no documento. A função do Chroma coloca isso.
    resultado = colecao.query(query_texts=[pergunta], n_results=k)
    saida = []
    for i in range(len(resultado["ids"][0])):
        saida.append(
            {
                "id": resultado["ids"][0][i],
                "distancia": round(resultado["distances"][0][i], 4),
                "titulo": resultado["metadatas"][0][i].get("titulo"),
                "tipo": resultado["metadatas"][0][i].get("tipo"),
                "trecho": resultado["documents"][0][i][:400],
            }
        )
    return saida


if __name__ == "__main__":
    pergunta = " ".join(sys.argv[1:]).strip()
    if not pergunta:
        raise SystemExit('uso: python buscar.py "quanto custa o hamburguer lume"')
    for item in buscar(pergunta):
        print("-" * 40)
        print(item["id"], "| distancia", item["distancia"], "|", item["tipo"])
        print(item["trecho"])

        LIMIAR = 0.45


LIMIAR = 0.45


def buscar_com_recorte(pergunta: str, k: int = 3) -> dict:
    achados = buscar(pergunta, k=k)
    if not achados or achados[0]["distancia"] > LIMIAR:
        return {"ok": False, "trechos": [], "motivo": "nada parecido o bastante"}
    return {"ok": True, "trechos": achados, "motivo": ""}