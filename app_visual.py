import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. ESTILO REFINADO (Tarja mais estreita)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff;
        color: white;
        padding: 8px 15px; /* Reduzido de 20px para 8px */
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .tag-card {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
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
        st.error(f"Erro: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# CONFIGURAÇÕES
META_GASTO_MENSAL = 3000.00
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Extras"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer"],
    "Rendimento": ["Dividendos", "Juros", "Aplicações"],
    "Pendência": ["Boleto a Pagar", "Empréstimo", "Dívida"]
}

# --- BARRA LATERAL ---
st.sidebar.header("📝 Novo Lançamento")
tipo = st.sidebar.selectbox("Tipo:", list(categorias_dict.keys()))
with st.sidebar.form("form_lancamento", clear_on_submit=True):
    v_data = st.date_input("Data", datetime.now())
    v_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    v_cat = st.selectbox("Categoria", categorias_dict[tipo])
    v_desc = st.text_input("Descrição")
    if st.form_submit_button("Salvar"):
        if v_valor > 0:
            ws.append_row([v_data.strftime("%d/%m/%Y"), v_valor, v_cat, tipo, v_desc])
            st.cache_data.clear(); st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        # TOTAIS
        rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
        des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
        ren = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
        pen = df_v[df_v['Tipo'] == 'Pendência']['Valor'].sum()
        saldo = (rec + ren) - des

        # TARJA AZUL COMPACTA
        st.markdown(f"""
            <div class="saldo-container">
                <span style='font-weight: bold; font-size: 1rem;'>SALDO ATUAL</span>
                <span style='font-weight: bold; font-size: 1.5rem;'>R$ {saldo:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

        # TAGS
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {rec:,.2f}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {des:,.2f}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='tag-card' style='border-left-color:#17a2b8;'><b>Rendimentos</b><br>R$ {ren:,.2f}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='tag-card' style='border-left-color:#ffc107;'><b>Pendências</b><br>R$ {pen:,.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")
        df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
        res = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()

        # 📊 GRÁFICO 1: COMPARATIVO
        st.subheader("📊 Comparativo Mensal")
        fig1 = go.Figure()
        for t, cor in zip(["Receita", "Despesa", "Rendimento"], ["#28a745", "#dc3545", "#17a2b8"]):
            if t in res.columns:
                fig1.add_trace(go.Bar(x=res['Mês/Ano'], y=res[t], name=t, marker_color=cor))
        fig1.update_layout(barmode='group', height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig1, use_container_width=True)

        # 📊 GRÁFICO 2: METAS (Recuperado)
        st.subheader("🎯 Meta de Gastos (Limite)")
        fig2 = go.Figure()
        if 'Despesa' in res.columns:
            fig2.add_trace(go.Bar(x=res['Mês/Ano'], y=res['Despesa'], name='Gasto Real', marker_color='#007bff'))
            fig2.add_trace(go.Scatter(x=res['Mês/Ano'], y=[META_GASTO_MENSAL]*len(res), name='Meta', line=dict(color='#ffc107', width=3, dash='dash')))
        fig2.update_layout(height=300, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(df.tail(10), use_container_width=True)
except Exception as e:
    st.error(f"Erro: {e}")
