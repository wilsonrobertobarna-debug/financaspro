import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# 1. COLE SUA CHAVE AQUI (Mesmo que venha com sujeira, o código vai filtrar)
CHAVE_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_APENAS_O_CONTEUDO_DA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Validando segurança...")
def conectar_google():
    # FAXINA AUTOMÁTICA: O regex busca APENAS o bloco entre BEGIN e END.
    # Isso joga o erro 95 (underline) no lixo instantaneamente!
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", CHAVE_BRUTA)
    
    if not match:
        st.error("🚨 Marcadores não encontrados! Verifique se colou do 'BEGIN' até o 'END'.")
        st.stop()
        
    # Corrige as quebras de linha (\n) que o JSON insere no texto
    chave_final = match.group(0).replace("\\n", "\n").strip()
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": chave_final
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    # Conecta à planilha (substitua o ID se necessário)
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    st.success("🔥 Agora sim, Wilson! O programa está online e conectado.")
    
except Exception as e:
    st.error(f"Erro persistente: {e}")
    st.info("💡 Wilson, se o erro continuar, vá nos 3 pontinhos (canto superior), clique em 'Clear Cache' e dê F5.")
