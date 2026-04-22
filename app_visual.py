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

# TELA DE LOGIN BLINDADA
if not st.session_state.autenticado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("🔐 Acesso FinançasPro")
        senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            if senha == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Incorreta!")
    st.stop()

# --- CONEXÃO GOOGLE SHEETS ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def carregar_dados(aba):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
        if df is None or df.empty:
            if aba == "LANCAMENTOS":
                return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Pagamento', 'Beneficiário', 'Status', 'KM', 'Descrição'])
            return pd.DataFrame()
        # Tratamento de data e valor padrão Wilson
        if 'Data' in df.columns:
            df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        if 'Valor' in df.columns:
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
        return df
    except:
        return pd.DataFrame()

def salvar_dados(df, aba):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_s = df.copy()
    if 'DT' in df_s.columns: df_s = df_s.drop(columns=['DT'])
    conn.update(spreadsheet=URL_PLANILHA, worksheet=aba, data=df_s)

# CARREGAMENTO INICIAL
df_g = carregar_dados("LANCAMENTOS")
df_b = carregar_dados("BANCOS")
df_m = carregar_dados("METAS")

# LISTAS DE SELEÇÃO
lista_contas = sorted(list(set(["Dinheiro", "Pix"] + (df_b['Banco'].dropna().tolist() if 'Banco' in df_b.columns else []))))
lista_cats = sorted(list(set(["Mercado", "Ração", "Combustível", "Saúde", "Lazer"] + (df_m['Categoria'].dropna().tolist() if 'Categoria' in df_m.columns else []))))

# --- INTERFACE PRINCIPAL ---
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson - V601</h1>", unsafe_allow_html=True)
tab_l, tab_b, tab_e, tab_gerenciar = st.tabs(["💰 Lançar", "✅ Baixas", "📋 Extrato", "🗑️ Gerenciar"])

with tab_l:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", date.today())
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita", "💎 Rendimento"], horizontal=True)
        
        c3, c4 = st.columns(2)
        conta = c3.selectbox("Conta:", lista_contas)
        benef_l = c4.text_input("Beneficiário:")
        
        c5, c6, c7 = st.columns([2, 2, 1])
        cat = c5.selectbox("Categoria:", lista_cats)
        valor = c6.number_input("Valor:", 0.0)
        parc = c7.number_input("Parc:", 1, 48, 1)
        
        c8, c9 = st.columns(2)
        status = c8.selectbox("Status:", ["⏳ Pendente", "✅ Pago"])
        km = c9.number_input("KM:", 0)
        
        desc = st.text_area("Descrição:", height=70)
        
        if st.button("🚀 GRAVAR LANÇAMENTO", use_container_width=True):
            novos = []
            for i in range(parc):
                dt_p = dt_l + timedelta(days=i*30)
                novos.append({
                    "Data": dt_p.strftime('%d/%m/%Y'),
                    "Tipo": tipo,
                    "Categoria": cat,
                    "Valor": valor/parc,
                    "Pagamento": conta,
                    "Beneficiário": f"{benef_l} ({i+1}/{parc})" if parc > 1 else benef_l,
                    "Status": status if i == 0 else "⏳ Pendente",
                    "KM": km,
                    "Descrição": desc
                })
            df_g = pd.concat([df_g, pd.DataFrame(novos)], ignore_index=True)
            salvar_dados(df_g, "LANCAMENTOS")
            st.success("Gravado com sucesso!")
            st.rerun()

with tab_e:
    st.subheader("📋 Extrato de Lançamentos")
    if not df_g.empty:
        st.dataframe(df_g.drop(columns=['DT']) if 'DT' in df_g.columns else df_g, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado na planilha.")

# O restante das funções de PDF e E-mail Wilson, você pode manter as que já tinha, 
# contanto que elas usem o df_g que carregamos lá em cima.
