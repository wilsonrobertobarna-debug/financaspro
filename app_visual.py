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

# 2. CONEXÃO (Utilizando seus Secrets já configurados)
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

# 3. LOGICA DE DADOS
client = conectar_google()
PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
sh = client.open_by_key(PLANILHA_ID)
ws = sh.get_worksheet(0)

# Categorias dinâmicas
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Investimentos", "Presente", "Outros (Receita)"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação", "Outros (Despesa)"]
}

# --- BARRA LATERAL ---
st.sidebar.header("📝 Novo Lançamento")
tipo = st.sidebar.radio("Tipo:", ["Despesa", "Receita"], horizontal=True)

with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data = st.date_input("Data", datetime.now())
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoria", categorias_dict[tipo])
    descricao = st.text_input("Descrição")
    
    if st.form_submit_button("Salvar"):
        if valor > 0:
            ws.append_row([data.strftime("%d/%m/%Y"), valor, categoria, tipo, descricao])
            st.sidebar.success("✅ Salvo!")
            st.cache_data.clear()
            st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    lista_dados = ws.get_all_values()
    if len(lista_dados) > 1:
        df = pd.DataFrame(lista_dados[1:], columns=lista_dados[0])
        df.columns = [c.strip() for c in df.columns]
        
        # Converte tipos de dados
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')
        
        # 4. GRÁFICO COMPARATIVO
        st.subheader("📊 Comparativo Mensal: Receitas vs Despesas")
        
        # Agrupa por Mês/Ano e Tipo
        resumo_mensal = df.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
        
        fig = go.Figure()
        if 'Receita' in resumo_mensal.columns:
            fig.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Receita'], name='Receitas', marker_color='#28a745'))
        if 'Despesa' in resumo_mensal.columns:
            fig.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Despesa'], name='Despesas', marker_color='#dc3545'))

        fig.update_layout(barmode='group', height=400, margin=dict(l=20, r=20, t=20, b=20))
        st.plotly_chart(fig, use_container_width=True)

        # Histórico
        st.markdown("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df.tail(10), use_container_width=True)
        
    else:
        st.info("Faça seu primeiro lançamento na barra lateral!")
except Exception as e:
    st.error(f"Erro ao processar gráfico: {e}")
