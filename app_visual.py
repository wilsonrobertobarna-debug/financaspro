import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro", page_icon="🛡️", layout="wide")

# Estilos CSS (Estrutura 100% preservada)
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
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

# 3. TRATAMENTO E DATA BRASIL (GMT-3)
def limpar_v(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

# Pega o horário exato de Brasília agora
fuso_br = timezone(timedelta(hours=-3))
agora_br = datetime.now(fuso_br)
hoje_br = agora_br.date()

@st.cache_data(ttl=60)
def carregar_dados():
    ws_l = sh.get_worksheet(0)
    dados_l = ws_l.get_all_values()
    df_l = pd.DataFrame(dados_l[1:], columns=dados_l[0]) if len(dados_l) > 1 else pd.DataFrame()
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    df_c.columns = [str(c).strip() for c in df_c.columns]
    df_c['Meta'] = df_c['Meta'].apply(limpar_v) if 'Meta' in df_c.columns else 0.0
    return df_b, df_c, df_l

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

# 4. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Menu:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]
        df_base['V_Num'] = df_base[c_val].apply(limpar_v)
        # Lê a data da planilha tratando como dia/mês/ano
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        
        # Filtros e Saldos
        bancos_lista = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Métricas
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_v).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_v).sum()
        df_pago = df_filtrado[df_filtrado[c_sta] == 'Pago']
        saldo_atual = s_ini + df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()

        mes_f_atual = hoje_br.strftime('%m/%y')
        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_f_atual]

        st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Receitas", f"R$ {df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("📉 Despesas", f"R$ {df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("💰 Rendimento", f"R$ {df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col4.metric("⏳ Pendente", f"R$ {df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- ECONOMIA ---
        st.write("---")
        st.subheader("📊 Resumo de Economia")
        gasto_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
        df_m = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': gasto_cat}).fillna(0.0)
        df_m = df_m[df_m['Meta'] > 0]

        if not df_m.empty:
            cols_res = st.columns(5)
            for i, (categoria, row) in enumerate(df_m.iterrows()):
                pct = (row['Real'] / row['Meta']) * 100 if row['Meta'] > 0 else 0
                cor = "#28a745" if pct < 80 else ("#ffc107" if pct <= 100 else "#dc3545")
                with cols_res[i % 5]:
                    st.markdown(f'<div class="resumo-card"><small><b>{categoria}</b></small><br><span style="color:{cor}; font-weight:bold;">{pct:.1f}%</span><br><small>R$ {row["Real"]:,.0f} / {row["Meta"]:,.0f}</small></div>', unsafe_allow_html=True)

        # --- GRÁFICOS ---
        st.write("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🏦 Bancos")
            s_pizza = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar_v).sum()
                re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                s_pizza.append({'Banco': b, 'Saldo': si + re - de})
            st.plotly_chart(px.pie(pd.DataFrame(s_pizza), values='Saldo', names='Banco', hole=.4, height=350), use_container_width=True)
