import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="FinançasPro Wilson v3.6", layout="wide")

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

# --- 2. GERADOR DE PDF PROFISSIONAL ---
def gerar_pdf(df_filtrado, periodo_txt):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, "EXTRATO FINANCEIRO - WILSON", ln=True, align="C")
    pdf.set_font("Arial", "", 9)
    pdf.cell(190, 7, f"Periodo: {periodo_txt}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho Otimizado
    pdf.set_fill_color(220, 220, 220)
    pdf.set_font("Arial", "B", 8)
    pdf.cell(20, 8, "Data", 1, 0, "C", True)
    pdf.cell(70, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(25, 8, "Banco", 1, 0, "C", True)
    pdf.cell(20, 8, "Status", 1, 0, "C", True)
    pdf.cell(25, 8, "Valor", 1, 0, "R", True)
    pdf.cell(30, 8, "Saldo Acum.", 1, 1, "R", True)
    
    pdf.set_font("Arial", "", 8)
    saldo_acum = 0
    df_pdf = df_filtrado.sort_values('DT')
    
    for _, row in df_pdf.iterrows():
        saldo_acum += row['V_Final']
        pdf.cell(20, 7, row['Data'], 1, 0, "C")
        pdf.cell(70, 7, str(row['Descrição'])[:40], 1)
        pdf.cell(25, 7, str(row['Banco']), 1, 0, "C")
        pdf.cell(20, 7, str(row['Status']), 1, 0, "C")
        
        if row['V_Final'] > 0: pdf.set_text_color(0, 128, 0)
        else: pdf.set_text_color(200, 0, 0)
        
        pdf.cell(25, 7, m_fmt(row['V_Num']), 1, 0, "R")
        pdf.set_text_color(0, 0, 0)
        pdf.cell(30, 7, m_fmt(saldo_acum), 1, 1, "R")
        
    return pdf.output(dest="S").encode("latin-1")

# --- 3. BARRA LATERAL (AÇÕES FIXAS) ---
st.sidebar.title("🎮 Menu Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Extrato Geral", "🐾 Milo & Bolt", "🚗 Veículo", "🖨️ Gerar PDF", "✏️ Editar Item"])

st.sidebar.divider()

with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_des = st.text_input("O que comprou?")
        f_cat = st.selectbox("Categoria", ["Mercado", "Obra", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        f_st = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("LANÇAR AGORA"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, "Despesa", f_bnc, f_st])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("🗑️ Apagar Registro"):
    if not df_base.empty:
        opcoes = [f"{r['ID_Planilha']} | {r['Data']} | {r['Descrição']}" for _, r in df_base.tail(10).iloc[::-1].iterrows()]
        sel_del = st.selectbox("Selecione:", [""] + opcoes)
        if sel_del and st.button("APAGAR DEFINITIVO"):
            ws.delete_rows(int(sel_del.split(" | ")[0]))
            st.cache_data.clear(); st.rerun()

# --- 4. TELAS ---

# Colunas que queremos mostrar para o Wilson (Esconde as técnicas)
COLUNAS_VISIVEIS = ["Data", "Descrição", "Valor", "Categoria", "Banco", "Status"]

if aba == "💰 Extrato Geral":
    st.title("🛡️ Seu Dinheiro")
    if not df_base.empty:
        c1, c2 = st.columns(2)
        c1.metric("Saldo em Conta", m_fmt(df_base['V_Final'].sum()))
        pendente = df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()
        c2.metric("Total Pendente", m_fmt(pendente), delta_color="inverse")
        
        st.dataframe(df_base.sort_values('DT', ascending=False), 
                     column_order=COLUNAS_VISIVEIS, use_container_width=True, hide_index=True)

elif aba == "🖨️ Gerar PDF":
    st.title("🖨️ Relatório para Impressão")
    with st.container(border=True):
        col1, col2 = st.columns(2)
        d1 = col1.date_input("De:", datetime.now() - relativedelta(days=30))
        d2 = col2.date_input("Até:", datetime.now())
        
        col3, col4 = st.columns(2)
        b_sel = col3.selectbox("Filtrar Banco", ["Todos"] + list(df_base['Banco'].unique()))
        s_sel = col4.selectbox("Filtrar Status", ["Todos", "Pago", "Pendente"])
    
    df_f = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)].copy()
    if b_sel != "Todos": df_f = df_f[df_f['Banco'] == b_sel]
    if s_sel != "Todos": df_f = df_f[df_f['Status'] == s_sel]
    
    if not df_f.empty:
        st.dataframe(df_f.sort_values('DT'), column_order=COLUNAS_VISIVEIS, hide_index=True)
        if st.button("🔥 GERAR E BAIXAR PDF"):
            pdf_bytes = gerar_pdf(df_f, f"{d1.strftime('%d/%m/%Y')} a {d2.strftime('%d/%m/%Y')}")
            st.download_button("📥 Clique aqui para Baixar", pdf_bytes, "Relatorio_Wilson.pdf", "application/pdf")

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Painel Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.metric("Total Gasto com os Meninos", m_fmt(df_p['V_Num'].sum()))
    st.dataframe(df_p.sort_values('DT', ascending=False), column_order=COLUNAS_VISIVEIS, hide_index=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_v.sort_values('DT', ascending=False), column_order=COLUNAS_VISIVEIS, hide_index=True)

elif aba == "✏️ Editar Item":
    st.title("✏️ Ajustar Lançamento")
    id_e = st.number_input("Digite o ID do item (visto no Extrato Geral):", min_value=2, step=1)
    it = df_base[df_base['ID_Planilha'] == id_e]
    if not it.empty:
        with st.form("edit_form"):
            new_desc = st.text_input("Descrição", it['Descrição'].iloc[0])
            new_val = st.number_input("Valor", float(it['V_Num'].iloc[0]))
            new_st = st.selectbox("Status", ["Pago", "Pendente"], index=0 if it['Status'].iloc[0] == "Pago" else 1)
            if st.form_submit_button("ATUALIZAR"):
                ws.update_cell(id_e, 2, f"{new_val:.2f}".replace('.', ','))
                ws.update_cell(id_e, 3, new_desc)
                ws.update_cell(id_e, 7, new_st)
                st.cache_data.clear(); st.success("Atualizado!"); st.rerun()
