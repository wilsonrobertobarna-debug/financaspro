import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. ÁREA DA CHAVE (SUBSTITUA TUDO ABAIXO PELA SUA CHAVE ORIGINAL)
# DICA: Verifique se a chave começa com "-----BEGIN PRIVATE KEY-----" 
# e termina com "-----END PRIVATE KEY-----"
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    "COLE_AQUI_SUA_CHAVE_COMPLETA_DO_ARQUIVO_JSON",
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar():
    try:
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        info = {
            "type": "service_account",
            "project_id": "financaspro-wilson",
            "private_key": "\n".join(PK_LIST).replace("\\n", "\n"),
            "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        creds = Credentials.from_service_account_info(info, scopes=scope)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro Crítico na Chave: {str(e)}")
        return None

# --- EXECUÇÃO DO SISTEMA ---
try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    client = conectar()
    
    if client:
        sh = client.open_by_key(SHEET_ID)
        st.success("✅ Conectado com Sucesso!")

        tab1, tab2 = st.tabs(["🚀 Lançamentos", "🏦 Bancos"])

        with tab1:
            with st.form("registro_simples", clear_on_submit=True):
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                valor = st.number_input("Valor", min_value=0.0, step=0.01)
                desc = st.text_input("Descrição")
                
                if st.form_submit_button("Salvar na Planilha"):
                    data_hj = datetime.now().strftime('%d/%m/%Y')
                    # Grava os dados como strings para evitar erros de tipo
                    sh.get_worksheet(0).append_row([str(data_hj), str(valor), str(desc), str(tipo)])
                    st.balloons()
                    st.info(f"Registrado: {desc} - R$ {valor}")

        with tab2:
            st.subheader("Visualização de Bancos")
            try:
                # Tenta ler a aba 'bancos', se falhar, avisa sem travar o app
                dados = sh.worksheet("bancos").get_all_records()
                if dados:
                    st.dataframe(pd.DataFrame(dados).astype(str))
                else:
                    st.write("Aba 'bancos' encontrada, mas está vazia.")
            except:
                st.warning("⚠️ Aba 'bancos' não detectada na planilha.")

except Exception as e:
    st.error(f"Erro Geral: {str(e)}")
