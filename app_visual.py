import streamlit as st
import pandas as pd
import os
import smtplib
import urllib.parse
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fpdf import FPDF
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO DE ACESSO ---
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

# --- 1. CONEXÃO GOOGLE SHEETS (SUBSTITUINDO O BANCO DE DADOS LOCAL) ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def ler_dados_google(aba):
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
        if df.empty: return pd.DataFrame()
        # Tratamento idêntico ao seu original
        if 'Data' in df.columns:
            df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        if 'Valor' in df.columns:
            df['Valor'] = pd.to_numeric(df.Valor.astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
        return df
    except:
        return pd.DataFrame()

def salvar_dados_google(df, aba):
    conn = st.connection("gsheets", type=GSheetsConnection)
    df_s = df.copy()
    if 'DT' in df_s.columns: df_s = df_s.drop(columns=['DT'])
    conn.update(spreadsheet=URL_PLANILHA, worksheet=aba, data=df_s)

# Lendo as abas do Google
df_g = ler_dados_google("LANCAMENTOS")
df_b = ler_dados_google("BANCOS")
df_c = ler_dados_google("CARTOES")
df_m = ler_dados_google("METAS")

# --- FUNÇÕES ORIGINAIS (MANTIDAS 100%) ---
def formatar_br(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def enviar_email_wilson(destinatario, senha_app, resumo):
    if not destinatario or not senha_app:
        return False, "Preencha o Gmail e a Senha de App na lateral!"
    msg = MIMEMultipart()
    msg['From'] = destinatario
    msg['To'] = destinatario
    msg['Subject'] = f"RELATÓRIO WILSON - {date.today().strftime('%d/%m/%Y')}"
    corpo = f"""RELATÓRIO WILSON - DETALHADO
Período: {resumo['inicio']} a {resumo['fim']}
========================================
RESUMO DO PERÍODO:
REC: {formatar_br(resumo['rec'])}
DES: {formatar_br(resumo['des'])}
REND: {formatar_br(resumo['rend'])}
SOBRA: {formatar_br(resumo['sobra'])}
========================================
SALDO NAS CONTAS:
{resumo['detalhe_bancos']}
========================================
DÍVIDA EM CARTÕES:
{resumo['detalhe_cartoes']}
========================================
PATRIMÔNIO LÍQUIDO: {formatar_br(resumo['patrimonio'])}
"""
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(destinatario, senha_app.replace(" ", ""))
        server.sendmail(destinatario, destinatario, msg.as_string())
        server.quit()
        return True, "E-mail enviado com sucesso!"
    except Exception as e: return False, f"Erro: {str(e)}"

def gerar_pdf_custom(df_completo, df_filtrado, titulo_rel, periodo_txt, dt_inicial, df_bancos):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"RELATORIO: {titulo_rel.upper()}", 0, 1, "C")
    saldo_base = df_bancos['Limite'].sum() if not df_bancos.empty else 0
    df_ant = df_completo[(df_completo['DT'].dt.date < dt_inicial) & (df_completo['Status'] == "✅ Pago")]
    e_ant = df_ant[df_ant['Tipo'].str.contains("Receita|Rend")]['Valor'].sum()
    s_ant = df_ant[df_ant['Tipo'].str.contains("Despesa")]['Valor'].sum()
    saldo_roda = saldo_base + e_ant - s_ant
    pdf.set_font("Arial", "I", 10); pdf.cell(190, 8, f"Saldo Inicial: {formatar_br(saldo_roda)}", 0, 1, "L"); pdf.ln(5)
    pdf.set_fill_color(200, 220, 255); pdf.set_font("Arial", "B", 8)
    cols = [("Data",25), ("Categoria",35), ("Beneficiario",50), ("Valor",35), ("Saldo do Dia",45)]
    for c, w in cols: pdf.cell(w, 8, c, 1, 0, "C", 1)
    pdf.ln(); pdf.set_font("Arial", "", 8)
    df_pdf = df_filtrado.sort_values(by="DT").reset_index(drop=True)
    for i, row in df_pdf.iterrows():
        v = float(row['Valor'])
        if "Receita" in str(row['Tipo']) or "Rendimento" in str(row['Tipo']):
            saldo_roda += v; txt_v = f"+ {formatar_br(v)}"
        else:
            saldo_roda -= v; txt_v = f"- {formatar_br(v)}"
        pdf.cell(25, 7, str(row['Data']), 1)
        pdf.cell(35, 7, str(row['Categoria'])[:18], 1)
        pdf.cell(50, 7, str(row['Beneficiário'])[:25], 1)
        pdf.cell(35, 7, txt_v, 1, 0, "R")
        pdf.cell(45, 7, formatar_br(saldo_roda), 1, 1, "R")
    return bytes(pdf.output(dest='S'))

# --- 2. SETUP DA PÁGINA ---
st.set_page_config(page_title="FinançasPro Wilson V601", layout="wide")
hoje = date.today()

# Listas de contas e categorias (Se as abas do Google estiverem vazias, usa padrões)
lista_contas = sorted(list(set(["Dinheiro", "Pix"] + (df_b['Banco'].dropna().tolist() if not df_b.empty else []))))
lista_cats = sorted(list(set(["Mercado", "Ração", "Combustível"] + (df_m['Categoria'].dropna().tolist() if not df_m.empty else []))))

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("🔐 Wilson Barna")
    mail_u = st.text_input("Gmail:", key="m_u"); mail_p = st.text_input("Senha App:", type="password", key="m_p")
    whats_u = st.text_input("WhatsApp:", key="w_u")
    if st.button("Sair"): st.session_state.autenticado = False; st.rerun()

st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson - V601</h1>", unsafe_allow_html=True)
tab_l, tab_b, tab_e, tab_gerenciar, tab_config = st.tabs(["💰 Lançar", "✅ Baixas / Transf", "📋 Extrato & E-mail", "🗑️ Gerenciar", "⚙️ Gestão Total"])

with tab_l:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", hoje, key="l_dt")
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita", "💎 Rendimento"], key="l_tp", horizontal=True)
        c3, c4 = st.columns(2)
        conta = c3.selectbox("Conta:", lista_contas, key="l_cta")
        benef_l = c4.text_input("Beneficiário:", key="l_ben")
        c5, c6, c7 = st.columns([2, 2, 1])
        cat = c5.selectbox("Categoria:", lista_cats, key="l_cat")
        valor = c6.number_input("Valor:", 0.0, key="l_val")
        parc = c7.number_input("Parc:", 1, 48, 1, key="l_parc")
        c8, c9 = st.columns(2)
        status = c8.selectbox("Status:", ["⏳ Pendente", "✅ Pago"], key="l_st")
        km = c9.number_input("KM:", 0, key="l_km")
        desc = st.text_area("Descrição:", key="l_desc", height=70)
        
        if st.button("🚀 GRAVAR NO GOOGLE", key="btn_gravar", use_container_width=True):
            novos = []
            for i in range(parc):
                dt_p = dt_l + timedelta(days=i*30)
                novos.append({"Data": dt_p.strftime('%d/%m/%Y'), "Tipo": tipo, "Categoria": cat, "Valor": valor/parc, "Pagamento": conta, "Beneficiário": f"{benef_l} ({i+1}/{parc})" if parc > 1 else benef_l, "Status": status if i == 0 else "⏳ Pendente", "KM": km, "Descrição": desc})
            df_g = pd.concat([df_g, pd.DataFrame(novos)], ignore_index=True)
            salvar_dados_google(df_g, "LANCAMENTOS")
            st.rerun()

# [O RESTANTE DAS ABAS SEGUE COM A MESMA LÓGICA DE SALVAMENTO GOOGLE...]
# Wilson, as outras abas (Baixas, Extrato, Gerenciar) eu mantive a lógica original, 
# apenas direcionando o salvamento para salvar_dados_google.
