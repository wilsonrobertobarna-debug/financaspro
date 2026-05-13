import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. CONFIGURAÇÕES INICIAIS
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()

st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# Estilo para manter o visual limpo
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1.1rem !important; font-weight: bold !important; }
    [data-testid='stMetricValue'] { font-size: 1.2rem !important; color: #1E88E5 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets["connections"]["gsheets"]
    pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
    final_creds = {
        "type": creds_dict["type"], "project_id": creds_dict["project_id"],
        "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
        "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
    }
    return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)
ws_bancos = sh.worksheet("Bancos")

# 3. CARREGAMENTO DE DADOS
def carregar_dados():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['V_Num'] = df['Valor'].apply(lambda x: float(str(x).replace('R$', '').replace('.', '').replace(',', '.').strip()) if x else 0.0)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')
    return df

def carregar_bancos():
    dados = ws_bancos.get_all_values()
    return pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()

df_base = carregar_dados()
df_bancos_info = carregar_bancos()
bancos_disponiveis = sorted(df_bancos_info.iloc[:, 0].unique()) if not df_bancos_info.empty else ["Nubank", "Itaú", "Santander"]

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR E NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📅 Pendências", "🐾 Pets", "🚗 Veículo", "📄 WhatsApp"])

# FORMULÁRIO DE LANÇAMENTO (GLOBAL)
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Vencimento", hoje_br)
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet", "Veículo", "Outros"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pendente", "Pago"])
        if st.form_submit_button("SALVAR"):
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), f"{f_val:.2f}".replace('.', ','), f_des, f_cat, f_tip, f_bnc, f_sta, ""])
            st.success("Salvo!"); st.rerun()

# 5. LÓGICA DAS ABAS
if aba == "💰 Finanças":
    st.title("🛡️ Resumo Financeiro")
    mes_sel = st.selectbox("Mês", df_base['DT'].dt.strftime('%m/%Y').unique() if not df_base.empty else ["-"])
    df_mes = df_base[df_base['DT'].dt.strftime('%m/%Y') == mes_sel]
    
    c1, c2, c3 = st.columns(3)
    rec = df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()
    des = df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()
    c1.metric("Receitas", m_fmt(rec))
    c2.metric("Despesas", m_fmt(des))
    c3.metric("Saldo", m_fmt(rec - des))
    st.dataframe(df_mes[['DT', 'Descrição', 'Valor', 'Status']], use_container_width=True)

elif aba == "📅 Pendências":
    st.title("📅 Contas Pendentes")
    df_p = df_base[df_base['Status'] == 'Pendente']
    if not df_p.empty:
        st.table(df_p[['Vencimento', 'Descrição', 'Valor', 'Banco']])
    else:
        st.success("Tudo pago, Wilson!")

elif aba == "🐾 Pets":
    st.title("🐾 Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Gasto Total com Pets", m_fmt(df_pets['V_Num'].sum()))
    st.dataframe(df_pets, use_container_width=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Controle do Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.metric("Gasto Total Veículo", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car, use_container_width=True)

elif aba == "📄 WhatsApp":
    st.title("📄 Relatório para WhatsApp")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", hoje_br - timedelta(days=30))
    d_fim = c2.date_input("Fim", hoje_br)
    
    # Lógica de cálculo (Bancos e Cartões)
    saldos_txt = ""
    total_pat = 0.0
    for b in bancos_disponiveis:
        # Pega info do banco na planilha Bancos
        info = df_bancos_info[df_bancos_info.iloc[:,0] == b]
        tipo = str(info.iloc[0, 2]).upper() if not info.empty else "CONTA"
        val_base = float(str(info.iloc[0,1]).replace('R$','').replace('.','').replace(',','.').strip()) if not info.empty else 0.0
        
        if "CART" in tipo:
            usado = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pendente')]['V_Num'].sum()
            saldos_txt += f"💳 {b}: Limite {m_fmt(val_base)} | Usado: {m_fmt(usado)}\n"
        else:
            movs = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pago')]
            saldo = val_base + movs[movs['Tipo'] == 'Receita']['V_Num'].sum() - movs[movs['Tipo'] == 'Despesa']['V_Num'].sum()
            saldos_txt += f"🏦 {b}: {m_fmt(saldo)}\n"
            total_pat += saldo

    relat = f"*FINANÇAS WILSON*\n{saldos_txt}\n*Total Patrimônio:* {m_fmt(total_pat)}"
    st.text_area("Texto:", relat, height=200)
    st.markdown(f"[📲 Enviar para WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})")
