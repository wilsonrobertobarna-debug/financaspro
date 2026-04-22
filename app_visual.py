import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
import smtplib
import urllib.parse
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DE ACESSO ---
st.set_page_config(page_title="FinançasPro Wilson V601", layout="wide")
SENHA_ACESSO = "1234"

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("🔐 Acesso FinançasPro")
        senha = st.text_input("Senha:", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            if senha == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Incorreta!")
    st.stop()

if not st.session_state.autenticado: tela_login()

# --- 1. BANCO DE DADOS (GOOGLE SHEETS) ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def carregar_dados_google(aba):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
        if aba == "LANCAMENTOS" and df is not None and not df.empty:
            df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        return df if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

def salvar_dados_google(df, aba):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_s = df.copy()
    if 'DT' in df_s.columns: df_s = df_s.drop(columns=['DT'])
    conn.update(spreadsheet=URL_PLANILHA, worksheet=aba, data=df_s)

# Carregamento Inicial
df_g = carregar_dados_google("LANCAMENTOS")
df_b = carregar_dados_google("BANCOS")
df_m = carregar_dados_google("METAS")

lista_contas = sorted(list(set(["Dinheiro", "Pix"] + (df_b['Banco'].dropna().tolist() if not df_b.empty else []))))
lista_cats = sorted(list(set(["Mercado", "Ração", "Combustível", "Lazer", "Saúde"] + (df_m['Categoria'].dropna().tolist() if not df_m.empty else []))))

def formatar_br(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

# --- 2. INTERFACE WILSON ---
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson - V601</h1>", unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["💰 Lançar", "✅ Baixas", "📊 Gráficos", "📋 Extrato"])

with t1:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", date.today())
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita", "💎 Rendimento"], horizontal=True)
        
        c3, c4 = st.columns(2)
        benef = c3.text_input("Beneficiário:")
        valor = c4.number_input("Valor:", 0.0)
        
        c5, c6 = st.columns(2)
        cat = c5.selectbox("Categoria:", lista_cats)
        conta = c6.selectbox("Conta:", lista_contas)
        
        status = st.selectbox("Status:", ["⏳ Pendente", "✅ Pago"])
        desc = st.text_area("Descrição:")

        if st.button("🚀 GRAVAR NO GOOGLE", use_container_width=True):
            novo = pd.DataFrame([{
                "Data": dt_l.strftime('%d/%m/%Y'),
                "Tipo": tipo,
                "Categoria": cat,
                "Valor": valor,
                "Pagamento": conta,
                "Beneficiário": benef,
                "Status": status,
                "Descrição": desc
            }])
            df_g = pd.concat([df_g, novo], ignore_index=True)
            salvar_dados_google(df_g, "LANCAMENTOS")
            st.success("✅ Gravado com sucesso!")
            st.rerun()

with t3:
    if not df_g.empty:
        despesas = df_g[df_g['Tipo'].str.contains("Despesa", na=False)]
        if not despesas.empty:
            fig = px.pie(despesas, values='Valor', names='Categoria', title='Meus Gastos')
            st.plotly_chart(fig, use_container_width=True)

with t4:
    st.subheader("📋 Extrato do Google Sheets")
    st.dataframe(df_g.drop(columns=['DT']) if 'DT' in df_g.columns else df_g, use_container_width=True)
