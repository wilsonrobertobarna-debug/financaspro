import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. ESTILO WILSON (REFORÇADO)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 10px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
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

# 3. TRATAMENTO DE DADOS (FOCO NA PRECISÃO)
@st.cache_data(ttl=60)
def carregar_tudo():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
        else: df_c['Meta'] = 0.0
        
        ws = sh.get_worksheet(0)
        dados = ws.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_tudo()

# 4. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        def limpar(v):
            v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return pd.to_numeric(v, errors='coerce') or 0.0

        df_base['V_Num'] = df_base[c_val].apply(limpar)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # FILTRO POR BANCO
        bancos_unicos = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Filtrar por Banco:", bancos_unicos)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # --- LÓGICA DE CÁLCULO REVISADA ---
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar).sum()
        
        # Saldo Geral: Apenas o que já aconteceu (Status != Pendente conforme sua regra)
        df_realizado = df_base[df_base[c_sta] != 'Pendente']
        t_rec = df_realizado[(df_realizado[c_tip] == 'Receita') | (df_realizado[c_tip] == 'Rendimento')]['V_Num'].sum()
        t_des = df_realizado[df_realizado[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_geral = s_ini + t_rec - t_des

        # Métricas do Mês (Considerando o filtro de banco)
        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        m_receita = df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum()
        m_despesa = df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum()
        m_rendimento = df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum()
        m_pendente = df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum()

        # EXIBIÇÃO
        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {m_receita:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_despesa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {m_rendimento:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {m_pendente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- GRÁFICO POR BANCO ---
        st.write("---")
        st.subheader("🏦 Distribuição por Banco")
        saldos_b = []
        for b in df_bancos_cad['Nome do Banco'].unique():
            si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar).sum()
            re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & ((df_base[c_tip] == 'Receita') | (df_base[c_tip] == 'Rendimento'))]['V_Num'].sum()
            de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
            saldos_b.append({'Banco': b, 'Saldo': si + re - de})
        
        df_sb = pd.DataFrame(saldos_b)
        df_sb = df_sb[df_sb['Saldo'] != 0]
        if not df_sb.empty:
            fig_p = px.pie(df_sb, values='Saldo', names='Banco', hole=.4, color_discrete_sequence=px.colors.qualitative.Prism)
            st.plotly_chart(fig_p, use_container_width=True)

        # --- METAS E LANÇAMENTOS ---
        st.write("---")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"📊 Metas vs Gasto ({mes_atual})")
            g_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
            df_p = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': g_cat}).fillna(0.0)
            df_p = df_p[(df_p['Meta'] > 0) | (df_p['Real'] > 0)]
            if not df_p.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(y=df_p.index, x=df_p['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig.add_trace(go.Bar(y=df_p.index, x=df_p['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.2))
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("📈 Evolução")
            evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0.0)
            st.bar_chart(evol)

        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

    # FORMULÁRIO
    with st.sidebar.form("f"):
        st.write("### 🚀 Lançar")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()
