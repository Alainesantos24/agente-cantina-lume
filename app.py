import streamlit as st

from agente import montar_grafo, nova_sessao, responder_turno

st.set_page_config(page_title="Cantina Lume", page_icon="🍽️", layout="centered")

st.title("Cantina Lume")
st.caption(
    "Demo educacional. Restaurante fictício, sem afiliação com o iFood. "
    "Não informe dado pessoal. Preço e status saem dos arquivos, não da cabeça do modelo."
)

with st.sidebar:
    st.subheader("Como testar")
    st.markdown(
        """
- Quanto custa o Hambúrguer Lume?
- Quero o Hambúrguer Lume sem cebola e uma Batata Frita
- Qual o total de Hambúrguer Lume e Batata Frita com entrega
- Cadê o pedido LM1002?
- Quero reembolso do LM1007
        """
    )
    st.caption("Pedidos de teste: LM1001 a LM1008.")
    if st.button("Limpar conversa"):
        st.session_state.sessao = nova_sessao()
        st.session_state.mensagens = []
        st.rerun()

if "app_grafo" not in st.session_state:
    st.session_state.app_grafo = montar_grafo()
if "sessao" not in st.session_state:
    st.session_state.sessao = nova_sessao()
if "mensagens" not in st.session_state:
    st.session_state.mensagens = []

for msg in st.session_state.mensagens:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

pergunta = st.chat_input("Escreve como se fosse pedir no balcão")
if pergunta:
    st.session_state.mensagens.append({"role": "user", "content": pergunta})
    with st.chat_message("user"):
        st.markdown(pergunta)
    with st.chat_message("assistant"):
        with st.spinner("Olhando o cardápio..."):
            resposta = responder_turno(
                st.session_state.app_grafo,
                st.session_state.sessao,
                pergunta,
            )
        st.markdown(resposta)
    st.session_state.mensagens.append({"role": "assistant", "content": resposta})