import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. SETUP INICIAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CHAVE PRIVADA (Mantenha como você já tem no seu arquivo)
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    # ... (sua chave aqui)
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "private_key": "\n".join(PK_LIST),
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

def carregar_aba(nome_aba):
    """Tenta carregar os dados e limpa os nomes das colunas"""
    try:
        client = conectar()
        sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
        ws = sh.worksheet(nome_aba)
        df = pd.DataFrame(ws.get_all_records())
        df.columns = [str(c).strip().lower() for c in df.columns] # Tudo minúsculo para facilitar
        return df
    except Exception as e:
        return None

# --- INTERFACE ---
tab_lanc, tab_bancos, tab_cartoes, tab_metas, tab_relat = st.tabs([
    "🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas", "📊 Relatórios"
])

with tab_bancos:
    df_b = carregar_aba("bancos")
    if df_b is not None and not df_b.empty:
        st.dataframe(df_b, use_container_width=True)
    else:
        st.warning("⚠️ Dados não encontrados na aba 'bancos'. Verifique se ela existe no Google Sheets.")

with tab_metas:
    df_m = carregar_aba("metas")
    if df_m is not None and not df_m.empty:
        # Tenta identificar colunas de valor
        col_v = next((c for c in df_m.columns if 'alvo' in c or 'valor' in c), None)
        col_n = next((c for c in df_m.columns if 'nome' in c or 'meta' in c), df_m.columns[0])
        
        if col_v:
            fig = px.bar(df_m, x=col_n, y=col_v, title="Suas Metas")
            st.plotly_chart(fig, use_container_width=True)
        st.table(df_m)
    else:
        st.info("💡 Adicione metas na sua planilha para visualizá-las aqui.")

with tab_relat:
    # Carrega a aba de lançamentos (ajuste o nome se for diferente de 'lancamentos')
    df_l = carregar_aba("lancamentos") 
    if df_l is not None and not df_l.empty:
        if 'tipo' in df_l.columns and 'valor' in df_l.columns:
            # Gráfico simples de Receitas vs Despesas
            resumo = df_l.groupby('tipo')['valor'].sum().reset_index()
            fig_r = px.pie(resumo, values='valor', names='tipo', title="Distribuição Financeira")
            st.plotly_chart(fig_r, use_container_width=True)
        else:
            st.error("A aba de lançamentos precisa das colunas 'tipo' e 'valor'.")
