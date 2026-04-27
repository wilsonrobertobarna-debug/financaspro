import streamlit as st
import pandas as pd
from datetime import date

# 1. Configuração da Página (O "RG" do seu App)
st.set_page_config(
    page_title="FinançasPro",
    page_icon="🛡️",
    layout="wide"
)

# Estilização personalizada para deixar o visual mais limpo
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_key_html=True)

st.title("🛡️ FinançasPro")
st.subheader("Gerenciador de Finanças Pessoais")

# 2. Inicialização do Banco de Dados (na memória do navegador)
if 'historico' not in st.session_state:
    st.session_state.historico = pd.DataFrame(columns=[
        'Data', 'Descrição', 'Categoria', 'Valor', 'Tipo', 'Banco', 'Cartão'
    ])

# 3. Formulário de Cadastro
with st.form("form_lancamento", clear_on_submit=True):
    st.write("### Novo Lançamento")
    
    col1, col2 = st.columns(2)
    
    with col1:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        data = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        descricao = st.text_input("Descrição", placeholder="Ex: Aluguel, Mercado...")
        
    with col2:
        categoria = st.selectbox("Categoria", ["Alimentação", "Lazer", "Contas Fixas", "Saúde", "Transporte", "Outros"])
        banco = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Santander", "Caixa", "Dinheiro Vivo"])
        cartao = st.selectbox("Cartão de Crédito", ["Nenhum", "Visa Principal", "Mastercard Reserva", "Elo"])

    btn_salvar = st.form_submit_button("Salvar Lançamento")

# 4. Lógica para salvar os dados
if btn_salvar:
    novo_dado = pd.DataFrame([{
        'Data': data,
        'Descrição': descricao,
        'Categoria': categoria,
        'Valor': valor if tipo == "Entrada" else -valor, # Saídas ficam negativas
        'Tipo': tipo,
        'Banco': banco,
        'Cartão': cartao
    }])
    
    # Adiciona ao histórico existente
    st.session_state.historico = pd.concat([st.session_state.historico, novo_dado], ignore_index=True)
    st.success("Lançamento registrado com sucesso!")

---

# 5. Visualização dos Dados
st.divider()
st.subheader("📋 Últimos Lançamentos")

if not st.session_state.historico.empty:
    # Mostra a tabela com os dados formatados
    st.dataframe(st.session_state.historico.sort_values(by='Data', ascending=False), use_container_width=True)
    
    # Resumo rápido
    total = st.session_state.historico['Valor'].sum()
    cor_saldo = "green" if total >= 0 else "red"
    st.markdown(f"### Saldo Total: <span style='color:{cor_saldo}'>R$ {total:.2f}</span>", unsafe_allow_html=True)
else:
    st.info("Nenhum lançamento registrado ainda.")
