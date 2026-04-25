import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA (Identidade FinançasPro)
st.set_page_config(
    page_title="FinançasPro Wilson", 
    layout="wide", 
    page_icon="🛡️"
)

# Estilo Minimalista (CSS customizado)
st.markdown("""
    <style>
    .main { background-color: #f5f5f5; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO AUTOMÁTICA VIA SECRETS
@st.cache_resource(show_spinner="Acessando base de dados...")
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        # Limpa a chave para evitar o erro PEM 95
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
        st.error(f"Erro na conexão segura: {e}")
        st.stop()

# 3. INTERFACE PRINCIPAL
st.title("🛡️ FinançasPro Wilson")
st.subheader("Controle Financeiro Pessoal")

try:
    client = conectar_google()
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0)
    
    # Busca os dados
    dados = ws.get_all_records()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Formatação de Moeda Brasileira (R$)
        # Supondo que sua coluna de valores se chama 'Valor' ou 'Preço'
        if 'Valor' in df.columns:
            total_gasto = df['Valor'].sum()
            
            # Métricas de Destaque
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Lançado", f"R$ {total_gasto:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
            with col2:
                st.metric("Nº de Transações", len(df))
        
        st.markdown("---")
        st.write("### 📋 Últimos Lançamentos")
        st.dataframe(df.tail(20), use_container_width=True)
        
    else:
        st.info("O sistema está conectado, mas a planilha parece estar vazia.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
