import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; }
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
ws = sh.get_worksheet(0)

# CONFIGURAÇÕES
META_GASTO = 500.00

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    v_tipo = st.sidebar.selectbox("Tipo:", ["Receita", "Despesa", "Rendimento", "Pendência"])
    v_banco = st.sidebar.selectbox("Banco:", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
    
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_cat = st.text_input("Categoria (Ex: Aluguel, Salário)")
        f_status = st.text_input("Status", value="Pago") 
        if st.form_submit_button("🚀 SALVAR AGORA"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, v_tipo, v_banco, f_status])
            st.cache_data.clear(); st.rerun()

# --- PROCESSAMENTO ---
try:
    dados_raw = ws.get_all_values()
    if len(dados_raw) > 1:
        df = pd.DataFrame(dados_raw[1:], columns=dados_raw[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            
            # CÁLCULOS PARA OS CARDS
            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            v_pend = df_v[df_v['Tipo'] == 'Pendência']['Valor'].sum()
            v_saldo = (v_rec + v_rend) - v_des

            # 1. TAG CENTRAL DE SALDO
            st.markdown(f"""
                <div class="saldo-container">
                    <small>SALDO ATUAL DISPONÍVEL</small>
                    <h1 style='margin:0;'>R$ {v_saldo:,.2f}</h1>
                </div>
            """, unsafe_allow_html=True)

            # 2. TAGS DE RESUMO (CARDS COLORIDOS)
            st.markdown(f"""
                <div class="card-container">
                    <div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div>
                    <div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div>
                    <div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div>
                    <div class="card pendencia">Pendentes<br>R$ {v_pend:,.2f}</div>
                </div>
            """, unsafe_allow_html=True)

            # 3. TABELA DE LANÇAMENTOS
            st.subheader("📋 Últimos Lançamentos")
            df_display = df_v.copy()
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            df_final = df_display[['Data', 'Valor', 'Categoria', 'Tipo', 'Banco', 'Descrição']].tail(15)
            df_final.columns = ['Data', 'Valor', 'Categoria', 'Tipo', 'Banco', 'Status']
            st.dataframe(df_final.iloc[::-1], use_container_width=True)

            # 4. GRÁFICO MENSAL
            st.markdown("---")
            st.subheader("📊 Comparativo Mensal")
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            res_m = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Despesa'], name='Despesa', marker_color='#dc3545'))
            st.plotly_chart(fig1, use_container_width=True)

            # 5. GRÁFICO DE METAS
            st.markdown("---")
            st.subheader("🎯 Metas por Categoria")
            res_c = df_v[df_v['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().reset_index()
            if not res_c.empty:
                fig2 = go.Figure()
                fig2.add_trace(go.Bar(x=res_c['Categoria'], y=res_c['Valor'], name='Gasto', marker_color='#007bff'))
                fig2.add_trace(go.Scatter(x=res_c['Categoria'], y=[META_GASTO]*len(res_c), name='Meta', line=dict(color='#ffc107', dash='dash')))
                st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")
