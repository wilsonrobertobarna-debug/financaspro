import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd

# Configuração da página - Isso deve ser a primeira coisa no código
st.set_page_config(page_title="FinançasPro", layout="wide")

# --- CONEXÃO COM A PLANILHA ---
# Usando o seu link direto que está funcionando e com acesso público
url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # Tenta ler a aba LANCAMENTOS
        dados = conn.read(spreadsheet=url, worksheet="LANCAMENTOS")
        # Padroniza as colunas para MAIÚSCULO e tira espaços
        dados.columns = [str(c).upper().strip() for c in dados.columns]
        return dados
    except Exception as e:
        st.error(f"Erro ao conectar com a planilha: {e}")
        return pd.DataFrame()

# --- SISTEMA DE LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso ao FinançasPro")
    senha = st.text_input("Digite a senha secreta:", type="password")
    if st.button("Entrar"):
        if senha == "1234":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta! Tente novamente.")
    st.stop()

# --- SE O USUÁRIO CHEGOU AQUI, ELE ESTÁ LOGADO ---
df = carregar_dados()

st.title("💰 FinançasPro - Dashboard")
st.write(f"Olá, Wilson! Sistema conectado com sucesso.")

if not df.empty:
    # Mostra um resumo rápido para testar
    col1, col2, col3 = st.columns(3)
    
    # Tentando calcular o total se a coluna VALOR existir
    if 'VALOR' in df.columns:
        total = df['VALOR'].sum()
        col1.metric("Saldo Total", f"R$ {total:,.2f}")
    
    st.write("### Suas últimas movimentações:")
    st.dataframe(df)
else:
    st.warning("A planilha foi lida, mas parece estar sem dados na aba 'LANCAMENTOS'.")

# Rodapé lateral
st.sidebar.success("Conectado à planilha Google")
if st.sidebar.button("Sair/Logoff"):
    st.session_state.autenticado = False
    st.rerun()
