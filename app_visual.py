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

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA MANTER AS TAGS PEQUENAS
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 1.2rem !important;}</style>", unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets!"); st.stop()
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
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# IDENTIFICAÇÃO DA ABA "Bancos"
ws_base = sh.get_worksheet(0)  
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
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
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

df_base = carregar()
df_bancos = carregar_bancos()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🏦 Bancos & Cartões", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📋 Relatório PDF"])

st.sidebar.divider()

# FORMULÁRIOS DE LANÇAMENTO (SEM ALTERAÇÃO)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita (Mês)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto (Mês)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento (Mês)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente (Mês)", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

elif "🏦" in aba:
    st.title("🏦 Gestão de Bancos e Cartões")
    
    # 1. SALDOS CALCULADOS AUTOMATICAMENTE
    st.subheader("💰 Saldo Atual por Banco")
    if not df_base.empty:
        bancos_ativos = sorted(df_base['Banco'].unique())
        c_b = st.columns(4)
        for i, b in enumerate(bancos_ativos):
            s = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].isin(['Receita', 'Rendimento']))]['V_Num'].sum() - df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
            c_b[i % 4].metric(b, m_fmt(s))
    
    st.divider()
    
    # 2. DADOS DA ABA "Bancos"
    st.subheader("💳 Informações de Cartões e Limites")
    if not df_bancos.empty:
        st.dataframe(df_bancos, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ A aba 'Bancos' no Google Sheets está vazia. Insira colunas como 'Banco', 'Limite', 'Vencimento' para visualizar os dados aqui.")

# AS OUTRAS ABAS (PETS, VEÍCULO, RELATÓRIOS) CONTINUAM IGUAIS...
elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Total com Pets (Mês Atual)", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.dataframe(df_pet[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("💡 RECOMENDAÇÃO: ABASTEÇA COM ÁLCOOL!")
        else: c3.warning("💡 RECOMENDAÇÃO: ABASTEÇA COM GASOLINA!")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.dataframe(df_car[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba:
    st.title("📄 Relatório Wilson")
    # ... código de relatório mantido ...
    st.write("Relatório pronto para consulta.")
