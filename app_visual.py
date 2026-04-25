import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# 2. FUNÇÃO DE CONEXÃO (Busca no cofre do Streamlit Cloud)
@st.cache_resource(show_spinner="Conectando ao banco de dados...")
def conectar_google():
    try:
        # Busca o bloco de configuração no painel do Streamlit
        creds_info = st.secrets["connections"]["gsheets"]
        
        # Garante que as quebras de linha da chave sejam lidas corretamente
        # Se você usar as aspas triplas no Secrets, pode remover o .replace se quiser
        private_key = creds_info["private_key"].replace("\\n", "\n")
        
        final_creds = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": private_key,
            "client_email": creds_info["client_email"],
            "token_uri": creds_info["token_uri"],
        }
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro nos Segredos: {e}")
        st.stop()

# 3. INTERFACE
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0)
    
    st.success("✅ Conexão Automática Estabelecida!")

    dados = ws.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df.tail(15), use_container_width=True)
    else:
        st.info("Planilha conectada, mas sem dados para exibir.")

except Exception as e:
    st.error(f"Erro de Execução: {e}")
