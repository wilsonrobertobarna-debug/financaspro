import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Cole sua PK_LIST completa aqui)
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP",
    # ... (mantenha sua chave completa aqui)
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    info = {
        "type": "service_account", 
        "project_id": "financaspro-wilson",
        "private_key": "\n".join(PK_LIST),
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

# --- SISTEMA ---
try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    client = conectar()
    sh = client.open_by_key(SHEET_ID)

    st.title("💰 FinançasPro Wilson")
    
    tab1, tab2 = st.tabs(["🚀 Lançamentos", "🏦 Bancos"])

    with tab1:
        with st.form("form_simples", clear_on_submit=True):
            tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
            valor = st.number_input("Valor", min_value=0.0, step=0.01)
            desc = st.text_input("Descrição")
            
            if st.form_submit_button("Salvar"):
                data_hj = datetime.now().strftime('%d/%m/%Y')
                # Enviando apenas como strings para não dar erro de tipo
                sh.get_worksheet(0).append_row([str(data_hj), str(valor), str(desc), str(tipo)])
                st.success("Salvo!")

    with tab2:
        st.subheader("Contas Cadastradas")
        try:
            # Força o pandas a ler tudo como texto para evitar erro de int/str
            dados = sh.worksheet("bancos").get_all_records()
            if dados:
                df = pd.DataFrame(dados)
                st.dataframe(df.astype(str))
            else:
                st.info("Aba 'bancos' está vazia.")
        except:
            st.warning("Aba 'bancos' não encontrada na sua planilha.")

except Exception as e:
    # Mostra o erro de forma que não trave o script
    st.error(f"Erro: {str(e)}")
