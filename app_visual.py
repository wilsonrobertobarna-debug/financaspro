import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. COLE SUA CHAVE AQUI (Pode vir com "sujeira", o código vai limpar)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP
... COLE O RESTO DA SUA CHAVE AQUI ...
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # --- OPERAÇÃO LIMPEZA TOTAL ---
    # 1. Resolve o problema do \n literal que vem do JSON
    raw_key = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # 2. FILTRO ANTI-ERRO 95 (Underline) e 64 (@): 
    # Extrai APENAS o bloco que começa com BEGIN e termina com END.
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", raw_key)
    
    if match:
        key_processada = match.group(0)
    else:
        # Se não achou os marcadores, tenta usar a string limpa
        key_processada = raw_key

    # 3. Reconstroi a chave linha por linha para garantir pureza
    linhas = [l.strip() for l in key_processada.split('\n') if l.strip()]
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
try:
    client = conectar_google()
    # Substitua pelo ID da sua planilha se necessário
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    st.success("✅ Wilson, o FinançasPro está ONLINE!")
    
    # Resto do seu código de carregar dados...
    df = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    st.dataframe(df.tail(10))

except Exception as e:
    st.error(f"Erro na conexão: {e}")
    st.info("Dica: Certifique-se de que colou a chave completa, começando em -----BEGIN e terminando em -----END")
