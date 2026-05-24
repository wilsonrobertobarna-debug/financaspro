import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1.1rem !important; font-weight: bold !important; }
    [data-testid='stMetricValue'] { font-size: 1.1rem !important; font-weight: bold !important; }
    .block-container { padding-top: 1rem; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict: st.error("⚠️ Verifique os Secrets!"); st.stop()
    pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
    return gspread.authorize(Credentials.from_service_account_info({
        "type": creds_dict["type"], "project_id": creds_dict["project_id"],
        "private_key": pk, "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"]
    }, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)
ws_bancos = sh.worksheet("Bancos") if "Bancos" in [w.title for w in sh.worksheets()] else None

# FUNÇÕES
def carregar_dados_gs():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    df['V_Num'] = pd.to_numeric(df['Valor'].replace({'R$': '', '\\.': '', ',': '.'}, regex=True), errors='coerce').fillna(0)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_manual_gs():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        return pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
    return pd.DataFrame()

def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

if 'df_base' not in st.session_state: atualizar_sessao()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']
bancos_disponiveis = df_bancos_info.iloc[:, 0].tolist() if not df_bancos_info.empty else ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"]
mes_atual = datetime.now().strftime('%m/%y')
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
if st.sidebar.button("🔄 Atualizar dados"):
    atualizar_sessao(); st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF", "📊 Análises & Configurações"])

# --- BLOCO DE FINANÇAS PRINCIPAL ---
if aba == "💰 Finanças & Bancos":
    st.header("💰 Finanças & Bancos")
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    st.pills("Período:", meses, selection_mode="single", default="Mai")
    
    # Exibir métricas básicas
    df_m = df_base[df_base['Mes_Ano'] == mes_atual]
    receita = df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()
    gasto = df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()
    st.columns(4)[0].metric("📈 Receita", m_fmt(receita))
    st.columns(4)[1].metric("📉 Gasto", m_fmt(gasto))

# --- BLOCO DE ANÁLISES (Onde colocaremos o botão do relatório) ---
elif aba == "📊 Análises & Configurações":
    st.markdown("## 📊 Painel de Análises & Configurações")
    st.subheader("🏦 Informações de Contas e Cartões")
    if 'mostrar_relatorio' not in st.session_state: st.session_state['mostrar_relatorio'] = False
    if st.button("📊 Clique aqui para ver o Relatório Bancário Completo"):
        st.session_state['mostrar_relatorio'] = not st.session_state['mostrar_relatorio']
    if st.session_state['mostrar_relatorio'] and not df_bancos_info.empty:
        st.dataframe(df_bancos_info, use_container_width=True, hide_index=True)
        if aba == "📊 Análises & Configurações":
    st.markdown("## 📊 Painel de Análises")
    
    # Exemplo: Gráfico de evolução do saldo (usando Plotly)
    import plotly.express as px
    
    df_analise = df_base.copy()
    df_analise['Data'] = pd.to_datetime(df_analise['DT'])
    df_analise = df_analise.sort_values('Data')
    
    # Calcular saldo acumulado (exemplo simples)
    df_analise['Saldo_Acumulado'] = df_analise.apply(
        lambda x: x['V_Num'] if x['Tipo'] == 'Receita' else -x['V_Num'], axis=1
    ).cumsum()
    
    fig = px.line(df_analise, x='Data', y='Saldo_Acumulado', title="Evolução do Saldo")
    st.plotly_chart(fig, use_container_width=True)
