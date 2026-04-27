import streamlit as st
import pandas as pd
from datetime import date

# 1. Títulos e Layout (Isso você já fez, só confira)
st.title("🛡️ FinançasPro")
st.subheader("Cadastro de Transações")

# 2. Criando o Formulário
with st.form("meu_formulario", clear_on_submit=True):
    col1, col2 = st.columns(2)
    
    with col1:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        data = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        
    with col2:
        categoria = st.selectbox("Categoria", ["Alimentação", "Lazer", "Contas Fixas", "Saúde", "Outros"])
        banco = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Santander", "Outro"])
        cartao = st.selectbox("Cartão de Crédito", ["Nenhum", "Visa", "Mastercard", "Elo"])

    descricao = st.text_input("Descrição (Ex: Compra no mercado)")
    
    # Botão de Enviar
    enviar = st.form_submit_button("Salvar Lançamento")

if enviar:
    st.success(f"Lançamento de R$ {valor} salvo com sucesso!")
