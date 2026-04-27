import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA (Para o ícone no celular)
st.set_page_config(
    page_title="FinançasPro",
    page_icon="🛡️",
    layout="wide"
)

# Estilos CSS Personalizados
st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 15px;
        border-radius: 12px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .resumo-card { 
        padding: 8px; border-radius: 8px; text-align: center; 
        border: 1px solid #ddd; background-color: #f8f9fa; margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
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
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. TRATAMENTO DE DADOS
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
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # Filtros
        bancos_lista = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculos de Saldo
        if banco_sel == "Todos":
            s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_v).sum()
        else:
            s_ini = df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_v).sum()
            
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

        st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Receitas", f"R$ {m_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("📉 Despesas", f"R$ {m_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("💰 Rendimento", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col4.metric("⏳ Pendente", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- ALERTAS DE METAS ---
        gasto_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
        df_m = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': gasto_cat}).fillna(0.0)
        df_m = df_m[df_m['Meta'] > 0]

        categorias_estouradas = df_m[df_m['Real'] > df_m['Meta']]
        if not categorias_estouradas.empty:
            for cat, row in categorias_estouradas.iterrows():
                excesso = row['Real'] - row['Meta']
                st.error(f"🚨 **Atenção Wilson!** Ultrapassou a meta de **{cat}** em **R$ {excesso:,.2f}**.")

        # --- RESUMO DA ECONOMIA (MINI CARDS) ---
        st.write("---")
        st.subheader("📊 Resumo de Economia")
        if not df_m.empty:
            cols_res = st.columns(5)
            for i, (categoria, row) in enumerate(df_m.iterrows()):
                pct = (row['Real'] / row['Meta']) * 100 if row['Meta'] > 0 else 0
                cor = "#28a745" if pct < 80 else ("#ffc107" if pct <= 100 else "#dc3545")
                with cols_res[i % 5]:
                    st.markdown(f'<div class="resumo-card"><small><b>{categoria}</b></small><br><span style="color:{cor}; font-weight:bold;">{pct:.1f}%</span><br><small>R$ {row["Real"]:,.0f} / {row["Meta"]:,.0f}</small></div>', unsafe_allow_html=True)

        # --- GRÁFICOS LADO A LADO ---
        st.write("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🏦 Bancos")
            s_pizza = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar_v).sum()
                re_p = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                de_p = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                s_pizza.append({'Banco': b, 'Saldo': (si + re_p - de_p)})
            df_p = pd.DataFrame(s_pizza)
            fig_p = px.pie(df_p[df_p['Saldo'] > 0], values='Saldo', names='Banco', hole=.4, height=350)
            st.plotly_chart(fig_p, use_container_width=True)

        with g2:
            st.subheader("📊 Gráfico de Metas")
            if not df_m.empty:
                df_plot = df_m.sort_values('Meta')
                fig_meta = go.Figure()
                fig_meta.add_trace(go.Bar(y=df_plot.index, x=df_plot['Meta'], name='Meta', orientation='h', marker_color='#E0E0E0'))
                fig_meta.add_trace(go.Bar(y=df_plot.index, x=df_plot['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig_meta.update_layout(barmode='overlay', height=350, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_meta, use_container_width=True)

        # --- EVOLUÇÃO ---
        st.write("---")
        st.subheader("📈 Evolução Mensal")
        evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
        if not evol.empty:
            st.bar_chart(evol)

        st.subheader("📋 Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # BARRA LATERAL - FORMULÁRIO
    with st.sidebar.form("novo"):
        st.write("### 🚀 Lançar")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()
