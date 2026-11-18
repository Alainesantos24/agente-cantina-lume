import os
from typing import Literal

from dotenv import load_dotenv
from google import genai
from google.genai import types
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

import re

from buscar import buscar_com_recorte
from cardapio import (atualizar_memoria_regras, extrair_codigo, itens_no_texto,
                      montar_contexto, norm, quer_entrega)
from ferramentas import consultar_pedido, encaminhar_humano, somar_total

load_dotenv()

CAMINHOS = ("cardapio", "pedido", "total", "encaminhar", "fora")


class Estado(TypedDict):
    pergunta: str
    historico: list[dict]
    memoria: dict
    caminho: str
    contexto: str
    resposta: str


_CLIENTE = None


def _cliente() -> genai.Client:
    global _CLIENTE
    if _CLIENTE is None:
        chave = os.getenv("GEMINI_API_KEY")
        if not chave:
            raise SystemExit("chave vazia: confira o .env e ative o .venv")
        _CLIENTE = genai.Client(api_key=chave)
    return _CLIENTE


def _modelo() -> str:
    return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")


def _gerar(conteudo: str, sistema: str) -> str:
    resposta = _cliente().models.generate_content(
        model=_modelo(),
        contents=conteudo,
        config=types.GenerateContentConfig(
            system_instruction=sistema,
            temperature=0,
        ),
    )
    return (resposta.text or "").strip()


def classificar(estado: Estado) -> dict:
    texto = estado["pergunta"].lower()
    memoria = estado.get("memoria") or {}

    if any(p in texto for p in ("reembolso", "dinheiro de volta", "cancelar", "reclamação", "reclamacao")):
        return {"caminho": "encaminhar"}
    if "pedido" in texto or "lm1" in texto.replace(" ", ""):
        return {"caminho": "pedido"}
    if any(p in texto for p in ("total", "quanto ficou", "fecha a conta", "qual a conta")):
        return {"caminho": "total"}
    if any(p in texto for p in ("quanto custa", "preço", "preco", "tem ", "entregam", "horário", "horario", "alérg", "alerg", "ingrediente")):
        return {"caminho": "cardapio"}
    if texto.startswith("quero ") or " sem " in f" {texto} " or "troca" in texto:
        return {"caminho": "cardapio"}

    sistema = (
        "Classifique a mensagem com UMA palavra: cardapio, pedido, total, encaminhar ou fora. "
        "total só se a pessoa pediu a soma ou a conta. "
        "Montar um pedido, tirar ingrediente ou perguntar se pode, é cardapio."
    )
    bruto = _gerar(f"Memória: {memoria}\nMensagem: {estado['pergunta']}", sistema).lower()
    caminho = "fora"
    for opcao in CAMINHOS:
        if opcao in bruto:
            caminho = opcao
            break
    return {"caminho": caminho}


def _precos_dos_trechos(trechos: list[str]) -> str:
    linhas = []
    for bloco in trechos:
        nome = ""
        preco = ""
        for linha in bloco.splitlines():
            if linha.lower().startswith("nome:"):
                nome = linha.split(":", 1)[1].strip()
            if linha.lower().startswith("preco_reais:"):
                preco = linha.split(":", 1)[1].strip()
        if nome and preco:
            linhas.append(f"{nome}: R$ {preco}")
    if not linhas:
        return ""
    return " Preços do cardápio: " + " | ".join(linhas) + "."


def usar_ferramenta(estado: Estado) -> dict:
    caminho = estado["caminho"]
    pergunta = estado["pergunta"]
    memoria = estado.get("memoria") or {}

    if caminho == "pedido":
        codigo = extrair_codigo(pergunta)
        if not codigo:
            return {"contexto": "", "resposta": "Me passa o código do pedido. Os de teste vão de LM1001 a LM1008."}
        dado = consultar_pedido(codigo)
        return {"contexto": str(dado), "resposta": dado["frase"]}

    if caminho == "total":
        nomes = [i["nome"] for i in itens_no_texto(pergunta)] or list(memoria.get("itens", []))
        if not nomes:
            return {"contexto": "",
                    "resposta": "Me diz os itens com o nome do cardápio, por exemplo Hambúrguer Lume e Batata Frita."}
        dado = somar_total(nomes, entrega=quer_entrega(pergunta))
        return {"contexto": str(dado), "resposta": dado["frase"]}

    # encaminhar
    dado = encaminhar_humano("reembolso/cancelamento/reclamação", pergunta)
    return {"contexto": str(dado), "resposta": dado["frase"]}


def responder(estado: Estado) -> dict:
    # Ferramenta já escreveu a frase. Não deixa o modelo "melhorar" o número.
    if estado["caminho"] in ("pedido", "total", "encaminhar") and estado.get("resposta"):
        return {}
    if estado.get("resposta"):
        return {}
    sistema = (
        "Você é o atendimento da Cantina Lume, restaurante fictício. "
        "Responda em português, curto, sem emoji. "
        "Use TODOS os trechos do CONTEXTO que falem de um item pedido pelo cliente. "
        "Para cada item pedido, diga o preco_reais que estiver no trecho, em reais. "
        "Se o cliente pediu para tirar um ingrediente, só confirme se esse ingrediente estiver em pode_tirar. "
        "Não fale de item que o cliente não pediu. "
        "Se um item pedido não aparecer em nenhum trecho, diga que não encontrou só esse item. "
        "Não invente preço, taxa, prazo ou ingrediente. "
        "Cite a fonte pelo título entre colchetes."
        "Se o CONTEXTO tiver linha REMOÇÃO ou TROCA, siga essa linha ao pé da letra."
    )
    texto = (
        f"Memória: {estado.get('memoria')}\n"
        f"Pergunta: {estado['pergunta']}\n"
        f"CONTEXTO:\n{estado.get('contexto')}"
    )
    return {"resposta": _gerar(texto, sistema)}

def atualizar_memoria(estado: Estado) -> dict:
    return {"memoria": atualizar_memoria_regras(estado["pergunta"], estado.get("memoria") or {})}


def _rota(estado: Estado) -> Literal["buscar_cardapio", "usar_ferramenta", "responder"]:
    if estado["caminho"] == "cardapio":
        return "buscar_cardapio"
    if estado["caminho"] in ("pedido", "total", "encaminhar"):
        return "usar_ferramenta"
    return "responder"


def montar_grafo():
    grafo = StateGraph(Estado)
    grafo.add_node("classificar", classificar)
    grafo.add_node("buscar_cardapio", buscar_cardapio)
    grafo.add_node("usar_ferramenta", usar_ferramenta)
    grafo.add_node("responder", responder)
    grafo.add_node("memoria", atualizar_memoria)
    grafo.add_edge(START, "classificar")
    grafo.add_conditional_edges("classificar", _rota)
    grafo.add_edge("buscar_cardapio", "responder")
    grafo.add_edge("usar_ferramenta", "responder")
    grafo.add_edge("responder", "memoria")
    grafo.add_edge("memoria", END)
    return grafo.compile()


def nova_sessao() -> dict:
    return {"historico": [], "memoria": {}}


def responder_turno(app, sessao: dict, pergunta: str) -> str:
    entrada = {
        "pergunta": pergunta,
        "historico": sessao.get("historico", []),
        "memoria": sessao.get("memoria", {}),
        "caminho": "",
        "contexto": "",
        "resposta": "",
    }
    saida = app.invoke(entrada)
    sessao["memoria"] = saida.get("memoria", {})
    sessao["historico"] = sessao.get("historico", []) + [
        {"pergunta": pergunta, "resposta": saida.get("resposta", "")}
    ]
    return saida.get("resposta", "")

def buscar_cardapio(estado: Estado) -> dict:
    pergunta = estado["pergunta"]
    memoria = estado.get("memoria") or {}

    contexto, nomeados = montar_contexto(pergunta, memoria)
    achado = buscar_com_recorte(pergunta, k=3)
    trechos = achado["trechos"] if achado["ok"] else []

    if nomeados:
        # item citado pelo nome já veio inteiro; da busca só interessa política
        quer_politica = re.search(r"alerg|contamina|entreg|\bkm\b|taxa|horario|pagamento|cancel", norm(pergunta))
        trechos = [t for t in trechos if t["tipo"] == "politica"] if quer_politica else []

    partes = [contexto] if contexto else []
    for t in trechos:
        partes.append(f"[{t['titulo']}] {t['trecho']}")
    precos = _precos_dos_trechos([t["trecho"] for t in trechos])
    if precos:
        partes.append(precos.strip())

    if not partes:
        return {"contexto": "", "resposta": "Não encontrei isso no cardápio nem nas políticas da Cantina Lume."}
    return {"contexto": "\n\n".join(partes)}