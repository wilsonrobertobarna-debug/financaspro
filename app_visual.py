import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="FinançasPro - Wilson", layout="wide")

# Título Principal
st.markdown("<h1 style='text-align: center; color: #2E7D32;'>💰 FinançasPro - Wilson</h1>", unsafe_allow_html=True)
st.divider()

import streamlit as st
from streamlit_gsheets import GSheetsConnection

# INJEÇÃO DIRETA: Isso simula o preenchimento do segredo sem usar o painel do site
if "connections" not in st.secrets:
    st.secrets["connections"] = {}

st.secrets["connections"]["gsheets"] = {
    "spreadsheet": "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit",
    "type": "service_account",
    "project_id": "financaspro-wilson",
    "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
    "token_uri": "https://oauth2.googleapis.com/token",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP\ngcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu\nBPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx\n74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox\nKe7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m\nkJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs\nrwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0\nFRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7\nnroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq\xlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au\nfWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t\nMcYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL\nYGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ\nBsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT\nqwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS\nNs8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB\nN9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw\nGW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC\nIXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA\no/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz\nMXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4\nqQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN\nIrq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA\nVnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW\nO02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb\n1GHhDwH33nMtylvbUkBN8pBU\n-----END PRIVATE KEY-----"
}

# Agora chamamos a conexão normalmente. Ela vai achar que os dados vieram do painel lateral.
conn = st.connection("gsheets", type=GSheetsConnection)

# Conecta enviando o dicionário diretamente para o parâmetro service_account_info
conn = st.connection("gsheets", type=GSheetsConnection, service_account_info=service_account_info)
# 2. Passamos o dicionário para o parâmetro correto
conn = st.connection("gsheets", type=GSheetsConnection, secrets=credentials_dict)

# Conecta usando o dicionário local em vez do st.secrets
conn = st.connection("gsheets", type=GSheetsConnection, **credentials_dict)

# O restante do seu código continua igual abaixo...
url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit"

def carregar_dados():
    return conn.read(worksheet="LANCAMENTOS", ttl="0")

def salvar_dados(df_novo):
    conn.update(worksheet="LANCAMENTOS", data=df_novo)
    st.cache_data.clear()

# Carregamento Inicial
try:
    df_atual = carregar_dados()
except Exception as e:
    st.error("Erro ao conectar na Planilha. Verifique os Secrets.")
    st.stop()

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Lançar Dados", "Extrato & Gráficos"])

if aba == "Lançar Dados":
    st.subheader("📝 Novo Lançamento")
    
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        with col2:
            categoria = st.text_input("Categoria (Ex: Mercado, Salário)")
            descricao = st.text_input("Descrição")
            banco = st.selectbox("Banco/Cartão", ["NuBank", "Itaú", "Inter", "Dinheiro"])
        
        btn_gravar = st.form_submit_button("🚀 GRAVAR NO GOOGLE SHEETS")

    if btn_gravar:
        novo_registro = pd.DataFrame([{
            "DATA": data.strftime("%d/%m/%Y"),
            "VALOR": valor if tipo == "Receita" else -valor,
            "CATEGORIA": categoria,
            "DESCRICAO": descricao,
            "BANCO": banco,
            "TIPO": tipo
        }])
        
        df_final = pd.concat([df_atual, novo_registro], ignore_index=True)
        salvar_dados(df_final)
        st.success("✅ Lançamento gravado com sucesso!")
        st.balloons()

elif aba == "Extrato & Gráficos":
    st.subheader("📊 Resumo Financeiro")
    
    if not df_atual.empty:
        # Cálculos Rápidos
        receitas = df_atual[df_atual['VALOR'] > 0]['VALOR'].sum()
        despesas = df_atual[df_atual['VALOR'] < 0]['VALOR'].sum()
        saldo = receitas + despesas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Despesas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        
        # Tabela e Gráfico
        col_tab, col_gra = st.columns([1.2, 1])
        with col_tab:
            st.write("📋 Últimos Lançamentos")
            st.dataframe(df_atual.sort_index(ascending=False), use_container_width=True)
        
        with col_gra:
            st.write("💡 Despesas por Categoria")
            df_gastos = df_atual[df_atual['VALOR'] < 0]
            if not df_gastos.empty:
                fig = px.pie(df_gastos, values=abs(df_gastos['VALOR']), names='CATEGORIA', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado na planilha.")
