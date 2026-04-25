import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO (Tags organizadas e visual limpo)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.5rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.8rem !important; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #28a745; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
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

# 3. INTERFACE DE NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS (DASHBOARD COMPLETO)
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.title("🛡️ FinançasPro - Central Wilson")
    
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Identificação de Colunas
        c_tipo = 'Tipo' if 'Tipo' in df.columns else (df.columns[3] if len(df.columns) > 3 else 'Tipo')
        c_cat = 'Categoria' if 'Categoria' in df.columns else (df.columns[2] if len(df.columns) > 2 else 'Categoria')
        c_bnc = 'Banco' if 'Banco' in df.columns else (df.columns[4] if len(df.columns) > 4 else 'Banco')
        c_status = 'Status' if 'Status' in df.columns else (df.columns[5] if len(df.columns) > 5 else 'Status')

        # Cálculos com Padronização
        df[c_tipo] = df[c_tipo].astype(str).str.strip().str.capitalize()
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum()
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum()
        rend = df[df[c_cat].astype(str).str.contains('Rendimento', case=False)]['Valor_Num'].sum()
        
        # Cálculo de Economia %
        eco_perc = ((rec - desp) / rec * 100) if rec > 0 else 0
        
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- TAGS (METRICS) ---
        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("🟢 Receitas", f_brl(rec))
        t2.metric("🔴 Despesas", f_brl(desp))
        t3.metric("💎 Saldo", f_brl(rec - desp))
        t4.metric("📈 Rendimentos", f_brl(rend))
        t5.metric("💡 Economia %", f"{eco_perc:.1f}%")

        st.write("---")
        
        # --- GRÁFICOS ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📊 Receitas x Despesas Mensal")
            try:
                df_m = df.copy()
                df_m['Data_DT'] = pd.to_datetime(df_m['Data'], dayfirst=True, errors='coerce')
                df_m = df_m.dropna(subset=['Data_DT'])
                df_m['Mes'] = df_m['Data_DT'].dt.strftime('%m/%y')
                comp = df_m.groupby(['Mes', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
                st.bar_chart(comp, color=['#dc3545', '#28a745']) # Vermelho e Verde
            except: st.info("Aguardando dados de data válidos...")

        with col_g2:
            st.subheader("🏦 Gastos por Banco")
            gastos_banco = df[df[c_tipo] == 'Despesa'].groupby(c_bnc)['Valor_Num'].sum()
            st.bar_chart(gastos_banco, color='#6c757d')

        st.write("---")
        st.subheader("🍕 Gastos por Categoria")
        gastos_cat = df[df[c_tipo] == 'Despesa'].groupby(c_cat)['Valor_Num'].sum()
        st.bar_chart(gastos_cat, color='#ffc107')

    # FORMULÁRIO LATERAL
    with st.sidebar.form("f_fin", clear_on_submit=True):
        st.subheader("📝 Lançamento")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
        f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"])
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
            st.cache_data.clear(); st.rerun()

# ABA 2 (Pets) e ABA 3 (Veículo) mantidas conforme o funcionamento anterior...
