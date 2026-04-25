import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE (Pode colar o bloco do JSON aqui sem medo)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Conectando ao Google...")
def conectar_google():
    # --- LIMPEZA NÍVEL HARD ---
    # Passo 1: Resolve os \n literais do JSON
    texto = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # Passo 2: EXTRAÇÃO CIRÚRGICA
    # O regex busca APENAS o que começa com BEGIN e termina com END.
    # Isso joga no lixo qualquer e-mail (@) ou underline (_) que veio junto.
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", texto)
    
    if not match:
        st.error("🚨 Wilson, não encontrei os marcadores BEGIN e END. Verifique se copiou a chave toda.")
        st.stop()
    
    chave_isolada = match.group(0)
    
    # Passo 3: Reconstroi linha por linha (remove espaços invisíveis)
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
    
    st.success("✅ Wilson, conexão estabelecida! O sistema está pronto.")
    
    # Mostra os últimos dados para confirmar
    dados = ws.get_all_records()
    if dados:
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(pd.DataFrame(dados).tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("💡 Se o erro persistir, no menu do Streamlit (3 pontinhos), clique em 'Clear Cache' e dê F5.")
