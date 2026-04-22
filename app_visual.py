import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuração da página
st.set_page_config(page_title="FinançasPro", layout="wide", page_icon="💰")

# --- CONEXÃO ---
url = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        dados = conn.read(spreadsheet=url, worksheet="LANCAMENTOS")
        # Padroniza colunas e remove espaços
        dados.columns = [str(c).upper().strip() for c in dados.columns]
        # Converte coluna de data
        if 'DT' in dados.columns:
            dados['DT'] = pd.to_datetime(dados['DT'], errors='coerce')
        return dados
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

# --- LOGIN ---
if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.title("🔐 Acesso FinançasPro")
    senha = st.text_input("Senha:", type="password")
    if st.button("Acessar Sistema"):
        if senha == "1234":
            st.session_state.autenticado = True
            st.rerun()
        else:
            st.error("Senha incorreta.")
    st.stop()

# --- SISTEMA PRINCIPAL ---
df = carregar_dados()

if df.empty:
    st.warning("Planilha vazia ou aba 'LANCAMENTOS' não encontrada.")
    st.stop()

st.title("📊 Painel Financeiro - FinançasPro")

# --- MÉTRICAS PRINCIPAIS ---
receitas = df[df['TIPO'] == 'Receita']['VALOR'].sum()
despesas = df[df['TIPO'] == 'Despesa']['VALOR'].sum()
saldo = receitas - despesas

c1, c2, c3 = st.columns(3)
c1.metric("Total Receitas", f"R$ {receitas:,.2f}", delta_color="normal")
c2.metric("Total Despesas", f"R$ {despesas:,.2f}", delta="-")
c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")

st.markdown("---")

# --- GRÁFICOS E ANÁLISES ---
col_esq, col_dir = st.columns(2)

with col_esq:
    st.subheader("Gastos por Categoria")
    df_gastos = df[df['TIPO'] == 'Despesa']
    fig_cat = px.pie(df_gastos, values='VALOR', names='CATEGORIA', hole=0.4)
    st.plotly_chart(fig_cat, use_container_width=True)

with col_dir:
    st.subheader("Gastos por Centro de Custo")
    if 'CENTRO_CUSTO' in df.columns:
        fig_cc = px.bar(df_gastos, x='CENTRO_CUSTO', y='VALOR', color='CENTRO_CUSTO')
        st.plotly_chart(fig_cc, use_container_width=True)

st.markdown("---")

# --- TABELA DE LANÇAMENTOS ---
st.subheader("📝 Histórico de Transações")
# Seletor para filtrar
filtro_cc = st.multiselect("Filtrar por Centro de Custo:", options=df['CENTRO_CUSTO'].unique())

if filtro_cc:
    df_mostrar = df[df['CENTRO_CUSTO'].isin(filtro_cc)]
else:
    df_mostrar = df

st.dataframe(df_mostrar.sort_values(by='DT', ascending=False), use_container_width=True)

# Sidebar com informações do Pet
st.sidebar.title("🐾 FinançasPro")
st.sidebar.info("Gerencie suas finanças pessoais e do seu Golden Retriever.")
if st.sidebar.button("Deslogar"):
    st.session_state.autenticado = False
    st.rerun()
