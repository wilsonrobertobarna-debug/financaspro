import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE ORIGINAL (A "Digital" do seu App)
# IMPORTANTE: Cole sua chave EXATAMENTE como ela está no arquivo JSON.
# Se a sua chave no JSON tiver '\n', mantenha. Se for uma linha só, mantenha.
CHAVE_BRUTA = """-----BEGIN PRIVATE KEY-----
SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = {
            "type": "service_account",
            "project_id": "financaspro-wilson",
            "private_key": CHAVE_BRUTA.replace("\\n", "\n"),
            "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na Chave: {str(e)}")
        return None

# --- INTERFACE ---
try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    client = conectar()
    
    if client:
        sh = client.open_by_key(SHEET_ID)
        st.success("✅ Conexão Restabelecida!")

        tab1, tab2 = st.tabs(["🚀 Lançamentos", "🏦 Bancos"])

        with tab1:
            with st.form("lancamento"):
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor", min_value=0.0)
                desc = st.text_input("Descrição")
                
                if st.form_submit_button("Salvar"):
                    data_hj = datetime.now().strftime('%d/%m/%Y')
                    sh.get_worksheet(0).append_row([data_hj, valor, desc, tipo])
                    st.success("Lançado!")

        with tab2:
            # Mostra os bancos sem frescura
            try:
                df = pd.DataFrame(sh.worksheet("bancos").get_all_records())
                st.dataframe(df)
            except:
                st.info("Aba 'bancos' não encontrada.")

except Exception as e:
    st.error(f"Erro de Execução: {str(e)}")
