# Avaliação da demo local

Data: 18/11/2026. Interface Streamlit, mesma função já validada no terminal.
Roteiro de 12 frases, sessão limpa entre total com entrega e total para retirada.
Não é taxa de acerto. É o resultado deste roteiro.

## O que foi conferido

| # | Pergunta | Esperado | Resultado |
|---|---|---|---|
| 1 | quanto custa o hamburguer lume | 34,90, sem 42,90 | passou |
| 2 | tem batata grande? | recusa, sem preço inventado | passou; ofereceu Batata Frita a 14,90 |
| 3 | hambúrguer lume sem cebola e batata frita | 34,90, cebola pode sair, 14,90 | passou |
| 4 | troca a batata por salada extra | não pede para repetir o lanche | passou; Salada Extra 9,90; cebola lembrada |
| 5 | total com entrega | 49,80 + 6,90 = 56,70 | passou |
| 6 | total para retirada | taxa 0, total 49,80 | passou |
| 7 | cadê o pedido LM1002 | saiu para entrega | passou |
| 8 | cadê o pedido LM9999 | não encontrou, faixa LM1001 a LM1008 | passou |
| 9 | reembolso do LM1007 | encaminha, não aprova | passou |
| 10 | entrega a 6 km | não, limite 4 km | passou |
| 11 | alergia a amendoim e brownie | não, tem amendoim | passou; citou contaminação cruzada |
| 12 | telefone do gerente | não encontrou, sem número | passou |

## Leitura

Fidelidade: preço, status e total saíram da base ou do cálculo. Telefone, pedido inexistente e item inexistente não foram inventados.

Relevância: cada pergunta caiu no caminho certo. Cardápio não virou soma. Reembolso não virou cardápio. A troca de item usou a memória da conversa.

Recusa: batata grande, LM9999, 6 km, amendoim e telefone foram recusados. Reembolso foi encaminhado, não concedido.

Limite desta avaliação: 12 frases, um restaurante fictício, uma sessão por vez. Não houve amostra grande, não houve usuário real e não há porcentagem de acerto.

Latência: a primeira mensagem da sessão demora mais, porque o modelo de embeddings carrega. As seguintes respondem na mesma sessão. Não foi cronometrado, então não há número de segundos.