import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 0.9rem; }
    .receita { background-color: #28a745; }
    .despesa { background-color: #dc3545; }
    .rendimento { background-color: #17a2b8; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
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

# 3. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws_finance = sh.get_worksheet(0) # Pega sempre a primeira aba
    LISTA_CAT = ["Mercado", "Shopee", "Mercado Livre", "AserNet", "Skyfit", "Farmácia", "Combustível", "Milo/Bolt", "Lazer", "Outros"]
    
    st.sidebar.header("📝 Novo Lançamento")
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY") 
        f_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_cat = st.selectbox("Categoria", LISTA_CAT)
        f_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Rendimento", "Pendência"])
        f_banco = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
        f_status = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("🚀 SALVAR"):
            dt_br = f_data.strftime("%d/%m/%Y")
            ws_finance.append_row([dt_br, f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    # EXIBIÇÃO... (Simplificada para o código não ficar gigante)
    dados = ws_finance.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"])
        st.title("🛡️ FinançasPro - Central")
        st.dataframe(df.iloc[::-1].head(10), use_container_width=True)

# ==========================================
# ABA 2: MILO & BOLT (CÓDIGO ANTI-ERRO)
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Cuidados: Milo & Bolt")
    
    # Busca inteligente pela aba
    todas_abas = [w.title for w in sh.worksheets()]
    nome_alvo = "Controle_Pets"
    
    if nome_alvo in todas_abas:
        ws_p = sh.worksheet(nome_alvo)
        
        st.sidebar.header("📝 Registro Pet")
        with st.sidebar.form("form_p", clear_on_submit=True):
            p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
            p_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            p_tipo = st.selectbox("O quê?", ["Ração", "Vacina", "Vermífugo", "Banho", "Saúde"])
            p_valor = st.number_input("Valor (R$)", min_value=0.0)
            p_det = st.text_input("Detalhes")
            
            if st.form_submit_button("🦴 SALVAR"):
                dt_br = p_data.strftime("%d/%m/%Y")
                ws_p.append_row([dt_br, p_pet, p_tipo, p_det, p_valor])
                # Lança no financeiro também (primeira aba)
                sh.get_worksheet(0).append_row([dt_br, p_valor, f"Pet: {p_tipo}", "Despesa", "Nubank", "Pago"])
                st.cache_data.clear(); st.rerun()

        dp_list = ws_p.get_all_values()
        if len(dp_list) > 1:
            dp = pd.DataFrame(dp_list[1:], columns=dp_list[0])
            st.dataframe(dp.iloc[::-1], use_container_width=True)
    else:
        st.error(f"⚠️ Erro: Não encontrei a aba '{nome_alvo}'")
        st.info(f"As abas que encontrei foram: {todas_abas}")
        st.warning("Dica: Verifique se não há um espaço sobrando no nome da aba na sua planilha.")

# ==========================================
# ABA 3: VEÍCULO
# ==========================================
else:
    st.title("🚗 Meu Veículo")
    st.info("Ajustando Pets primeiro...")
