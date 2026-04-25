import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 8px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px; line-height: 1.1;
    }
    .saldo-container h2 { margin: 0; font-size: 1.8rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .economia-texto { color: #007bff; font-size: 1.1rem; font-weight: bold; text-align: center; margin-bottom: 25px; }
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

# 3. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🛡️ FinançasPro Wilson</h1><p style='text-align: center; font-size: 1.5rem; margin-top: -10px;'>🐾<br>🐾</p>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        mes_atual = datetime.now().strftime('%m/%y')
        
        c_tipo = 'Tipo' if 'Tipo' in df.columns else df.columns[3]
        c_cat = 'Categoria' if 'Categoria' in df.columns else df.columns[2]
        c_stat = 'Status' if 'Status' in df.columns else df.columns[5]
        c_bnc = 'Banco' if 'Banco' in df.columns else df.columns[4]

        # Dashboard e Histórico (omitidos aqui por brevidade, manter igual ao anterior)
        # ... (Cálculos de rec, desp, saldo, etc)
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual</small><h2>{f_brl(rec - desp)}</h2></div>', unsafe_allow_html=True)
        st.subheader("📋 Histórico")
        df_visual = df.copy()
        df_visual.index = df_visual.index + 2
        st.dataframe(df_visual.iloc[::-1], use_container_width=True)

    # MENU LATERAL FINANÇAS
    menu_acao = st.sidebar.selectbox("Ação Financeira:", ["Novo Lançamento", "Editar/Excluir"])
    if menu_acao == "Novo Lançamento":
        with st.sidebar.form("f_novo"):
            st.subheader("📝 Novo")
            f_dat = st.date_input("Data", datetime.now())
            f_val = st.number_input("Valor", min_value=0.0)
            f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
            f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
            f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"])
            f_stat = st.selectbox("Status", ["Pago", "Pendente"])
            if st.form_submit_button("🚀 SALVAR"):
                ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
                st.cache_data.clear(); st.rerun()
    # ... (Bloco Editar/Excluir continua igual)

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    
    # Formulário de Lançamento para Pets
    with st.sidebar.form("f_pets"):
        st.subheader("🐾 Novo Registro Pet")
        p_dat = st.date_input("Data", datetime.now())
        p_obs = st.text_input("O que aconteceu? (Banho, Vacina, Ração...)")
        p_val = st.number_input("Custo (se houver)", min_value=0.0)
        if st.form_submit_button("🚀 SALVAR NO PET"):
            ws_p.append_row([p_dat.strftime("%d/%m/%Y"), p_obs, str(p_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

    dados_p = ws_p.get_all_values()
    if len(dados_p) > 1:
        st.dataframe(pd.DataFrame(dados_p[1:], columns=dados_p[0]).iloc[::-1], use_container_width=True)

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Controle: Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")

    # Formulário de Lançamento para Veículo
    with st.sidebar.form("f_veiculo"):
        st.subheader("🚗 Novo Registro Veículo")
        v_dat = st.date_input("Data", datetime.now())
        v_km = st.number_input("KM Atual", min_value=0)
        v_obs = st.text_input("Manutenção/Abastecimento")
        v_val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("🚀 SALVAR NO VEÍCULO"):
            ws_v.append_row([v_dat.strftime("%d/%m/%Y"), str(v_km), v_obs, str(v_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

    dados_v = ws_v.get_all_values()
    if len(dados_v) > 1:
        st.dataframe(pd.DataFrame(dados_v[1:], columns=dados_v[0]).iloc[::-1], use_container_width=True)
