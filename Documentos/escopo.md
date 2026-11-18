# Escopo MVP — Agente Cantina Lume

## Problema

O restaurante fictício Cantina Lume perde tempo no atendimento.
O cliente pergunta preço, alérgeno, horário e status do pedido.
Resposta errada (preço inventado ou ingrediente omitido) gera cancelamento.

## Usuário

Só o cliente final. Dono, entregador e operador ficam de fora.

## O agente faz (só isso)

1. Responde cardápio, preço, ingrediente, alérgeno, horário e política
com base num documento. Se não estiver no documento, diz que não sabe.
2. Consulta o status de um pedido fictício por um código.
3. Soma o total dos itens que o cliente montou, com os preços do cardápio.
4. Lembra, na mesma conversa, restrição alimentar e itens já citados.
5. Encaminha para um humano em reclamação grave, reembolso ou assunto fora da base.

## Fora do MVP

* API real do iFood, pagamento, Pix, nota fiscal, login
* WhatsApp, Telegram, voz
* Vários restaurantes e vários usuários com conta
* Treinar modelo próprio
* Foto de prato e painel do dono
* Qualquer dado pessoal real. Tudo fictício.

## Frase do LinkedIn

Agente de atendimento de um restaurante parceiro que responde com base
no cardápio, consulta pedido, calcula total e escala para humano quando não sabe.

## Critério de pronto

1. Preço de um item do cardápio volta com o valor do documento.
2. Item que não existe recebe "não encontrei", nunca um preço chutado.
3. Código de pedido devolve o status cadastrado.
4. "Troca a batata por salada" funciona sem o cliente repetir o prato.
5. Pedido de reembolso é encaminhado, não resolvido pelo agente.
6. Uma pessoa de fora entende o que o agente faz em menos de 1 minuto.

## Stack travada

* LLM: Gemini, gemini-3.8-flash, chave no Google AI Studio
* Agente: LangGraph (classificar, buscar, ferramenta, encaminhar)
* RAG: Chroma + embeddings locais multilingual-e5-small
* Ferramentas: consultar\_pedido, somar\_total, encaminhar\_humano
* Interface: Streamlit
* Fora: OpenAI, multiagente, WhatsApp, API real, banco na nuvem



\## Parte 5 — Sistema de busca (RAG)



\### Indexação



Foi criado o script `indexar.py`, responsável por ler os arquivos do cardápio e as políticas da Cantina Lume e armazená-los no Chroma.



\- Banco vetorial: Chroma

\- Modelo de embeddings: `intfloat/multilingual-e5-small`

\- Coleção: `cantina\_lume`

\- Armazenamento: pasta `.chroma`

\- Total indexado: 25 documentos

\- Tipos encontrados: `cardapio` e `politica`



Também foi criado o script `buscar.py` para realizar consultas e recuperar os documentos mais relevantes.



\### Testes de recuperação



\*\*Teste 1 — Preço do Hambúrguer Lume\*\*



Pergunta: "quanto custa o hamburguer lume"



Resultado:

\- Primeiro documento: `cardapio:hamburguer-lume`

\- Preço recuperado: R$ 34,90

\- Distância: 0.1036



Status: APROVADO.



\*\*Teste 2 — Batata grande\*\*



Pergunta: "tem batata grande"



Resultado:

\- Primeiro documento: `cardapio:batata-frita`

\- Preço: R$ 14,90

\- Descrição: porção única.

\- Não existe tamanho grande no documento.



Distância: 0.1542



Status: APROVADO.



\*\*Teste 3 — Entrega e taxa\*\*



Pergunta: "vocês entregam a 6 km e qual a taxa"



Resultado:

\- Primeiro documento: `politica:entrega`

\- Limite de entrega: 4 km

\- Taxa: R$ 6,90

\- Distância: 0.1072



Status: APROVADO.



\*\*Teste 4 — Alergia a amendoim\*\*



Pergunta: "sou alergico a amendoim, posso comer brownie"



Resultado:

\- Primeiro documento: `cardapio:brownie`

\- Ingrediente amendoim encontrado.

\- Alergênicos: glúten, lactose, ovo e amendoim.

\- Segundo documento: `politica:alergia`

\- Distância do primeiro resultado: 0.098



Status: APROVADO.



\*\*Teste 5 — Reembolso\*\*



Pergunta: "quero reembolso do pedido"



Resultado:

\- Primeiro documento: `politica:reembolso`

\- Prazo informado: até 5 dias úteis após a análise.

\- Análise realizada por uma pessoa.

\- Distância: 0.124



Status: APROVADO.



\### Resultado da Parte 5



Os cinco testes de recuperação foram executados e aprovados.



A busca conseguiu recuperar corretamente informações sobre preços, produtos, entrega, alergênicos e reembolso.



\*\*Conclusão: Parte 5 concluída com 5 de 5 testes aprovados.\*\*

