from agente import montar_grafo, nova_sessao, responder_turno

app = montar_grafo()
sessao = nova_sessao()
print("Cantina Lume, teste no terminal. Escreva sair para encerrar.")
print("Memória desta sessão começa vazia.")

while True:
    texto = input("\nvocê: ").strip()
    if texto.lower() in ("sair", "exit", "quit"):
        break
    if not texto:
        continue
    print("agente:", responder_turno(app, sessao, texto))
    print("memória:", sessao.get("memoria"))