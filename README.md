# Cantina Lume — Agente de Atendimento Inteligente

Demo educacional de um agente de atendimento para um restaurante fictício.
Não tem afiliação com o iFood. Não processa pagamento, não usa API real
de delivery e não deve receber dado pessoal.

O modelo redige. Preço, status de pedido e total saem de arquivo ou de código.

## O que faz

- Responde cardápio, alergênico, item removível, horário e entrega com base nos documentos.
- Consulta pedido fictício pelo código (LM1001 a LM1008).
- Soma o total pelo nome completo do item e aplica taxa só quando a solicitação é de entrega.
- Lembra, na mesma conversa, restrição alimentar e itens já citados.
- Encaminha reclamação, cancelamento, reembolso e assunto fora da base. Não aprova reembolso.

## O que não faz

Pagamento, login, WhatsApp, vários usuários, vários restaurantes e modelo treinado.
Item inexistente, pedido fora da faixa e dado ausente são recusados. Não há chute de preço.

## Base

- 16 itens de cardápio em Markdown, na pasta `dados`
- políticas da casa, inclusive entrega até 4 km com taxa de 6,90 e retirada sem taxa
- 8 pedidos fictícios, de LM1001 a LM1008

Exemplos que a base sustenta: Hambúrguer Lume a 34,90, com cebola removível;
Batata Frita a 14,90; os dois com entrega fecham em 56,70.
Brownie com amendoim é recusado para alergia declarada.

## Como está feito

Python 3.12. Grafo em LangGraph com classificação, busca, ferramenta, redação e memória.
A busca usa Chroma e o modelo de representação multilingual-e5-small.
Se o primeiro trecho estiver acima de 0,45 de distância, o agente recusa.
O modelo é o Gemini (`gemini-3.5-flash-lite`). A chave fica no `.env`, fora do Git.
A tela é Streamlit e chama a mesma função validada no terminal.

## Como rodar

É preciso Python 3.12 e uma chave do Gemini, criada no AI Studio.

```text
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Cria um arquivo `.env` na raiz, sem aspas:

```text
GEMINI_API_KEY=sua_chave
```

Depois:

```text
python indexar.py
streamlit run app.py
```

Abre em `http://localhost:8501`. A primeira mensagem demora, porque o modelo de representação carrega na hora.
O botão Limpar conversa zera a memória da sessão.

## Roteiro mínimo

1. Quanto custa o hambúrguer lume — 34,90
2. Tem batata grande? — não tem
3. Quero o hambúrguer lume sem cebola e uma batata frita — 34,90 e 14,90
4. Qual o total de Hambúrguer Lume e Batata Frita com entrega — 56,70
5. Cadê o pedido LM1002 — saiu para entrega
6. Quero reembolso do LM1007 — encaminha, não aprova

O registro dos 12 casos da demo local está em `avaliacao.md`.
Não é taxa de acerto. É o resultado desse roteiro, em 18/11/2026.

## Aviso

Restaurante fictício. Demo para estudo e portfólio.
Não informe CPF, telefone, endereço nem dado de pagamento.
