import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

# 2. CHAVE DE ACESSO (O código abaixo vai limpar ela para você)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_APENAS_O_CONTEUDO_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # FILTRO DE SEGURANÇA: Extrai apenas o que está entre BEGIN e END
    # Isso joga fora o erro 95 (underline) na hora!
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", CHAVE_PRIVADA_BRUTA)
    
    if not match:
        st.error("🚨 Marcadores não encontrados! Copie desde o BEGIN até o END.")
        st.stop()
        
    chave_limpa = match.group(0).replace("\\n", "\n")
    
    # ... resto do código de conexão ...
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": chave_limpa
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

st.title("🛡️ FinançasPro Wilson")
try:
    client = conectar_google()
    st.success("🔥 Agora sim! Conexão estabelecida.")
except Exception as e:
    st.error(f"Erro: {e}")
