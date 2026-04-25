import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO (Recuperando o visual das Tags)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; color: #1e1e1e; }
    [data-testid="stMetricLabel"] { font-size: 0.9rem !important; font-weight: bold; color: #555; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; border: 1px solid #e0e0e0; box-shadow: 2px 2px 8px rgba(0,0,0,0.05); }
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; background-color: #28a745; color: white; font-weight: bold; border: none; }
    .stButton>button:hover { background-color: #218838; border: none; }
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

# --- FUNÇÃO DE TABELA ---
def exibir_tabela(aba_sheet, titulo):
    dados = aba_sheet.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        st.subheader(f"📋 {titulo}")
        st.dataframe(df.iloc[::-1], use_container_width=True)

# 3. NAVEGAÇÃO LATERAL (TRAZENDO OS BOTÕES DE VOLTA)
st.sidebar.markdown("# 🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

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
        
        # Mapeamento Inteligente de Colunas
        c_tipo = 'Tipo' if 'Tipo' in df.columns else (df.columns[3] if len(df.columns) > 3 else 'Tipo')
        c_cat = 'Categoria' if 'Categoria' in df.columns else (df.columns[2] if len(df.columns) > 2 else 'Categoria')
        c_banco = 'Banco' if 'Banco' in df.columns else (df.columns[4] if len(df.columns) > 4 else 'Banco')
        c_status = 'Status' if 'Status' in df.columns else (df.columns[5] if len(df.columns) > 5 else 'Status')

        # Padronização e Cálculos
        df[c_tipo] = df[c_tipo].astype(str).str.strip().str.capitalize()
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum()
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum()
        pend = df[df[c_status].astype(str).str.contains('Pendente', case=False)]['Valor_Num'].sum()

        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # EXIBIÇÃO DAS TAGS (METRICS)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🟢 Receitas", f_brl(rec))
        m2.metric("🔴 Despesas", f_brl(desp))
        m3.metric("💎 Saldo", f_brl(rec - desp))
        m4.metric("⏳ Pendente", f_brl(pend))

        st.write("---")
        
        # GRÁFICOS LADO A LADO
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("📊 Receitas x Despesas")
            try:
                df_g = df.copy()
                df_g['Data_DT'] = pd.to_datetime(df_g['Data'], dayfirst=True, errors='coerce')
                df_g['Mes'] = df_g['Data_DT'].dt.strftime('%m/%y')
                comp = df_g.groupby(['Mes', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
                st.bar_chart(comp, color=['#dc3545', '#28a745']) # Vermelho/Verde
            except: st.info("Sem dados para o gráfico mensal.")

        with g2:
            st.subheader("🏦 Gastos por Banco")
            df_banco = df[df[c_tipo] == 'Despesa'].groupby(c_banco)['Valor_Num'].sum()
            if not df_banco.empty:
                st.bar_chart(df_banco, color='#6c757d')
            else: st.info("Lance despesas com banco para ver aqui.")

    # Formulário de Cadastro
    with st.sidebar.form("f_fin", clear_on_submit=True):
        st.subheader("📝 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor (R$)", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Shopee", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
        f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outro"])
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR AGORA"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
            st.cache_data.clear(); st.rerun()

    exibir_tabela(ws, "Histórico Financeiro")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    ws_p = sh.worksheet("Controle_Pets")
    st.title("🐾 Cuidados: Milo & Bolt")
    with st.sidebar.form("f_pet", clear_on_submit=True):
        p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
        p_dat = st.date_input("Data", datetime.now())
        p_tip = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Saúde"])
        p_val = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("🦴 SALVAR PET"):
            ws_p.append_row([p_dat.strftime("%d/%m/%Y"), p_pet, p_tip, "App", str(p_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()
    exibir_tabela(ws_p, "Histórico dos Pets")

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    ws_v = sh.worksheet("Controle_Veiculo")
    st.title("🚗 Controle do Veículo")
    with st.sidebar.form("f_vei", clear_on_submit=True):
        v_dat = st.date_input("Data", datetime.now())
        v_tip = st.selectbox("Serviço", ["Abastecimento", "Manutenção", "Lavagem"])
        v_km = st.number_input("KM Atual", min_value=0)
        v_val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("🚗 SALVAR VEÍCULO"):
            ws_v.append_row([v_dat.strftime("%d/%m/%Y"), v_tip, "App", str(v_km), str(v_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()
    exibir_tabela(ws_v, "Histórico do Veículo")
