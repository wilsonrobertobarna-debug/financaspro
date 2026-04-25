import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
# DICA: Wilson, pode colar o bloco do JSON aqui sem medo. 
# O código abaixo vai "garimpar" a chave real e jogar o lixo (e-mails, underlines) fora.
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Conectando ao Google...")
def conectar_google():
    # --- OPERAÇÃO LIMPEZA TOTAL ---
    # Passo 1: Resolve os \n que o JSON coloca no texto
    texto = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # Passo 2: EXTRAÇÃO CIRÚRGICA
    # Busca apenas o que está entre os marcadores oficiais.
    # Isso ignora o erro 95 (underline) e o erro 64 (@) automaticamente.
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", texto)
    
    if not match:
        st.error("🚨 Marcadores BEGIN/END não encontrados! Verifique se copiou a chave toda.")
        st.stop()
    
    chave_isolada = match.group(0)
    
    # Passo 3: Limpeza de linhas (remove espaços invisíveis das pontas)
    linhas = [l.strip() for l in chave_isolada.split('\n') if l.strip()]
    chave_final = "\n".join(linhas)
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_info = {
        "type": "service_account", 
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", 
        "private_key": chave_final
    }
    
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- INTERFACE ---
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)
    
    st.success("✅ Conexão estabelecida!")
    
    # Visualização simples para teste
    df = pd.DataFrame(ws.get_all_records())
    if not df.empty:
        st.dataframe(df.tail(10))

except Exception as e:
    st.error(f"Erro detectado: {e}")
