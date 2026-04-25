import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE (Pode colar o JSON INTEIRO aqui, sem limpar nada)
# O código abaixo vai "caçar" a chave no meio do texto e ignorar e-mails e nomes de campos.
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Validando segurança...")
def conectar_google():
    # --- OPERAÇÃO GARIMPO ---
    # 1. Converte \n literais (comuns no JSON) em quebras reais
    texto = CHAVE_PRIVADA_BRUTA.replace("\\n", "\n")
    
    # 2. FILTRO CIRÚRGICO: Extrai APENAS o que está entre BEGIN e END
    # Isso joga fora o erro 95 (underline) e o erro 64 (@) instantaneamente
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", texto)
    
    if not match:
        st.error("🚨 Marcadores não encontrados! Verifique se você colou do '-----BEGIN' até o 'END-----'.")
        st.stop()
    
    chave_pura = match.group(0)
    
    # 3. Limpa espaços fantasmas no início/fim de cada linha
    linhas = [l.strip() for l in chave_pura.split('\n') if l.strip()]
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

# --- INTERFACE PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)
    
    st.success("✅ Conexão estabelecida com sucesso!")
    
    # Teste de leitura
    dados = ws.get_all_records()
    if dados:
        st.dataframe(pd.DataFrame(dados).tail(5), use_container_width=True)

except Exception as e:
    st.error(f"Erro detectado: {e}")
    st.info("💡 Se o erro persistir, abra seu arquivo .json no BLOCO DE NOTAS e copie a chave novamente.")
