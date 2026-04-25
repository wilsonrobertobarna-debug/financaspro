import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 0.9rem; }
    .receita { background-color: #28a745; }
    .despesa { background-color: #dc3545; }
    .rendimento { background-color: #17a2b8; }
    .pendencia { background-color: #ffc107; color: #212529; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
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

# --- NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.sidebar.header("📝 Novo Lançamento")
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_cat = st.text_input("Categoria")
        f_tipo = st.selectbox("Tipo:", ["Receita", "Despesa", "Rendimento", "Pendência"])
        f_banco = st.selectbox("Banco:", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
        f_status = st.text_input("Status", value="Pago")
        if st.form_submit_button("🚀 SALVAR FINANÇAS"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    try:
        dados_list = ws.get_all_values()
        if len(dados_list) > 1:
            # Pega apenas as 6 primeiras colunas para evitar o erro de duplicados/vazios
            df = pd.DataFrame(dados_list[1:], columns=dados_list[0])
            df = df.iloc[:, :6] 
            
            # Limpeza de nomes e conversão
            df.columns = [c.strip() for c in df.columns]
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df_v = df.dropna(subset=['Data']).copy()

            st.title("🛡️ FinançasPro Wilson")
            
            # CARDS
            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            v_pend = df_v[df_v['Tipo'] == 'Pendência']['Valor'].sum()
            
            st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL</small><h1 style="margin:0;">R$ {(v_rec + v_rend) - v_des:,.2f}</h1></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-container"><div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div><div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div><div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div><div class="card pendencia">Pendentes<br>R$ {v_pend:,.2f}</div></div>', unsafe_allow_html=True)

            st.subheader("📋 Últimos Lançamentos")
            df_table = df_v.tail(10).copy()
            df_table['Data'] = df_table['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_table.iloc[::-1], use_container_width=True)

            # GRÁFICO POR CATEGORIA
            st.markdown("---")
            st.subheader("🎯 Gastos por Categoria (Mês Atual)")
            mes_f = datetime.now().strftime('%m/%Y')
            df_v['Mês'] = df_v['Data'].dt.strftime('%m/%Y')
            df_mes = df_v[(df_v['Mês'] == mes_f) & (df_v['Tipo'] == 'Despesa')]
            res_cat = df_mes.groupby('Categoria')['Valor'].sum().reset_index()
            if not res_cat.empty:
                fig = go.Figure(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff'))
                st.plotly_chart(fig, use_container_width=True)
    except Exception as e: st.error(f"Erro ao carregar dados: {e}")

# ==========================================
# ABAS PETS E VEÍCULO (Seguem a mesma lógica)
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    try:
        ws_p = sh.worksheet("Controle_Pets")
        # ... formulário igual ao anterior ...
        dados_p = ws_p.get_all_values()
        if len(dados_p) > 1:
            dp = pd.DataFrame(dados_p[1:], columns=dados_p[0]).iloc[:, :6]
            st.dataframe(dp.iloc[::-1], use_container_width=True)
    except: st.info("Verifique a aba 'Controle_Pets' no Sheets.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    try:
        ws_v = sh.worksheet("Controle_Veiculo")
        # ... formulário igual ao anterior ...
        dados_v = ws_v.get_all_values()
        if len(dados_v) > 1:
            dv = pd.DataFrame(dados_v[1:], columns=dados_v[0]).iloc[:, :5]
            st.dataframe(dv.iloc[::-1], use_container_width=True)
    except: st.info("Verifique a aba 'Controle_Veiculo' no Sheets.")
