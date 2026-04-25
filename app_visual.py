import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (O COFRE)
# IMPORTANTE: Pode colar o bloco inteiro do JSON aqui, o código vai filtrar.
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource(show_spinner="Conectando ao cofre...")
def conectar_google():
    # CAMADA 1: Limpeza de quebras de linha literais (\n)
    texto = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # CAMADA 2: Filtro de marcadores (Extrai APENAS o que está entre BEGIN e END)
    # Isso joga fora qualquer e-mail (@) ou ponto (.) que tenha "vazado" na colagem
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", texto)
    if not match:
        st.error("🚨 Erro Crítico: Não encontrei os marcadores BEGIN e END na sua chave!")
        st.stop()
    
    chave_isolada = match.group(0)
    
    # CAMADA 3: Reconstrução Linha por Linha (Garante que não existam espaços invisíveis)
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

# --- INTERFACE PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    client = conectar_google()
    # Conecta à sua planilha
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)
    
    st.success("🔥 Conexão Estabelecida! O sistema está pronto.")
    
    # Exemplo rápido dos últimos dados
    dados = ws.get_all_records()
    if dados:
        st.subheader("📋 Últimos Lançamentos")
        st.table(dados[-5:]) # Mostra os últimos 5

except Exception as e:
    st.error(f"Erro detectado: {e}")
    st.info("💡 Wilson, se o erro persistir, tente abrir o arquivo .json no BLOCO DE NOTAS (Notepad) para copiar a chave limpa.")
