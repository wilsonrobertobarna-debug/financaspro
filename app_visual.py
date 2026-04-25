import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# 1. COLE SUA CHAVE AQUI (Pode vir com "sujeira", o código vai garimpar)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_APENAS_O_CONTEUDO_DA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Validando segurança...")
def conectar_google():
    # OPERAÇÃO LIMPEZA: O regex busca APENAS o que está entre BEGIN e END.
    # Isso joga o erro 95 (underline) no lixo automaticamente!
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", CHAVE_PRIVADA_BRUTA)
    
    if not match:
        st.error("🚨 Marcadores não encontrados! Verifique se colou do 'BEGIN' até o 'END'.")
        st.stop()
        
    # Resolve os \n que o JSON coloca no meio do texto
    chave_limpa = match.group(0).replace("\\n", "\n")
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": chave_limpa
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

st.title("🛡️ FinançasPro Wilson")
try:
    client = conectar_google()
    st.success("🔥 Agora sim, Wilson! Conexão estabelecida com sucesso.")
except Exception as e:
    st.error(f"Erro persistente: {e}")
