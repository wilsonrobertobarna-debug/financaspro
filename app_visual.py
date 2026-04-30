import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página
st.set_page_config(page_title="FinançasPro", layout="wide", initial_sidebar_state="collapsed")

# Versão do aplicativo no canto superior esquerdo
st.markdown("<div style='font-size: 10px; color: gray;'>Versão 1.0</div>", unsafe_allow_html=True)

# Título do aplicativo
st.title("FinançasPro")
st.markdown("---")

# Inicializa o estado de transações
if "transacoes" not in st.session_state:
    st.session_state.transacoes = []

# Formulário para adicionar nova transação
st.header("Nova Transação")

with st.form(key="form_transacao"):
    col1, col2 = st.columns(2)
    
    with col1:
        # Pega a data atual do sistema
        data_transacao = st.date_input("Data", value=date.today())
        
        # Botão de rendimentos removido, mantido apenas as opções de despesa e outros
        tipo = st.selectbox("Tipo", ["Despesa", "Outros"])
        valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
    
    with col2:
        descricao = st.text_input("Descrição")
        
        # Campos re-incluídos conforme exigido
        centro_custo = st.text_input("Centro de Custo")
        beneficiario = st.text_input("Beneficiário")
        
    submit_button = st.form_submit_button(label="Adicionar Transação")

if submit_button:
    nova_transacao = {
        "Data": data_transacao,
        "Tipo": tipo,
        "Valor": valor,
        "Descrição": descricao,
        "Centro de Custo": centro_custo,
        "Beneficiário": beneficiario
    }
    st.session_state.transacoes.append(nova_transacao)
    st.success("Transação adicionada com sucesso!")

# Visualização dos dados
st.header("Resumo Financeiro")

if st.session_state.transacoes:
    df_transacoes = pd.DataFrame(st.session_state.transacoes)
    st.dataframe(df_transacoes, use_container_width=True)
else:
    st.info("Nenhuma transação cadastrada no momento.")

# Demonstração da linha corrigida
st.markdown("### Metas do Mês")

metas_map = {"Alimentação": 500.00, "Transporte": 300.00}

df_metas_graph = pd.DataFrame({
    'Categoria': ['Alimentação', 'Transporte', 'Lazer'],
    'Valor': [420.00, 250.00, 100.00]
})

# Linha corrigida para aplicar o map corretamente
df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map)

st.dataframe(df_metas_graph, use_container_width=True)
