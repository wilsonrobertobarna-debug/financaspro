import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração da página
st.set_page_config(page_title="FinançasPro", layout="wide")

# Conexão com o Google Sheets
url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit?usp=sharing"
conn = st.connection("gsheets", type=GSheetsConnection)

try:
    # Lendo diretamente pela URL e especificando a aba
    df = conn.read(spreadsheet=url, worksheet="LANCAMENTOS")
    # Limpa nomes de colunas (tira espaços e deixa em maiúsculo)
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error(f"Erro de conexão: {e}")
    st.stop()

# --- LOGIN SIMPLES ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    senha = st.text_input("Digite a senha para acessar o FinançasPro:", type="password")
    if senha == "1234":
        st.session_state.autenticado = True
        st.rerun()
    else:
        if senha:
            st.warning("Senha incorreta!")
        st.stop()

# --- SEU SISTEMA DAQUI PARA BAIXO ---
st.title("💰 FinançasPro")

if not df.empty:
    # Garante que a coluna DT seja data
    df['DT'] = pd.to_datetime(df['DT'], errors='coerce')
    
    st.write("### Últimos Lançamentos")
    st.dataframe(df.head())
else:
    st.info("A planilha está vazia. Comece a lançar seus gastos!")

st.success("Sistema conectado com sucesso à aba LANCAMENTOS!")
