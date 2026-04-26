import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
ws = sh.get_worksheet(0) # Planilha Principal

# Carregar dados globais para todas as abas
dados_brutos = ws.get_all_values()
df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
df_base.columns = [c.strip() for c in df_base.columns]
c_tipo, c_cat, c_stat, c_bnc = df_base.columns[3], df_base.columns[2], df_base.columns[5], df_base.columns[4]

# 3. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS (Dashboard Geral)
# ==========================================
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🛡️ FinançasPro Wilson</h1><p style='text-align: center; font-size: 1.5rem; margin-top: -10px;'>🐾<br>🐾</p>", unsafe_allow_html=True)
    
    bancos_lista = ["Todos"] + sorted(list(df_base[c_bnc].unique()))
    banco_filtro = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
    df = df_base[df_base[c_bnc] == banco_filtro].copy() if banco_filtro != "Todos" else df_base.copy()

    df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    
    rec = df[df[c_tipo].str.contains('Receita', case=False, na=False)]['Valor_Num'].sum()
    desp = df[df[c_tipo].str.contains('Despesa', case=False, na=False)]['Valor_Num'].sum()
    rend = df[df[c_cat].str.contains('Rendimento', case=False, na=False)]['Valor_Num'].sum()
    saldo = rec - desp
    def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    st.markdown(f'<div class="saldo-container"><small>Saldo em: {banco_filtro}</small><h2>{f_brl(saldo)}</h2></div>', unsafe_allow_html=True)
    t1, t2, t3 = st.columns(3)
    t1.metric("🟢 Receitas", f_brl(rec)); t2.metric("🔴 Despesas", f_brl(desp)); t3.metric("📈 Rendimentos", f_brl(rend))

    st.subheader("📋 Histórico Geral")
    df_visual = df.copy(); df_visual.index = df.index + 2
    st.dataframe(df_visual.iloc[::-1], use_container_width=True)

# ==========================================
# ABA 2: MILO & BOLT (Filtro Automático)
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    df_pets = df_base[df_base[c_cat].str.contains('Milo|Bolt', case=False, na=False)].copy()
    if not df_pets.empty:
        df_pets.index = df_pets.index + 2
        st.dataframe(df_pets.iloc[::-1], use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado para os pets na planilha principal.")

# ==========================================
# ABA 3: MEU VEÍCULO (Filtro Automático)
# ==========================================
else:
    st.title("🚗 Controle: Veículo")
    df_veic = df_base[df_base[c_cat].str.contains('Veículo|Combustível', case=False, na=False)].copy()
    if not df_veic.empty:
        df_veic.index = df_veic.index + 2
        st.dataframe(df_veic.iloc[::-1], use_container_width=True)
    else:
        st.info("Nenhum lançamento de veículo encontrado.")

# --- MENU LATERAL PARA LANÇAMENTOS ---
st.sidebar.write("---")
acao = st.sidebar.selectbox("Ação:", ["Novo Lançamento", "Editar/Excluir"])
if acao == "Novo Lançamento":
    with st.sidebar.form("f_novo"):
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_cat = st.selectbox("Categoria", ["Mercado", "Milo/Bolt", "Veículo: Abastecimento", "Combustível", "Skyfit", "Outros"])
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro"])
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
            st.cache_data.clear(); st.rerun()
