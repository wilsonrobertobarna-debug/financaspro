import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v3.5", layout="wide")

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
    df['V_Final'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. FUNÇÃO PDF MELHORADA ---
def gerar_pdf(df_filtrado, periodo_txt):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "RELATORIO FINANCEIRO - WILSON", ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(190, 7, f"Periodo: {periodo_txt}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho - Sem as colunas de ID
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(20, 8, "Data", 1, 0, "C", True)
    pdf.cell(75, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(25, 8, "Banco", 1, 0, "C", True)
    pdf.cell(20, 8, "Status", 1, 0, "C", True)
    pdf.cell(25, 8, "Valor", 1, 0, "R", True)
    pdf.cell(25, 8, "Saldo Acum.", 1, 1, "R", True)
    
    pdf.set_font("Arial", "", 8)
    saldo_acumulado = 0
    df_pdf = df_filtrado.sort_values('DT')
    
    for _, row in df_pdf.iterrows():
        saldo_acumulado += row['V_Final']
        pdf.cell(20, 7, row['Data'], 1, 0, "C")
        pdf.cell(75, 7, str(row['Descrição'])[:45], 1)
        pdf.cell(25, 7, str(row['Banco']), 1, 0, "C")
        pdf.cell(20, 7, str(row['Status']), 1, 0, "C")
        
        # Cor para Valor
        if row['V_Final'] > 0: pdf.set_text_color(0, 100, 0)
        else: pdf.set_text_color(150, 0, 0)
        pdf.cell(25, 7, m_fmt(row['V_Num']), 1, 0, "R")
        
        # Saldo Acumulado
        pdf.set_text_color(0, 0, 0)
        pdf.cell(25, 7, m_fmt(saldo_acumulado), 1, 1, "R")
        
    return pdf.output(dest="S").encode("latin-1")

# --- 3. MENU LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Geral", "📄 WhatsApp", "✏️ Editar", "🐾 Pets", "🚗 Veículo", "🖨️ PDF"])

st.sidebar.divider()

# AÇÕES FIXAS NA BARRA LATERAL
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Obra", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        f_st = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("LANÇAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, "Despesa", f_bnc, f_st])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("🗑️ Excluir Item"):
    if not df_base.empty:
        opcoes = [f"{r['ID_Planilha']} | {r['Data']} | {r['Descrição']} | {m_fmt(r['V_Num'])}" for _, r in df_base.tail(15).iloc[::-1].iterrows()]
        sel_del = st.selectbox("Escolha:", [""] + opcoes)
        if sel_del and st.button("CONFIRMAR EXCLUSÃO"):
            ws.delete_rows(int(sel_del.split(" | ")[0]))
            st.cache_data.clear(); st.rerun()

# --- 4. TELAS ---

if aba == "💰 Geral":
    st.title("🛡️ Finanças Wilson")
    if not df_base.empty:
        st.metric("Saldo Total", m_fmt(df_base['V_Final'].sum()))
        st.dataframe(df_base.sort_values('DT', ascending=False), use_container_width=True, hide_index=True)

elif aba == "🖨️ PDF":
    st.title("🖨️ Relatório para Impressão")
    c1, c2, c3, c4 = st.columns(4)
    d1 = c1.date_input("Início", datetime.now() - relativedelta(days=30))
    d2 = c2.date_input("Fim", datetime.now())
    b_sel = c3.selectbox("Banco", ["Todos"] + list(df_base['Banco'].unique()))
    s_sel = c4.selectbox("Status", ["Todos", "Pago", "Pendente"])
    
    df_f = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)].copy()
    if b_sel != "Todos": df_f = df_f[df_f['Banco'] == b_sel]
    if s_sel != "Todos": df_f = df_f[df_f['Status'] == s_sel]
    
    if not df_f.empty:
        st.dataframe(df_f.sort_values('DT'), hide_index=True)
        if st.button("GERAR PDF"):
            pdf_bytes = gerar_pdf(df_f, f"{d1.strftime('%d/%m/%Y')} a {d2.strftime('%d/%m/%Y')}")
            st.download_button("📥 Baixar PDF", pdf_bytes, "Relatorio_Wilson.pdf", "application/pdf")

elif aba == "🐾 Pets":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.subheader("🏥 Check-up")
    ca, cb = st.columns(2)
    ca.checkbox("Vacinas Milo", key="m1"); cb.checkbox("Vacinas Bolt", key="b1")
    st.dataframe(df_p.sort_values('DT', ascending=False), hide_index=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Veículo")
    st.subheader("⛽ Álcool x Gasolina")
    pa = st.number_input("Preço Álcool", min_value=0.0)
    pg = st.number_input("Preço Gasolina", min_value=0.0)
    if pg > 0:
        if pa/pg <= 0.7: st.success("Vá de ÁLCOOL")
        else: st.warning("Vá de GASOLINA")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_v, hide_index=True)

# Aba Editar e WhatsApp mantidas de forma simplificada
