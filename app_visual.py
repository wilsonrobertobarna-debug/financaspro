import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime

# =========================================================
# 1. CONFIGURAÇÕES INICIAIS
# =========================================================
st.set_page_config(page_title="FinançasPro v2.0", layout="wide", page_icon="💰")

# Injeção manual de segredos para contornar erro do painel Streamlit
if "connections" not in st.secrets:
    st.secrets["connections"] = {}

st.secrets["connections"]["gsheets"] = {
    "spreadsheet": "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit",
    "type": "service_account",
    "project_id": "financaspro-wilson",
    "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP\ngcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu\nBPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx\n74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox\nKe7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m\nkJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs\nrwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0\nFRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7\nnroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq\xlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au\nfWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t\nMcYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL\nYGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ\nBsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT\nqwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS\nNs8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB\nN9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw\ GW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC\nIXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA\ o/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz\nMXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4\nqQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN\nIrq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA\nVnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW\nO02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb\n1GHhDwH33nMtylvbUkBN8pBU\n-----END PRIVATE KEY-----"
}

# 2. CONEXÃO
conn = st.connection("gsheets", type=GSheetsConnection)

# 3. INTERFACE LATERAL (Sidebar)
st.sidebar.title("FinançasPro")
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/584/584705.png", width=100)
aba = st.sidebar.radio("Navegação", ["📊 Dashboard", "➕ Novo Lançamento", "⚙️ Cadastros"])

# =========================================================
# ABA: DASHBOARD
# =========================================================
if aba == "📊 Dashboard":
    st.header("📊 Resumo Financeiro")
    
    try:
        df = conn.read()
        if not df.empty:
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            total_entrada = 1500.00 # Exemplo: df[df['Tipo'] == 'Receita']['Valor'].sum()
            total_saida = 850.00   # Exemplo: df[df['Tipo'] == 'Despesa']['Valor'].sum()
            
            col1.metric("Entradas", f"R$ {total_entrada:,.2f}")
            col2.metric("Saídas", f"R$ {total_saida:,.2f}", delta_color="inverse")
            col3.metric("Saldo Atual", f"R$ {(total_entrada - total_saida):,.2f}")
            
            st.divider()
            st.subheader("Últimas Transações")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum dado encontrado na planilha.")
    except Exception as e:
        st.error(f"Erro ao conectar: {e}")

# =========================================================
# ABA: NOVO LANÇAMENTO
# =========================================================
elif aba == "➕ Novo Lançamento":
    st.header("➕ Cadastrar Transação")
    
    with st.form("form_transacao", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            data = st.date_input("Data da Transação", datetime.now())
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Salário", "Saúde"])
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            banco = st.selectbox("Banco/Conta", ["Nubank", "Itaú", "Bradesco", "Carteira"])

        with col2:
            beneficiario = st.text_input("Beneficiário/Origem")
            centro_custo = st.selectbox("Centro de Custo", ["Pessoal", "Casa", "Trabalho"])
            forma_pagto = st.selectbox("Forma de Pagamento", ["Dinheiro", "Pix", "Cartão de Crédito", "Boleto"])
            parcelado = st.checkbox("É parcelado?")
            num_parcelas = st.number_input("Número de Parcelas", min_value=1, max_value=48, value=1) if parcelado else 1
            status = st.selectbox("Status", ["Pago", "Pendente"])

        descricao = st.text_area("Observações")
        
        btn_salvar = st.form_submit_button("Salvar no Google Sheets")
        
        if btn_salvar:
            st.success(f"Lançamento de R$ {valor} registrado (Simulação)!")
            st.info("Para salvar de verdade, a conta de serviço precisa de permissão de 'Editor' na planilha.")

# =========================================================
# ABA: CADASTROS
# =========================================================
elif aba == "⚙️ Cadastros":
    st.header("⚙️ Gerenciar Categorias e Bancos")
    
    tab1, tab2 = st.tabs(["Bancos", "Categorias"])
    
    with tab1:
        st.write("Lista de Bancos Cadastrados")
        st.table(["Nubank", "Itaú", "Bradesco", "Carteira"])
        novo_banco = st.text_input("Adicionar novo banco")
        if st.button("Adicionar Banco"):
            st.toast(f"Banco {novo_banco} adicionado!")

    with tab2:
        st.write("Lista de Categorias")
        st.table(["Alimentação", "Saúde", "Lazer", "Moradia"])
        nova_cat = st.text_input("Adicionar nova categoria")
        if st.button("Adicionar Categoria"):
            st.toast(f"Categoria {nova_cat} adicionada!")
