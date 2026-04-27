import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro", page_icon="🛡️", layout="wide")

# Estilos CSS
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .resumo-card { padding: 8px; border-radius: 8px; text-align: center; border: 1px solid #ddd; background-color: #f8f9fa; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar():
    try:
        info = st.secrets["connections"]["gsheets"]
        key = info["private_key"].replace("\\n", "\n").strip()
        creds = Credentials.from_service_account_info({
            "type": info["type"], "project_id": info["project_id"],
            "private_key_id": info["private_key_id"], "private_key": key,
            "client_email": info["client_email"], "token_uri": info["token_uri"],
        }, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. FUNÇÕES DE APOIO
def limpar_v(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

@st.cache_data(ttl=60)
def carregar_dados():
    ws_l = sh.get_worksheet(0)
    dados_l = ws_l.get_all_values()
    df_l = pd.DataFrame(dados_l[1:], columns=dados_l[0]) if len(dados_l) > 1 else pd.DataFrame()
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    return df_b, df_c, df_l

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

# --- AJUSTE DE DATA BRASIL ---
fuso_br = timezone(timedelta(hours=-3))
hoje_br = datetime.now(fuso_br)

# 4. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Menu:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]
        df_base['V_Num'] = df_base[c_val].apply(limpar_v)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        
        # Pega o mês mais recente que existe na planilha (Resolve o erro do gráfico sumir)
        mes_atual = df_base.sort_values('DT', ascending=False)['Mes_Ano'].iloc[0]

        # Filtros e Cálculos
        bancos_lista = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Saldo
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_v).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_v).sum()
        df_pago = df_filtrado[df_filtrado[c_sta] == 'Pago']
        saldo_atual = s_ini + df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()

        st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # Gráficos e Métricas
        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"🏦 Bancos ({mes_atual})")
            s_pizza = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar_v).sum()
                re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                s_pizza.append({'Banco': b, 'Saldo': si + re - de})
            fig_p = px.pie(pd.DataFrame(s_pizza), values='Saldo', names='Banco', hole=.4, height=350)
            st.plotly_chart(fig_p, use_container_width=True)

        with col2:
            st.subheader("📊 Últimos Lançamentos")
            st.dataframe(df_filtrado.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1].head(10), use_container_width=True)

    # FORMULÁRIO LATERAL
    with st.sidebar.form("novo"):
        st.write("### 🚀 Lançar")
        # DATA FORÇADA BRASIL
        f_dat = st.date_input("Data", hoje_br)
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("SALVAR"):
            sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()
