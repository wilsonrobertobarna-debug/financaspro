import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. FUNÇÃO DE CONEXÃO DIRETA (O "Coração" do App)
@st.cache_resource
def conectar_google_sheets():
    # Escopos necessários para o Google Drive e Sheets
    scope = ["https://www.googleapis.com/auth/spreadsheets", 
             "https://www.googleapis.com/auth/drive"]
    
    # Suas credenciais em formato de dicionário
    info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": r"-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP\ngcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu\nBPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx\n74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox\nKe7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m\nkJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs\nrwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0\nFRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7\nnroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq\xlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au\nfWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t\nMcYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL\nYGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ\nBsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT\nqwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS\Ns8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB\nN9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw\ GW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC\nIXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA\ o/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz\nMXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4\nqQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN\nIrq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA\nVnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW\nO02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb\n1GHhDwH33nMtylvbUkBN8pBU\n-----END PRIVATE KEY-----"
    }
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    # Abre a planilha pelo link
    url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit"
    return client.open_by_url(url)

# 3. INTERFACE
st.title("💰 FinançasPro Wilson")

try:
    sh = conectar_google_sheets()
    worksheet = sh.get_worksheet(0) # Pega a primeira aba
    
    # Lê os dados
    df = pd.DataFrame(worksheet.get_all_records())
    
    st.success("Conexão estabelecida via Gspread!")
    st.sidebar.markdown(f"**Status:** Conectado ✅")
    
    aba = st.sidebar.radio("Navegação", ["Resumo", "Novo Lançamento"])
    
    if aba == "Resumo":
        st.subheader("📊 Seus Lançamentos")
        st.dataframe(df, use_container_width=True)
        
    elif aba == "Novo Lançamento":
        with st.form("add_data"):
            data = st.date_input("Data", datetime.now())
            valor = st.number_input("Valor", min_value=0.0)
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            submit = st.form_submit_button("Salvar")
            
            if submit:
                # Exemplo de como adicionar linha (precisa ter as mesmas colunas)
                # worksheet.append_row([str(data), valor, tipo])
                st.info("Função de salvar pronta para ser ativada!")

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("Verifique se o e-mail da conta de serviço é 'Editor' na planilha.")
