import streamlit as st
from datetime import date

# 1. Configuração da Página (O Título que aparece no navegador)
st.set_page_config(
    page_title="FinançasPro",
    page_icon="🛡️",
    layout="wide"
)

# Estilo para o botão ficar azul e bonito
st.markdown("""
    <style>
    .stButton>button { 
        width: 100%; 
        background-color: #007bff; 
        color: white; 
        font-weight: bold;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛡️ FinançasPro")

# 2. O Formulário de Lançamentos
# O 'clear_on_submit=True' limpa os campos depois que você clica em salvar
with st.form("meu_formulario", clear_on_submit=True):
    st.subheader("Cadastro de Transações")
    
    # Criando duas colunas para aproveitar o espaço
    col1, col2 = st.columns(2)
    
    with col1:
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
        data = st.date_input("Data", value=date.today())
        tipo = st.selectbox("Tipo", ["Saída", "Entrada"])
        
    with col2:
        # Aqui estão os campos de Categoria, Bancos e Cartões que você pediu
        categoria = st.selectbox("Categoria", ["Alimentação", "Lazer", "Contas Fixas", "Saúde", "Transporte", "Outros"])
        banco = st.selectbox("Bancos", ["Nubank", "Itaú", "Bradesco", "Santander", "Caixa", "Dinheiro Vivo"])
        cartao = st.selectbox("Cartões de Créditos", ["Nenhum", "Visa", "Mastercard", "Elo"])

    # Campo de descrição logo abaixo
    descricao = st.text_input("Descrição", placeholder="Ex: Compra no mercado, Salário...")
    
    # Botão de Salvar
    btn_salvar = st.form_submit_button("Salvar Lançamento")

# 3. O que acontece quando você clica no botão
if btn_salvar:
    # Mostra uma mensagem de sucesso na tela
    st.success(f"Lançamento de R$ {valor:.2f} registrado com sucesso!")
    
    # Cria uma pequena tabela só para conferir o que foi salvo agora
    st.write("---")
    st.write("**Resumo do Lançamento:**")
    st.write(f"📅 **Data:** {data} | 🏷️ **Categoria:** {categoria}")
    st.write(f"🏦 **Banco:** {banco} | 💳 **Cartão:** {cartao}")
    st.write(f"📝 **Descrição:** {descricao}")
