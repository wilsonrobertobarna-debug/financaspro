import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÕES DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. FUNÇÃO DE CONEXÃO (Formatada para evitar erro de PEM)
@st.cache_resource
def conectar_google_sheets():
    scope = ["https://www.googleapis.com/auth/spreadsheets", 
             "https://www.googleapis.com/auth/drive"]
    
    # Wilson, mantive exatamente a sua chave, mas usando o formato de bloco do Python
    # para que o interpretador não se confunda com as barras invertidas.
    private_key = (
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP\n"
        "gcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu\n"
        "BPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx\n"
        "74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox\n"
        "Ke7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m\n"
        "kJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs\n"
        "rwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0\n"
        "FRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7\n"
        "nroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq\n"
        "xlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au\n"
        "fWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t\n"
        "McYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL\n"
        "YGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ\n"
        "BsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT\n"
        "qwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS\n"
        "Ns8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB\n"
        "N9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw\n"
        "GW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC\n"
        "IXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA\n"
        "o/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz\n"
        "MXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4\n"
        "qQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN\n"
        "Irq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA\n"
        "VnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW\n"
        "O02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb\n"
        "1GHhDwH33nMtylvbUkBN8pBU\n"
        "-----END PRIVATE KEY-----\n"
    )

    info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": private_key
    }
    
    creds = Credentials.from_service_account_info(info, scopes=scope)
    client = gspread.authorize(creds)
    
    url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit"
    return client.open_by_url(url)

# 3. INTERFACE
st.title("💰 FinançasPro Wilson")

try:
    sh = conectar_google_sheets()
    worksheet = sh.get_worksheet(0)
    
    # Carregamento seguro para DataFrame
    records = worksheet.get_all_records()
    df = pd.DataFrame(records)
    
    st.sidebar.success("Conectado com sucesso! ✅")
    st.subheader("📊 Meus Dados")
    st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("💡 Verifique se o e-mail 'financas-wilson@...' é EDITOR na planilha.")
