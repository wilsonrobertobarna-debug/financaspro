import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuração da Página
st.set_page_config(
    page_title="FinançasPro",
    page_icon="🛡️",
    layout="wide"
)

# Estilização para o botão ficar azul e ocupar a largura total
st.markdown("""
    <style>
    .stButton>button { width: 100%; background-color: #007bff; color: white; height: 3em; }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ FinançasPro")

# 2. Inicialização do Histórico (Estado da Sessão)
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=[
        'Data', 'Descrição', 'Categoria', 'Valor', 'Tipo', 'Banco', 'Cartão'
    ])

# 3. Formulário de Cadastro
with st.form("form_lancamento", clear_on_submit=True):
    st.subheader("Novo Lançamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        data = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        
    with col2:
        categoria = st.selectbox("Categoria", ["Alimentação", "Lazer", "Contas Fixas", "Saúde", "Transporte", "Outros"])
        banco = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Santander", "Caixa", "Dinheiro Vivo"])
        cartao = st.selectbox("Cartão de Crédito", ["Nenhum", "Visa", "Mastercard", "Elo"])

    descricao = st.text_input("Descrição", placeholder="Ex: Compra no mercado...")
    btn_salvar = st.form_submit_button("Salvar Lançamento")

# 4. Lógica para Salvar
if btn_salvar:
    # Saídas ficam negativas para o cálculo do saldo
    valor_final = valor if tipo == "Entrada" else -valor
    
    novo_dado = pd.DataFrame([{
        'Data': data,
        'Descrição': descricao,
        'Categoria': categoria,
        'Valor': valor_final,
        'Tipo': tipo,
        'Banco': banco,
        'Cartão': cartao
    }])
    
    st.session_state.historico = pd.concat([st.session_state.historico, novo_dado], ignore_index=True)
    st.success("Lançamento registrado!")

# 5. Visualização (A linha que causou o erro agora está correta aqui)
st.divider()
st.subheader("📋 Últimos Lançamentos")

if not st.session_state.historico.empty:
    # Exibe a tabela
    st.dataframe(st.session_state.historico.sort_values(by='Data', ascending=False), use_container_width=True)
    
    # Cálculo do Saldo
    saldo = st.session_state.historico['Valor'].sum()
    cor = "green" if saldo >= 0 else "red"
    st.markdown(f"### Saldo Atual: :[{cor}][R$ {saldo:.2f}]")
else:
    st.info("Nenhum dado cadastrado.")
