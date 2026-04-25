import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (Secrets)
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": private_key,
            "client_email": creds_info["client_email"],
            "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# --- CONFIGURAÇÃO DE METAS ---
META_GASTO_MENSAL = 3000.00 

# --- BARRA LATERAL ---
st.sidebar.header("📝 Novo Lançamento")
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Investimentos", "Presente", "Outros"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Outros"]
}
tipo = st.sidebar.radio("Tipo:", ["Despesa", "Receita"], horizontal=True)

with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data_input = st.date_input("Data", datetime.now())
    valor_input = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    categoria_input = st.selectbox("Categoria", categorias_dict[tipo])
    descricao_input = st.text_input("Descrição")
    
    if st.form_submit_button("Salvar"):
        if valor_input > 0:
            ws.append_row([data_input.strftime("%d/%m/%Y"), valor_input, categoria_input, tipo, descricao_input])
            st.cache_data.clear()
            st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    lista_dados = ws.get_all_values()
    if len(lista_dados) > 1:
        # Cria DataFrame e limpa nomes de colunas
        df = pd.DataFrame(lista_dados[1:], columns=lista_dados[0])
        df.columns = [c.strip() for c in df.columns]

        # CONVERSÃO BLINDADA (Onde a mágica acontece)
        # 1. Trata Valores (ignora textos errados na coluna numérica)
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # 2. Trata Datas (ignora datas mal digitadas)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        
        # Remove linhas onde a data é inválida para não quebrar o gráfico
        df_valid = df.dropna(subset=['Data']).copy()
        df_valid['Mês/Ano'] = df_valid['Data'].dt.strftime('%m/%Y')

        # --- GRÁFICO DE BARRAS COM META ---
        if not df_valid.empty:
            st.subheader("📊 Acompanhamento de Metas e Gastos")
            
            resumo = df_valid.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            
            fig = go.Figure()
            if 'Despesa' in resumo.columns:
                fig.add_trace(go.Bar(x=resumo['Mês/Ano'], y=resumo['Despesa'], name='Gasto Real', marker_color='#dc3545'))
            
            fig.add_trace(go.Scatter(
                x=resumo['Mês/Ano'], 
                y=[META_GASTO_MENSAL] * len(resumo),
                name='Meta', line=dict(color='#ffc107', width=3, dash='dash')
            ))
            
            fig.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=30, b=0))
            st.plotly_chart(fig, use_container_width=True)

        # --- TABELA DE LANÇAMENTOS ---
        st.markdown("---")
        st.subheader("📋 Histórico")
        # Mostra o DF original para você ver onde está o erro (aparecerá como NaT ou 0)
        st.dataframe(df.tail(15), use_container_width=True)
        
    else:
        st.info("Planilha vazia. Use a barra lateral para lançar dados.")

except Exception as e:
    st.error(f"Ocorreu um erro inesperado: {e}")
