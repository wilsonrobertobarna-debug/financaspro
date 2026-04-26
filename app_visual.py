import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. ESTILO E CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 15px;
        border-radius: 12px; text-align: center; margin-bottom: 25px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; }
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

# 3. MOTOR DE DADOS (LIMPEZA AGRESSIVA)
@st.cache_data(ttl=60)
def carregar_dados():
    try:
        # Categorias e Metas (Coluna C)
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
        
        df_c['Nome'] = df_c['Nome'].astype(str).str.strip()

        # Lançamentos e Bancos
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos, df_cats, df_base = carregar_dados()

# 4. DASHBOARD PRINCIPAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        # Mapeamento de colunas por posição para evitar erro de nome
        c_val, c_cat, c_tip = df_base.columns[1], df_base.columns[2], df_base.columns[3]

        df_base['V_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace('.', '').str.replace(',', '.'), errors='coerce').fillna(0.0)
        df_base['Mes_Ano'] = pd.to_datetime(df_base[df_base.columns[0]], dayfirst=True, errors='coerce').dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # Bloco de Saldo
        s_ini = pd.to_numeric(df_bancos['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if not df_bancos.empty else 0
        total_rec = df_base[df_base[c_tip] == 'Receita']['V_Num'].sum()
        total_desp = df_base[df_base[c_tip] == 'Despesa']['V_Num'].sum()
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual</small><h2>R$ {(s_ini + total_rec - total_desp):,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📊 Meta vs Real ({mes_atual})")
            gastos_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base[c_tip] == 'Despesa')].groupby(c_cat)['V_Num'].sum()
            
            df_grafico = pd.DataFrame({'Meta': df_cats.set_index('Nome')['Meta'], 'Real': gastos_mes}).fillna(0.0)
            df_grafico = df_grafico[(df_grafico['Meta'] > 0) | (df_grafico['Real'] > 0)]

            if not df_grafico.empty:
                fig = go.Figure()
                fig.add_trace(go.Bar(y=df_grafico.index, x=df_grafico['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig.add_trace(go.Bar(y=df_grafico.index, x=df_grafico['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig.update_layout(barmode='group', height=350, margin=dict(l=0, r=0, t=0, b=0), legend=dict(orientation="h", y=1.2))
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📈 Evolução Mensal")
            evolucao = df_base.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0.0)
            st.bar_chart(evolucao)

        st.dataframe(df_base.iloc[::-1], use_container_width=True)

    # FORMULÁRIO DE LANÇAMENTO
    with st.sidebar.form("add"):
        st.write("### 🚀 Lançar")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats['Nome'].tolist()) if not df_cats.empty else ["Outros"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos.empty else ["Dinheiro"])
        if st.form_submit_button("SALVAR"):
            sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# (As abas Milo e Veículo seguem o mesmo padrão de visualização)
