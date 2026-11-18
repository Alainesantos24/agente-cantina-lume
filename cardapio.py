import re
import unicodedata
from pathlib import Path

PASTA = Path(__file__).parent
CARDAPIO = PASTA / "dados" / "cardapio"


def norm(texto: str) -> str:
    """minúsculo e sem acento: 'Nome', 'nome' e 'Água'/'agua' viram a mesma coisa."""
    t = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn").strip()


def carregar_cardapio() -> dict:
    """chave = nome sem acento. Arquivo sem nome ou preço dá erro ALTO."""
    itens = {}
    for arquivo in sorted(CARDAPIO.glob("*.md")):
        texto = arquivo.read_text(encoding="utf-8").strip()
        campos = {}
        for linha in texto.splitlines():
            if ":" in linha:
                chave, valor = linha.split(":", 1)
                campos[norm(chave)] = valor.strip()
        if "nome" not in campos or "preco_reais" not in campos:
            raise ValueError(f"{arquivo.name}: falta 'nome' ou 'preco_reais' (olhe a primeira linha)")
        itens[norm(campos["nome"])] = {
            "arquivo": arquivo.stem,
            "nome": campos["nome"],
            "preco_reais": float(campos["preco_reais"]),
            "campos": campos,
        }
    return itens


def itens_no_texto(texto: str) -> list[dict]:
    """itens citados pelo nome completo, na ordem em que aparecem na frase."""
    t = norm(texto)
    achados = []
    for chave, item in carregar_cardapio().items():
        m = re.search(r"(?<!\w)" + re.escape(chave) + r"s?(?!\w)", t)
        if m:
            achados.append((m.start(), item))
    return [item for _, item in sorted(achados, key=lambda x: x[0])]


def quer_entrega(pergunta: str) -> bool:
    return not re.search(r"retirad|retirar|buscar|vou pegar|balcao", norm(pergunta))


def extrair_codigo(pergunta: str) -> str:
    m = re.search(r"lm\s*-?\s*(\d{4})", norm(pergunta))
    return f"LM{m.group(1)}" if m else ""


def _extrair_sem(t: str) -> list[str]:
    return [m.strip() for m in re.findall(
        r"\bsem\s+([^,.;?!]+?)(?=\s+e\s+|\s+com\s+|,|\.|;|\?|!|$)", t)]


def checar_remocoes(pergunta: str, itens: list[dict]) -> list[str]:
    linhas = []
    for s in _extrair_sem(norm(pergunta)):
        quem = []
        for item in itens:
            pode = item["campos"].get("pode_tirar", "")
            achou = [e.strip() for e in pode.split(",") if s in norm(e)]
            if achou:
                quem.append(f"{achou[0]} pode sair do {item['nome']}")
        if quem:
            linhas.append(f"REMOÇÃO 'sem {s}': " + "; ".join(quem) + ".")
        else:
            linhas.append(f"REMOÇÃO 'sem {s}': NÃO consta em pode_tirar de nenhum item pedido. Não confirmar.")
    return linhas


def extrair_troca(pergunta: str, itens_memoria: list[str]):
    """'troca a batata por salada extra' -> {'sai': 'Batata Frita', 'entra': item}"""
    t = norm(pergunta)
    if not re.search(r"\b(troca|trocar|troque|substitui|substituir)\b", t) or " por " not in t:
        return None
    esquerda, direita = t.split(" por ", 1)
    entra = itens_no_texto(direita)
    if not entra:
        return None
    sai = None
    for nome in itens_memoria:
        palavras = [w for w in norm(nome).split() if len(w) > 3]
        if any(re.search(r"(?<!\w)" + w, esquerda) for w in palavras):
            sai = nome
            break
    return {"sai": sai, "entra": entra[0]}


def aplicar_troca(itens: list[str], troca) -> list[str]:
    novos = list(itens)
    entra = troca["entra"]["nome"]
    if troca["sai"] in novos:
        pos = novos.index(troca["sai"])
        novos.pop(pos)
        if entra not in novos:
            novos.insert(pos, entra)
    elif entra not in novos:
        novos.append(entra)
    return novos


_PEDIR = r"\b(quero|queria|vou querer|adiciona|adicione|coloca|poe|bota|manda)\b"


def atualizar_memoria_regras(pergunta: str, memoria: dict) -> dict:
    mem = dict(memoria or {})
    t = norm(pergunta)

    sem = _extrair_sem(t)
    if sem:
        atuais = [x.strip() for x in mem.get("restricao", "").split(",") if x.strip()]
        for s in sem:
            if f"sem {s}" not in atuais:
                atuais.append(f"sem {s}")
        mem["restricao"] = ", ".join(atuais)

    itens = list(mem.get("itens", []))
    troca = extrair_troca(pergunta, itens)
    if troca:
        itens = aplicar_troca(itens, troca)
    elif re.search(_PEDIR, t):
        for item in itens_no_texto(pergunta):
            if item["nome"] not in itens:
                itens.append(item["nome"])
    if itens:
        mem["itens"] = itens
    return mem


def ficha(item: dict) -> str:
    c = item["campos"]
    return (
        f"[{item['arquivo']}] {item['nome']}: R$ {item['preco_reais']:.2f}\n"
        f"  alergenos: {c.get('alergenos', '')}\n"
        f"  pode_tirar: {c.get('pode_tirar', '')}\n"
        f"  nao_pode_tirar: {c.get('nao_pode_tirar', '')}\n"
        f"  adicional: {c.get('adicional', 'nenhum')}"
    )


def montar_contexto(pergunta: str, memoria: dict):
    """Item citado pelo nome entra inteiro no contexto, sem depender do vetor."""
    memoria = memoria or {}
    itens_mem = list(memoria.get("itens", []))
    cardapio = carregar_cardapio()
    nomeados = itens_no_texto(pergunta)
    troca = extrair_troca(pergunta, itens_mem)

    relevantes = list(nomeados)
    linhas = []
    if troca:
        depois = aplicar_troca(itens_mem, troca)
        linhas.append(f"TROCA: sai {troca['sai'] or '(não achei na memória)'}, "
                      f"entra {troca['entra']['nome']} (R$ {troca['entra']['preco_reais']:.2f}).")
        linhas.append("Pedido depois da troca: " + ", ".join(depois) + ".")
        for nome in depois:
            item = cardapio.get(norm(nome))
            if item and item not in relevantes:
                relevantes.append(item)
        if memoria.get("restricao"):
            linhas.append(f"Restrição guardada: {memoria['restricao']}.")
    linhas += checar_remocoes(pergunta, relevantes)
    partes = [ficha(i) for i in relevantes]
    return "\n".join(partes + linhas), relevantes