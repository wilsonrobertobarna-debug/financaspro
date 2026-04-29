import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF

# --- 1. CONEXÃO DIRETA (O CORAÇÃO DO PROGRAMA) ---
st.set_page_config(page_title="FinançasPro Wilson v8.0", layout="wide")

@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

@st.cache_data(ttl=2)
def carregar_dados():
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Planilha'] = range(2, len(df) + 2)
    def p_float(v):
        try:
            val = str(v).replace('R$', '').replace('.', '').replace(',', '.').strip()
            return float(val) if val else 0.0
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['V_Final'] = df.apply(lambda r: r['V_Num'] if str(r['Tipo']).strip() in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. FUNÇÃO PDF (O QUE VOCÊ PEDIU) ---
def gerar_pdf(df_filtrado, periodo_txt):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "RELATORIO FINANCEIRO - WILSON", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Periodo: {periodo_txt}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(20, 8, "Data", 1, 0, "C", True)
    pdf.cell(75, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(25, 8, "Banco", 1, 0, "C", True)
    pdf.cell(25, 8, "Valor", 1, 0, "R", True)
    pdf.cell(30, 8, "Saldo Ac.", 1, 1, "R", True)
    saldo_acum = 0
    for _, row in df_filtrado.sort_values('DT').iterrows():
        saldo_acum += row['V_Final']
        pdf.set_font("Arial", "", 8)
        pdf.cell(20, 7, str(row['Data']), 1)
        pdf.cell(75, 7, str(row['Descrição'])[:45], 1)
        pdf.cell(25, 7, str(row['Banco']), 1)
        pdf.cell(25, 7, m_fmt(row['V_Num']), 1, 0, "R")
        pdf.cell(30, 7, m_fmt(saldo_acum), 1, 1, "R")
    return pdf.output(dest="S").encode("latin-1")

# --- 3. BARRA LATERAL (SIMPLES E FIXA) ---
st.sidebar.title("🎮 FinançasPro Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Geral & Busca", "🏦 Bancos", "🐾 Milo & Bolt", "🚗 Veículo", "🖨️ PDF"])

st.sidebar.divider()
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", 0.0)
        f_des = st.text_input("Descrição")
        f_cat = st.selectbox("Tag", ["Mercado", "Obra", "Pet: Milo", "Pet: Bolt", "Veículo", "Lazer", "Contas Fixas"])
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        f_st = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("LANÇAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), f"{f_val:.2f}".replace('.', ','), f_des, f_cat, f_tip, f_bnc, f_st])
            st.cache_data.clear(); st.rerun()

# --- 4. TELAS (VOLTANDO AO QUE FUNCIONA) ---

if aba == "💰 Geral & Busca":
    st.title("💰 Controle Geral")
    
    # Busca por texto (Filtra tudo na hora)
    pesquisa = st.text_input("🔍 O que você quer encontrar? (Ex: mercado, cimento, vacina...)")
    df_f = df_base[df_base.apply(lambda r: pesquisa.lower() in r.astype(str).str.lower().values, axis=1)] if pesquisa else df_base
    
    col1, col2 = st.columns(2)
    col1.metric("Saldo Geral", m_fmt(df_base['V_Final'].sum()))
    col2.metric("Lançamentos Filtrados", len(df_f))
    
    st.divider()
    st.dataframe(df_f.sort_values('DT', ascending=False), 
                 column_order=["Data", "Descrição", "Valor", "Banco", "Status"], 
                 use_container_width=True, hide_index=True)

elif aba == "🏦 Bancos":
    st.title("🏦 Saldo nos Bancos")
    if not df_base.empty:
        bancos = df_base.groupby('Banco')['V_Final'].sum().reset_index()
        for i, row in bancos.iterrows():
            st.write(f"**{row['Banco']}:** {m_fmt(row['V_Final'])}")
        st.divider()
        b_sel = st.selectbox("Ver extrato de:", bancos['Banco'].unique())
        st.dataframe(df_base[df_base['Banco'] == b_sel].sort_values('DT', ascending=False), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.metric("Total Gasto Pets", m_fmt(df_p['V_Num'].sum()))
    st.dataframe(df_p.sort_values('DT', ascending=False), column_order=["Data", "Descrição", "Valor", "Status"], hide_index=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Meu Veículo")
    v1, v2 = st.columns(2)
    alc = v1.number_input("Álcool", 0.0)
    gas = v2.number_input("Gasolina", 0.0)
    if gas > 0:
        if alc/gas <= 0.7: st.success("✅ ÁLCOOL")
        else: st.warning("⛽ GASOLINA")

elif aba == "🖨️ PDF":
    st.title("🖨️ Relatório")
    d1 = st.date_input("De:", datetime.now() - relativedelta(days=30))
    d2 = st.date_input("Até:", datetime.now())
    st_sel = st.selectbox("Status", ["Todos", "Pago", "Pendente"])
    
    df_pdf = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    if st_sel != "Todos": df_pdf = df_pdf[df_pdf['Status'] == st_sel]
    
    if st.button("GERAR PDF"):
        pdf_bytes = gerar_pdf(df_pdf, f"{d1} a {d2}")
        st.download_button("📥 Baixar PDF", pdf_bytes, "Relatorio.pdf")
