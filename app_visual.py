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

# 3. CARREGAMENTO DE CADASTROS
@st.cache_data(ttl=60)
def carregar_cadastros():
    try:
        ws_b = sh.worksheet("Bancos")
        df_b = pd.DataFrame(ws_b.get_all_records())
    except:
        df_b = pd.DataFrame(columns=['Nome do Banco', 'Saldo Inicial', 'Tipo de Conta'])
    
    try:
        ws_c = sh.worksheet("Categoria")
        df_c = pd.DataFrame(ws_c.get_all_records())
        if 'Meta' in df_c.columns:
            df_c['Meta'] = pd.to_numeric(df_c['Meta'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        else:
            df_c['Meta'] = 0
    except:
        df_c = pd.DataFrame(columns=['Nome', 'Meta'])
    
    try:
        ws_ct = sh.worksheet("Cartoes")
        df_ct = pd.DataFrame(ws_ct.get_all_records())
    except:
        df_ct = pd.DataFrame(columns=['Nome do Cartão', 'Limite'])
        
    return df_b, df_c, df_ct

df_bancos_cad, df_cats_cad, df_cartoes_cad = carregar_cadastros()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        df_base['Valor_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_foco = datetime.now().strftime('%m/%y')

        # Filtro de Banco
        bancos_lista = ["Todos"] + sorted(df_bancos_cad['Nome do Banco'].unique().tolist()) if not df_bancos_cad.empty else ["Todos"]
        banco_sel = st.selectbox("🔍 Selecione o Banco:", bancos_lista)
        df_filtrado = df_base[df_base[c_bnc] == banco_sel].copy() if banco_sel != "Todos" else df_base.copy()

        # Cálculo de Saldo
        s_ini = pd.to_numeric(df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if banco_sel != "Todos" else pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()
        rec = df_filtrado[df_filtrado[c_tip] == 'Receita']['Valor_Num'].sum()
        desp = df_filtrado[df_filtrado[c_tip] == 'Despesa']['Valor_Num'].sum()
        saldo_exibir = s_ini + rec - desp

        st.markdown(f'<div class="saldo-container"><small>Saldo Atual em {banco_sel}</small><h2>R$ {saldo_exibir:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # GRÁFICOS
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📊 Metas vs Gasto ({mes_foco})")
            df_gasto_mes = df_base[(df_base['Mes_Ano'] == mes_foco) & (df_base[c_tip] == 'Despesa')]
            gasto_por_cat = df_gasto_mes.groupby(c_cat)['Valor_Num'].sum().reset_index()
            df_metas = pd.merge(df_cats_cad[['Nome', 'Meta']], gasto_por_cat, left_on='Nome', right_on=c_cat, how='left').fillna(0)
            df_metas = df_metas.rename(columns={'Nome': 'Categoria', 'Meta': 'Meta Planejada', 'Valor_Num': 'Gasto Real'}).set_index('Categoria')
            df_metas = df_metas[['Meta Planejada', 'Gasto Real']]
            st.bar_chart(df_metas, color=['#007bff', '#ff4b4b'], horizontal=True)

        with col2:
            st.subheader("🏦 Despesa por Banco/Cartão")
            uso_banco = df_base[df_base[c_tip] == 'Despesa'].groupby(c_bnc)['Valor_Num'].sum()
            st.bar_chart(uso_banco, color='#28a745')

        st.subheader("📋 Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    with st.sidebar.form("f_add"):
        st.write("### ➕ Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Origem", sorted(df_bancos_cad['Nome do Banco'].tolist() + df_cartoes_cad['Nome do Cartão'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    df_p = pd.DataFrame(ws_p.get_all_values()[1:], columns=ws_p.get_all_values()[0])
    st.dataframe(df_p.iloc[::-1], use_container_width=True)
    with st.sidebar.form("f_pet"):
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_obs = st.text_input("Obs")
        p_val = st.number_input("Custo", min_value=0.0)
        if st.form_submit_button("Salvar Pet"):
            ws_p.append_row([p_dat.strftime("%d/%m/%Y"), p_obs, str(p_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    df_v = pd.DataFrame(ws_v.get_all_values()[1:], columns=ws_v.get_all_values()[0])
    st.dataframe(df_v.iloc[::-1], use_container_width=True)
    with st.sidebar.form("f_car"):
        v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        v_km = st.number_input("KM", min_value=0)
        v_obs = st.text_input("Obs")
        if st.form_submit_button("Salvar Veículo"):
            ws_v.append_row([v_dat.strftime("%d/%m/%Y"), str(v_km), v_obs, "0"])
            st.cache_data.clear(); st.rerun()
