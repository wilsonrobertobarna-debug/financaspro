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
        background-color: #007bff; color: white; padding: 10px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2rem; }
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

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=60)
def carregar_tudo():
    # Carrega Cadastros
    try: df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    except: df_b = pd.DataFrame(columns=['Nome do Banco', 'Saldo Inicial'])
    
    try: 
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        if 'Meta' in df_c.columns:
            df_c['Meta'] = pd.to_numeric(df_c['Meta'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
    except: df_c = pd.DataFrame(columns=['Nome', 'Meta'])
    
    try: df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
    except: df_ct = pd.DataFrame(columns=['Nome do Cartão'])

    # Carrega Lançamentos
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
    
    return df_b, df_c, df_ct, df_base

df_bancos_cad, df_cats_cad, df_cartoes_cad, df_base = carregar_tudo()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Tratamento de colunas
        c_dat, c_val, c_cat, c_tip, c_bnc = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4]
        df_base['Valor_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_foco = datetime.now().strftime('%m/%y')

        # Dashboard de Saldo
        s_ini = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()
        saldo_geral = s_ini + df_base[df_base[c_tip] == 'Receita']['Valor_Num'].sum() - df_base[df_base[c_tip] == 'Despesa']['Valor_Num'].sum()
        st.markdown(f'<div class="saldo-container"><small>Saldo Geral</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # GRÁFICOS
        st.write("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader(f"📊 Metas vs Gasto ({mes_foco})")
            df_mes = df_base[(df_base['Mes_Ano'] == mes_foco) & (df_base[c_tip] == 'Despesa')]
            g_cat = df_mes.groupby(c_cat)['Valor_Num'].sum().reset_index()
            df_comp = pd.merge(df_cats_cad[['Nome', 'Meta']], g_cat, left_on='Nome', right_on=c_cat, how='left').fillna(0)
            df_comp = df_comp.rename(columns={'Nome': 'Categoria', 'Meta': 'Meta', 'Valor_Num': 'Real'}).set_index('Categoria')[['Meta', 'Real']]
            st.bar_chart(df_comp, horizontal=True, color=['#007bff', '#ff4b4b'])

        with g2:
            st.subheader("📉 Receita x Despesa")
            g_evol = df_base.groupby(['Mes_Ano', c_tip])['Valor_Num'].sum().unstack().fillna(0)
            st.line_chart(g_evol)

        st.subheader("🏦 Uso por Banco")
        st.bar_chart(df_base[df_base[c_tip] == 'Despesa'].groupby(c_bnc)['Valor_Num'].sum(), color='#28a745')

        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_base.iloc[::-1].head(10), use_container_width=True)

    # Sidebar Form
    with st.sidebar.form("add"):
        st.write("### ➕ Novo")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        f_bnc = st.selectbox("Origem", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        if st.form_submit_button("SALVAR"):
            sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    df_p = pd.DataFrame(ws_p.get_all_values()[1:], columns=ws_p.get_all_values()[0])
    st.dataframe(df_p.iloc[::-1], use_container_width=True)
    with st.sidebar.form("p"):
        p_d = st.date_input("Data")
        p_o = st.text_input("Obs")
        p_v = st.number_input("Valor")
        if st.form_submit_button("Salvar"):
            ws_p.append_row([p_d.strftime("%d/%m/%Y"), p_o, str(p_v).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    df_v = pd.DataFrame(ws_v.get_all_values()[1:], columns=ws_v.get_all_values()[0])
    st.dataframe(df_v.iloc[::-1], use_container_width=True)
    with st.sidebar.form("v"):
        v_d = st.date_input("Data")
        v_k = st.number_input("KM")
        v_o = st.text_input("Obs")
        if st.form_submit_button("Salvar"):
            ws_v.append_row([v_d.strftime("%d/%m/%Y"), str(v_k), v_o, "0"])
            st.cache_data.clear(); st.rerun()
