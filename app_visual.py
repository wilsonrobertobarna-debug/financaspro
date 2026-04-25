import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# Estilo para botões e métricas
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO BÁSICA
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

# 3. LÓGICA DO APP
client = conectar_google()
PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
sh = client.open_by_key(PLANILHA_ID)
ws = sh.get_worksheet(0)

# --- BARRA LATERAL: FORMULÁRIO DE LANÇAMENTO ---
st.sidebar.header("📝 Novo Lançamento")
with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data = st.date_input("Data", datetime.now())
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
    categoria = st.selectbox("Categoria", ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Outros"])
    descricao = st.text_input("Descrição / Detalhes")
    
    submit = st.form_submit_button("Salvar na Planilha")

    if submit:
        if valor > 0:
            nova_linha = [data.strftime("%d/%m/%Y"), valor, categoria, descricao]
            ws.append_row(nova_linha)
            st.sidebar.success("✅ Gravado com sucesso!")
            # Limpa o cache para mostrar o novo dado na tabela
            st.cache_data.clear()
        else:
            st.sidebar.warning("Por favor, insira um valor maior que zero.")

# --- ÁREA PRINCIPAL: VISUALIZAÇÃO ---
st.title("🛡️ FinançasPro Wilson")

try:
    dados = ws.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        
        # Totais rápidos
        total = df['Valor'].sum() if 'Valor' in df.columns else 0
        col1, col2 = st.columns(2)
        col1.metric("Gasto Total", f"R$ {total:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
        col2.metric("Lançamentos", len(df))

        st.markdown("---")
        st.subheader("📊 Histórico Recente")
        st.dataframe(df.tail(15), use_container_width=True)
    else:
        st.info("Nenhum dado encontrado. Use o formulário ao lado para começar!")

except Exception as e:
    st.error(f"Erro ao ler dados: {e}")
