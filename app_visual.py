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
        background-color: #007bff; color: white; padding: 10px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2rem; }
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

# 3. CARREGAMENTO DE DADOS (CADASTROS + LANÇAMENTOS)
@st.cache_data(ttl=60)
def carregar_tudo():
    # Bancos
    try: df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    except: df_b = pd.DataFrame(columns=['Nome do Banco', 'Saldo Inicial'])
    # Categorias
    try: 
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        if 'Meta' in df_c.columns:
            df_c['Meta'] = pd.to_numeric(df_c['Meta'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        else: df_c['Meta'] = 0
    except: df_c = pd.DataFrame(columns=['Nome', 'Meta'])
    # Cartões
    try: df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
    except: df_ct = pd.DataFrame(columns=['Nome do Cartão'])
    # Lançamentos Principais
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
    return df_b, df_c, df_ct, df_base

df_bancos_cad, df_cats_cad, df_cartoes_cad, df_base = carregar_tudo()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS (DASHBOARD COMPLETO)
# ==========================================
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Padronização de Colunas
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        # Conversões
        df_base['Valor_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # 1. DASHBOARD DE SALDO
        s_ini = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()
        rec_t = df_base[df_base[c_tip].str.contains('Receita', case=False, na=False)]['Valor_Num'].sum()
        desp_t = df_base[df_base[c_tip].str.contains('Despesa', case=False, na=False)]['Valor_Num'].sum()
        saldo_geral = s_ini + rec_t - desp_t

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Consolidado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # 2. GRÁFICOS LADO A LADO
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📊 Metas vs Real ({mes_atual})")
            df_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base[c_tip].str.contains('Despesa', case=False, na=False))]
            gasto_cat = df_mes.groupby(c_cat)['Valor_Num'].sum().reset_index()
            df_meta_comp = pd.merge(df_cats_cad[['Nome', 'Meta']], gasto_cat, left_on='Nome', right_on=c_cat, how='left').fillna(0)
            df_meta_comp = df_meta_comp.rename(columns={'Nome': 'Categoria', 'Meta': 'Meta', 'Valor_Num': 'Gasto'}).set_index('Categoria')[['Meta', 'Gasto']]
            st.bar_chart(df_meta_comp, horizontal=True, color=['#007bff', '#ff4b4b'])
            st.caption("🔵 Azul: Meta | 🔴 Vermelho: Gasto Real")

        with col2:
            st.subheader("📈 Evolução Mensal")
            df_evol = df_base.groupby(['Mes_Ano', c_tip])['Valor_Num'].sum().unstack().fillna(0)
            st.line_chart(df_evol)

        st.write("---")
        st.subheader("🏦 Despesas por Banco/Origem")
        desp_banco = df_base[df_base[c_tip].str.contains('Despesa', case=False, na=False)].groupby(c_bnc)['Valor_Num'].sum()
        st.bar_chart(desp_banco, color='#28a745')

        # 3. TABELA DE HISTÓRICO
        st.subheader("📋 Histórico Completo")
        st.dataframe(df_base.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # SIDEBAR: LANÇAMENTO
    with st.sidebar.form("f_novo"):
        st.write("### ➕ Novo Lançamento")
        f_d = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_v = st.number_input("Valor", min_value=0.0)
        f_t = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_c = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        bancos = df_bancos_cad['Nome do Banco'].tolist() if not df_bancos_cad.empty else []
        cartoes = df_cartoes_cad['Nome do Cartão'].tolist() if not df_cartoes_cad.empty else []
        f_b = st.selectbox("Banco/Origem", sorted(bancos + cartoes + ["Dinheiro"]))
        f_s = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR"):
            sh.get_worksheet(0).append_row([f_d.strftime("%d/%m/%Y"), str(f_v).replace('.', ','), f_c, f_t, f_b, f_s])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    dados_p = ws_p.get_all_values()
    if len(dados_p) > 1:
        df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0])
        st.dataframe(df_p.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_pet"):
        st.write("### ➕ Gasto com Pets")
        p_d = st.date_input("Data", datetime.now())
        p_o = st.text_input("Descrição/Obs")
        p_v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar Pet"):
            ws_p.append_row([p_d.strftime("%d/%m/%Y"), p_o, str(p_v).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    dados_v = ws_v.get_all_values()
    if len(dados_v) > 1:
        df_v = pd.DataFrame(dados_v[1:], columns=dados_v[0])
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_car"):
        st.write("### ➕ Manutenção/KM")
        v_d = st.date_input("Data", datetime.now())
        v_k = st.number_input("Kilometragem", min_value=0)
        v_o = st.text_input("O que foi feito?")
        if st.form_submit_button("Salvar Veículo"):
            ws_v.append_row([v_d.strftime("%d/%m/%Y"), str(v_k), v_o, "0"])
            st.cache_data.clear(); st.rerun()
