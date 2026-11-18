import json
from pathlib import Path
from cardapio import carregar_cardapio, norm

PASTA = Path(__file__).parent
PEDIDOS = PASTA / "dados" / "pedidos.json"
ENCAMINHAMENTOS = PASTA / "dados" / "encaminhamentos.jsonl"

STATUS = {
    "aguardando_confirmacao": "ainda não foi confirmado pela cozinha",
    "em_preparo": "está sendo preparado",
    "saiu_para_entrega": "já saiu para entrega",
    "entregue": "foi entregue",
    "cancelado": "foi cancelado",
    "problema_reportado": "tem um problema em análise por uma pessoa",
}


def _carregar_pedidos() -> list[dict]:
    dados = json.loads(PEDIDOS.read_text(encoding="utf-8"))
    return dados["pedidos"]


def consultar_pedido(codigo: str) -> dict:
    codigo = codigo.strip().upper()
    for pedido in _carregar_pedidos():
        if pedido["codigo"].upper() == codigo:
            frase = STATUS.get(pedido["status"], "status não cadastrado")
            return {
                "ok": True,
                "codigo": pedido["codigo"],
                "status": pedido["status"],
                "frase": f"O pedido {pedido['codigo']} {frase}.",
                "itens": pedido["itens"],
                "total_reais": pedido["total_reais"],
                "nota": pedido.get("nota", ""),
            }
    return {
        "ok": False,
        "codigo": codigo,
        "frase": f"Não encontrei o pedido {codigo}. Confere o código. Os de teste vão de LM1001 a LM1008.",
    }


def somar_total(nomes: list[str], entrega: bool = True) -> dict:
    cardapio = carregar_cardapio()
    achados, faltando, ja = [], [], set()
    for nome in nomes:
        chave = norm(nome)
        if not chave or chave in ja:
            continue
        item = cardapio.get(chave)
        if item is None:
            faltando.append(nome)
            continue
        ja.add(chave)
        achados.append({"nome": item["nome"], "preco_reais": item["preco_reais"]})

    if faltando or not achados:
        return {
            "ok": False,
            "frase": "Não somei. Estes nomes não estão no cardápio: " + ", ".join(faltando or nomes) + ".",
            "itens": achados,
            "faltando": faltando,
        }

    subtotal = round(sum(i["preco_reais"] for i in achados), 2)
    taxa = 6.90 if entrega else 0.0
    total = round(subtotal + taxa, 2)
    return {
        "ok": True,
        "itens": achados,
        "subtotal_reais": subtotal,
        "taxa_entrega_reais": taxa,
        "total_reais": total,
        "frase": f"Subtotal R$ {subtotal:.2f}, taxa de entrega R$ {taxa:.2f}, total R$ {total:.2f}.",
    }

def encaminhar_humano(motivo: str, resumo: str) -> dict:
    registro = {"motivo": motivo, "resumo": resumo}
    with ENCAMINHAMENTOS.open("a", encoding="utf-8") as arquivo:
        arquivo.write(json.dumps(registro, ensure_ascii=False) + "\n")
    return {
        "ok": True,
        "frase": "Encaminhei para uma pessoa da Cantina Lume. Eu não confirmo cancelamento, reembolso nem pagamento.",
    }