import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração da página
st.set_page_config(page_title="FinançasPro", layout="wide")

# Conexão com o Google Sheets
conn = st.connection("gsheets", type=GSheetsConnection)

# Tenta ler os dados da aba "LANCAMENTOS"
try:
    df = conn.read(worksheet="LANCAMENTOS")
    # Padroniza os nomes das colunas para MAIÚSCULO para evitar erros
    df.columns = [str(c).upper().strip() for c in df.columns]
except Exception as e:
    st.error(f"Erro ao ler a aba 'LANCAMENTOS'. Verifique se o nome na planilha está correto.")
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
