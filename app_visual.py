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

# DIMINUIR O VALOR (Métricas)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
ws_base = sh.get_worksheet(0)

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

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📲 WhatsApp", "📄 Relatório PDF"])

st.sidebar.divider()

with st.sidebar.expander("🚀 Novo", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parc.", min_value=1, value=1)
        f_des = st.text_input("Desc.")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Cat.", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Bco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("Despesas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        st.subheader("🔍 Lançamentos")
        st.dataframe(df_base[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    st.subheader("⛽ Álcool ou Gasolina?")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
    preco_alc = col_c1.number_input("Preço Álcool", min_value=0.0, step=0.01, format="%.2f")
    preco_gas = col_c2.number_input("Preço Gasolina", min_value=0.0, step=0.01, format="%.2f")
    if preco_alc > 0 and preco_gas > 0:
        res = preco_alc / preco_gas
        if res <= 0.7: col_c3.success(f"✅ ÁLCOOL ({res:.2%})")
        else: col_c3.warning(f"✅ GASOLINA ({res:.2%})")

elif "📲" in aba:
    st.title("📲 WhatsApp")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("De", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = c2.date_input("Até", datetime.now(), format="DD/MM/YYYY")
    
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    
    if not df_per.empty:
        # Cálculos do Período
        r_v = df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        rend_v = df_per[df_per['Tipo'] == 'Rendimento']['V_Num'].sum()
        sobra = (r_v + rend_v) - d_v
        
        # Cálculo de Saldos por Banco (Tudo desde o início)
        bancos = sorted(df_base['Banco'].unique())
        saldos_txt = ""
        total_patrimonio = 0
        for b in bancos:
            if b.strip():
                entrou = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                saiu = df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
                saldo_b = entrou - saiu
                saldos_txt += f"- {b}: {m_fmt(saldo_b)}\n"
                total_patrimonio += saldo_b

        # Montagem do Relatório igual ao que você tinha
        relat = (
            f"📊 *RELATÓRIO WILSON*\n"
            f"📅 Período: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
            f"============================\n"
            f"🟢 REC: {m_fmt(r_v)}\n"
            f"🔴 DES: {m_fmt(d_v)}\n"
            f"💰 REND: {m_fmt(rend_v)}\n"
            f"⚖️ SOBRA: {m_fmt(sobra)}\n"
            f"============================\n\n"
            f"🏦 *SALDOS ATUAIS:*\n"
            f"{saldos_txt}\n"
            f"⭐ *PATRIMÔNIO:* {m_fmt(total_patrimonio)}"
        )
        
        st.text_area("Cópia", relat, height=400)
        st.markdown(f'[📲 Enviar via WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif "📄" in aba:
    st.title("📄 Relatório PDF")
    # ... (Restante do código do PDF permanece igual)
