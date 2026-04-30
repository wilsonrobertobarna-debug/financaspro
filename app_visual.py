import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO CSS PARA MANTER AS TAGS DE VALORES PEQUENAS
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 1.1rem !important;}</style>", unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique as chaves nos Secrets!"); st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
# Sua Planilha Principal
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# IDENTIFICAÇÃO DAS ABAS
ws_base = sh.get_worksheet(0) # Primeira aba (Lançamentos)
try:
    ws_bancos = sh.worksheet("Bancos") # Aba que você criou
except:
    ws_bancos = None

# 3. FUNÇÕES DE CARREGAMENTO DE DADOS
@st.cache_data(ttl=2)
def carregar_base():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

@st.cache_data(ttl=2)
def carregar_bancos():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 0:
            # Retorna tudo o que você preencheu na aba Bancos
            return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

# INICIALIZAÇÃO DOS DADOS
df_base = carregar_base()
df_bancos = carregar_bancos()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. BARRA LATERAL (MENU E LANÇAMENTOS)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🏦 Bancos & Cartões", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

st.sidebar.divider()

with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "XP", "Mercado Pago"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS

# --- TELA 1: FINANÇAS ---
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_total = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_total)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimentos", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendentes", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        st.subheader("📊 Últimos Lançamentos")
        st.dataframe(df_base[['Data', 'Descrição', 'Categoria', 'Valor', 'Banco', 'Status']].iloc[::-1].head(10), use_container_width=True, hide_index=True)

# --- TELA 2: BANCOS & CARTÕES (Ajustada para sua nova aba) ---
elif "🏦" in aba:
    st.title("🏦 Gestão de Bancos e Cartões")
    
    # Parte 1: Saldo calculado pelos lançamentos
    st.subheader("💰 Saldo em Conta (Cálculo Automático)")
    if not df_base.empty:
        bancos_ativos = sorted(df_base['Banco'].unique())
        cols = st.columns(4)
        for i, b in enumerate(bancos_ativos):
            s = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].isin(['Receita', 'Rendimento']))]['V_Num'].sum() - \
                df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
            cols[i % 4].metric(b, m_fmt(s))
    
    st.divider()
    
    # Parte 2: O que você preencheu manualmente no Sheets
    st.subheader("📋 Informações da Aba Bancos")
    if not df_bancos.empty:
        # Mostra exatamente Nome do Banco, Saldo Inicial, Tipo de Conta, etc.
        st.dataframe(df_bancos, use_container_width=True, hide_index=True)
    else:
        st.warning("A aba 'Bancos' no Google Sheets parece estar vazia ou não foi encontrada.")

# --- TELA 3: PETS ---
elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Total com Pets", m_fmt(df_pet['V_Num'].sum()))
        st.dataframe(df_pet.iloc[::-1], use_container_width=True, hide_index=True)

# --- TELA 4: VEÍCULO ---
elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    st.info("Aqui você acompanha gastos com combustível e manutenção.")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.dataframe(df_car.iloc[::-1], use_container_width=True, hide_index=True)

# --- TELA 5: RELATÓRIOS ---
elif "📄" in aba:
    st.title("📄 Relatório de Gastos")
    if not df_base.empty:
        # Gráfico simples de gastos por categoria
        df_gastos = df_base[df_base['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        fig = px.pie(df_gastos, values='V_Num', names='Categoria', title="Distribuição de Gastos")
        st.plotly_chart(fig, use_container_width=True)
