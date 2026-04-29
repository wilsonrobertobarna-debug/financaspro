import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import plotly.express as px

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v7.0", layout="wide", page_icon="💰")

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

# --- 2. GERADOR DE PDF (COM SALDO ACUMULADO) ---
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
    pdf.cell(70, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(25, 8, "Banco", 1, 0, "C", True)
    pdf.cell(20, 8, "Status", 1, 0, "C", True)
    pdf.cell(25, 8, "Valor", 1, 0, "R", True)
    pdf.cell(30, 8, "Saldo Ac.", 1, 1, "R", True)
    saldo_acum = 0
    for _, row in df_filtrado.sort_values('DT').iterrows():
        saldo_acum += row['V_Final']
        pdf.set_font("Arial", "", 8)
        pdf.cell(20, 7, str(row['Data']), 1)
        pdf.cell(70, 7, str(row['Descrição'])[:40], 1)
        pdf.cell(25, 7, str(row['Banco']), 1)
        pdf.cell(20, 7, str(row['Status']), 1)
        pdf.cell(25, 7, m_fmt(row['V_Num']), 1, 0, "R")
        pdf.cell(30, 7, m_fmt(saldo_acum), 1, 1, "R")
    return pdf.output(dest="S").encode("latin-1")

# --- 3. MENU LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["📊 Dashboard & Metas", "🏦 Saldos por Banco", "🐾 Milo & Bolt", "🚗 Veículo", "🖨️ Relatório PDF"])

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

with st.sidebar.expander("🗑️ Excluir Registro"):
    if not df_base.empty:
        opcoes = [f"{r['ID_Planilha']} | {r['Data']} | {r['Descrição']}" for _, r in df_base.tail(10).iloc[::-1].iterrows()]
        sel_del = st.selectbox("Escolha:", [""] + opcoes)
        if sel_del and st.button("CONFIRMAR EXCLUSÃO"):
            ws.delete_rows(int(sel_del.split(" | ")[0]))
            st.cache_data.clear(); st.rerun()

# --- 4. TELAS ---

if aba == "📊 Dashboard & Metas":
    st.title("📊 Painel e Pesquisa Global")
    busca = st.text_input("🔍 Pesquisar (ex: nome do mercado, peça da obra...)")
    df_f = df_base[df_base.apply(lambda r: busca.lower() in r.astype(str).str.lower().values, axis=1)] if busca else df_base
    
    c1, c2 = st.columns([2, 1])
    with c1:
        st.subheader("Tags de Gastos")
        if not df_f.empty:
            fig = px.pie(df_f[df_f['V_Final'] < 0], values='V_Num', names='Categoria')
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        st.subheader("🎯 Metas")
        meta = 5000.0
        gasto = abs(df_f[df_f['V_Final'] < 0]['V_Num'].sum())
        st.write(f"Gasto Atual: {m_fmt(gasto)}")
        st.progress(min(gasto/meta, 1.0))

    st.divider()
    st.dataframe(df_f.sort_values('DT', ascending=False), 
                 column_order=["Data", "Descrição", "Valor", "Categoria", "Banco", "Status"], 
                 use_container_width=True, hide_index=True)

elif aba == "🏦 Saldos por Banco":
    st.title("🏦 Meus Bancos")
    if not df_base.empty:
        bancos = df_base.groupby('Banco')['V_Final'].sum().reset_index()
        cols = st.columns(len(bancos) if len(bancos) > 0 else 1)
        for i, row in bancos.iterrows():
            cols[i % len(cols)].metric(row['Banco'], m_fmt(row['V_Final']))
        st.divider()
        st.subheader("Extrato por Banco")
        b_sel = st.selectbox("Selecione o Banco:", bancos['Banco'].unique())
        st.dataframe(df_base[df_base['Banco'] == b_sel].sort_values('DT', ascending=False), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Cantinho do Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.metric("Total Gasto com os Pets", m_fmt(df_p['V_Num'].sum()))
    st.dataframe(df_p.sort_values('DT', ascending=False), column_order=["Data", "Descrição", "Valor", "Status"], hide_index=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Gestão Veicular")
    v1, v2 = st.columns(2)
    alc = v1.number_input("Álcool", 0.0)
    gas = v2.number_input("Gasolina", 0.0)
    if gas > 0:
        if alc/gas <= 0.7: st.success("✅ Vá de ÁLCOOL")
        else: st.warning("⛽ Vá de GASOLINA")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_v.sort_values('DT', ascending=False), use_container_width=True, hide_index=True)

elif aba == "🖨️ Relatório PDF":
    st.title("🖨️ Gerador de Relatório Profissional")
    ca, cb, cc = st.columns(3)
    d1 = ca.date_input("De:", datetime.now() - relativedelta(days=30))
    d2 = cb.date_input("Até:", datetime.now())
    st_sel = cc.selectbox("Filtrar Status", ["Todos", "Pago", "Pendente"])
    
    df_pdf = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    if st_sel != "Todos": df_pdf = df_pdf[df_pdf['Status'] == st_sel]
    
    if st.button("🔥 BAIXAR RELATÓRIO PDF"):
        pdf_res = gerar_pdf(df_pdf, f"{d1} a {d2}")
        st.download_button("📥 Baixar Agora", pdf_res, f"Extrato_Wilson_{datetime.now().strftime('%d_%m')}.pdf")
