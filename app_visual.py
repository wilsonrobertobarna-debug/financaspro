import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 15px;
        border-radius: 12px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
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

# 3. CARGA DE DADOS
@st.cache_data(ttl=60)
def carregar_dados():
    # Bancos e Categorias
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    
    # Lançamentos (Aba Principal)
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    df_l = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
    return df_b, df_c, df_l

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

# 4. TRATAMENTO INICIAL
def limpar(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]
    
    df_base['V_Num'] = df_base[c_val].apply(limpar)
    df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. INTERFACE E FILTROS REATIVOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Menu:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    # FILTRO GLOBAL (O segredo está aqui)
    bancos_lista = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
    banco_sel = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
    
    # Criamos o DataFrame que os gráficos vão usar
    df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

    # CÁLCULOS REATIVOS
    # Saldo Inicial (ajusta se for Todos ou um banco só)
    if banco_sel == "Todos":
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar).sum()
    else:
        s_ini = df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar).sum()

    # Movimentações Reais (Pago)
    df_pago = df_filtrado[df_filtrado[c_sta] == 'Pago']
    entradas = df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
    saidas = df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()
    saldo_atual = s_ini + entradas - saidas

    # Métricas do Mês
    df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
    m_rec = df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum()
    m_des = df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum()
    m_ren = df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum()
    m_pen = df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum()

    # EXIBIÇÃO DASHBOARD
    st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("📈 Receitas", f"R$ {m_rec:,.2f}")
    col2.metric("📉 Despesas", f"R$ {m_des:,.2f}")
    col3.metric("💰 Rendimentos", f"R$ {m_ren:,.2f}")
    col4.metric("⏳ Pendente", f"R$ {m_pen:,.2f}")

    # --- GRÁFICOS DINÂMICOS ---
    st.write("---")
    g1, g2 = st.columns(2)

    with g1:
        if banco_sel == "Todos":
            st.subheader("🏦 Divisão por Banco")
            # Aqui calculamos o saldo individual de cada banco para a pizza
            saldos_pizza = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar).sum()
                re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                saldos_pizza.append({'Banco': b, 'Saldo': si + re - de})
            df_pizza = pd.DataFrame(saldos_pizza)
            fig = px.pie(df_pizza[df_pizza['Saldo']>0], values='Saldo', names='Banco', hole=.4)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.subheader(f"📊 Composição {banco_sel}")
            # Se filtrou um banco, mostra Receita vs Despesa desse banco
            fig = px.pie(names=['Entradas', 'Saídas'], values=[m_rec + m_ren, m_des], hole=.4, 
                         color_discrete_map={'Entradas':'#28a745', 'Saídas':'#dc3545'})
            st.plotly_chart(fig, use_container_width=True)

    with g2:
        st.subheader("📈 Evolução Mensal")
        # Evolução usa SEMPRE o df_filtrado para mudar conforme o banco
        evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
        st.bar_chart(evol)

    st.write("---")
    st.subheader("📋 Lançamentos")
    st.dataframe(df_filtrado.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)
