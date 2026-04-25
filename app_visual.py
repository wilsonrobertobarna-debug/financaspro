import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE (Pode colar o JSON inteiro aqui, o código vai garimpar)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Validando credenciais...")
def conectar_google():
    # --- LIMPEZA NÍVEL HARD ---
    # Passo 1: Resolve os \n literais que o JSON coloca
    passo1 = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # Passo 2: EXTRAÇÃO POR MARCADOR
    # O regex abaixo busca APENAS o que começa com BEGIN e termina com END.
    # Isso joga no lixo qualquer e-mail (@) ou nome de campo (private_key_) que veio junto.
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", passo1)
    
    if not match:
        st.error("🚨 Marcadores BEGIN/END não encontrados! Verifique se copiou a chave toda.")
        st.stop()
    
    chave_isolada = match.group(0)
    
    # Passo 3: Limpeza de linhas (remove espaços invisíveis que o Windows adora colocar)
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
    # Conecta à planilha pelo ID que você já usa
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    st.success("✅ Conexão estabelecida com sucesso!")
    
    # Visualização rápida
    df = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    if not df.empty:
        st.subheader("📋 Últimos Registros")
        st.dataframe(df.tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("💡 Wilson, tente o seguinte: abra o seu arquivo .json no BLOCO DE NOTAS (Notepad) e copie APENAS o conteúdo de 'private_key' (sem as aspas).")
