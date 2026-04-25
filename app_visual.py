import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# 2. FUNÇÃO DE CONEXÃO BLINDADA
@st.cache_resource(show_spinner="Conectando ao banco de dados...")
def conectar_google():
    try:
        # Busca no cofre
        creds_info = st.secrets["connections"]["gsheets"]
        
        # LIMPEZA DA CHAVE: Remove \n literais, espaços e garante o formato PEM
        raw_key = creds_info["private_key"]
        private_key = raw_key.replace("\\n", "\n").strip()
        
        # Montagem do dicionário (NOMES CURTOS OBRIGATÓRIOS)
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
        st.error(f"❌ Erro Crítico nos Segredos: {e}")
        st.stop()

# 3. INTERFACE
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0)
    
    st.success("✅ Conexão Estabelecida!")

    dados = ws.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        st.dataframe(df.tail(15), use_container_width=True)
    else:
        st.info("Planilha vazia ou sem dados legíveis.")

except Exception as e:
    st.error(f"❌ Erro de Execução: {e}")
