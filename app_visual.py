import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. COLE A CHAVE AQUI (Pode vir com espaços ou \n, o código limpa)
CHAVE_ENTRADA = """-----BEGIN PRIVATE KEY-----
COLE_AQUI_APENAS_O_CONTEUDO_DA_CHAVE
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # --- OPERAÇÃO FAXINA ---
    # Passo 1: Extrai apenas o bloco BEGIN/END (deleta e-mails e underlines externos)
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", CHAVE_ENTRADA)
    if not match:
        st.error("🚨 Wilson, não achei os marcadores BEGIN/END. Verifique a colagem!")
        st.stop()
    
    # Passo 2: Limpa quebras de linha e espaços fantasmas
    chave_final = match.group(0).replace("\\n", "\n").strip()
    
    # Passo 3: Monta as credenciais
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": chave_final
    }
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- INTERFACE ---
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    # Substitua pelo ID da sua planilha se necessário
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    st.success("✅ O programa está VIVO! Conexão restaurada.")
    
    # Mostra os dados para provar que funcionou
    ws = sh.get_worksheet(0)
    st.write("Últimos dados lidos:", ws.get_all_records()[-5:])

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("💡 Wilson, se o erro 95 continuar, limpe o Cache do Streamlit (nos 3 pontinhos do canto superior direito) e dê F5.")
