import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 10px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO GERAL
@st.cache_data(ttl=60)
def carregar_aba(nome_aba):
    try:
        ws = sh.worksheet(nome_aba)
        dados = ws.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# --- LÓGICA DA ABA FINANÇAS (MANTIDA) ---
if aba == "💰 Finanças":
    df_bancos_cad = carregar_aba("Bancos")
    df_cats_cad = carregar_aba("Categoria")
    df_base = carregar_aba(sh.get_worksheet(0).title)
    
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    # ... (Cálculos e Gráficos de Finanças permanecem aqui)

# --- ABA MILO & BOLT (RESTAURADA) ---
elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Controle: Milo & Bolt</h1>", unsafe_allow_html=True)
    
    df_p = carregar_aba("Controle_Pets")
    
    if not df_p.empty:
        # Mostra o histórico completo primeiro, como estava antes
        st.subheader("📋 Histórico de Registros")
        st.dataframe(df_p.iloc[::-1], use_container_width=True)
        
        st.write("---")
        st.subheader("📊 Resumo de Cuidados")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🐶 **Último registro:** {df_p.iloc[-1][0]} - {df_p.iloc[-1][2]}")
    else:
        st.warning("Nenhum dado encontrado na aba Controle_Pets.")

    # Formulário lateral para novos registros
    with st.sidebar.form("f_pet"):
        st.write("### 🐾 Novo Registro")
        p_dat = st.date_input("Data", datetime.now())
        p_pet = st.selectbox("Pet", ["Milo", "Bolt", "Ambos"])
        p_tipo = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Veterinário", "Outros"])
        p_obs = st.text_input("Observação")
        if st.form_submit_button("SALVAR"):
            sh.worksheet("Controle_Pets").append_row([p_dat.strftime("%d/%m/%Y"), p_pet, p_tipo, p_obs])
            st.cache_data.clear(); st.rerun()

# --- ABA MEU VEÍCULO (RESTAURADA) ---
else:
    st.markdown("<h1 style='text-align: center;'>🚗 Manutenção e Veículo</h1>", unsafe_allow_html=True)
    
    df_v = carregar_aba("Controle_Veiculo")
    
    if not df_v.empty:
        # Mostra a tabela de manutenção completa
        st.subheader("📋 Histórico do Veículo")
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
        
        st.write("---")
        ultima_km = df_v.iloc[-1][2] if 'KM' in df_v.columns or len(df_v.columns) > 2 else "Não informada"
        st.success(f"📍 **KM Atual Registrada:** {ultima_km}")
    else:
        st.warning("Nenhum dado encontrado na aba Controle_Veiculo.")

    # Formulário lateral para veículo
    with st.sidebar.form("f_veic"):
        st.write("### 🚗 Novo Registro")
        v_dat = st.date_input("Data", datetime.now())
        v_tipo = st.selectbox("Tipo", ["Combustível", "Troca de Óleo", "Pneus", "Revisão", "Outros"])
        v_km = st.text_input("KM Atual")
        v_val = st.text_input("Valor (R$)")
        if st.form_submit_button("SALVAR"):
            sh.worksheet("Controle_Veiculo").append_row([v_dat.strftime("%d/%m/%Y"), v_tipo, v_km, v_val])
            st.cache_data.clear(); st.rerun()
