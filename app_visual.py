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
            "private_key": pk, "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E FUNÇÕES
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
    df['Ano_Mes_Sort'] = df['DT'].dt.strftime('%Y-%m')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf_unico(df, banco, p_ini, p_fim):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"EXTRATO: {banco}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Periodo: {p_ini.strftime('%d/%m/%Y')} - {p_fim.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_fill_color(230, 230, 230)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Data", 1, 0, "C", True)
    pdf.cell(85, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(40, 8, "Valor", 1, 0, "R", True)
    pdf.cell(40, 8, "Saldo", 1, 1, "R", True)
    pdf.set_font("Arial", "", 8)
    for _, r in df.iloc[::-1].iterrows():
        pdf.cell(25, 7, str(r['Data']), 1, 0, "C")
        pdf.cell(85, 7, str(r['Descrição'])[:40], 1, 0, "L")
        pdf.cell(40, 7, r['V_Fmt'], 1, 0, "R")
        pdf.cell(40, 7, r['S_Fmt'], 1, 1, "R")
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (PROTEGIDO)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])
st.sidebar.divider()

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "XP", "Mercado Pago"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_dt = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
            ws_base.append_row([nova_dt, v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
    
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
    m2.metric("📉 Gasto", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
    m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
    m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        fig = px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Mensal")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(gastos_cat, x='Categoria', y='V_Num', title="Gastos por Categoria"), use_container_width=True)

    st.write("### 🔍 Pesquisar Lançamentos")
    p1, p2, p3 = st.columns([1, 1, 2])
    b_p = p1.selectbox("Banco:", ["Todos"] + sorted(df_base['Banco'].unique().tolist()))
    t_p = p2.selectbox("Tipo:", ["Todos", "Receita", "Despesa", "Rendimento"])
    d_p = p3.text_input("Descrição Wilson:")
    df_f = df_base.copy()
    if b_p != "Todos": df_f = df_f[df_f['Banco'] == b_p]
    if t_p != "Todos": df_f = df_f[df_f['Tipo'] == t_p]
    if d_p: df_f = df_f[df_f['Descrição'].str.contains(d_p, case=False, na=False)]
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Categoria']].iloc[::-1], use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato com Pesquisa")
    col1, col2, col3 = st.columns([1,1,2])
    d_ini = col1.date_input("Início", datetime.now().replace(day=1))
    d_fim = col2.date_input("Fim", datetime.now())
    txt_b = col3.text_input("🔍 Buscar na Descrição:")
    
    b_sel = st.selectbox("Selecione o Banco:", sorted(df_base['Banco'].unique()))
    
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b = df_b[(df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_fim)]
    if txt_b: df_b = df_b[df_b['Descrição'].str.contains(txt_b, case=False, na=False)]
    
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['V_Fmt'] = df_b.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] == 'Despesa' else m_fmt(r['V_Num']), axis=1)
    df_b['S_Fmt'] = df_b['Saldo_Acum'].apply(m_fmt)
    
    pdf_bytes = gerar_pdf_unico(df_b, b_sel, d_ini, d_fim)
    st.download_button("📄 BAIXAR EXTRATO PDF", pdf_bytes, f"extrato_{b_sel}.pdf", "application/pdf", use_container_width=True)
    
    st.table(df_b[['Data', 'Descrição', 'V_Fmt', 'S_Fmt']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Completo Wilson")
    r1, r2 = st.columns(2)
    ini_r = r1.date_input("Início", datetime.now().replace(day=1))
    fim_r = r2.date_input("Fim", datetime.now())
    
    df_r = df_base[(df_base['DT'].dt.date >= ini_r) & (df_base['DT'].dt.date <= fim_r)]
    rec = df_r[df_r['Tipo']=='Receita']['V_Num'].sum()
    des = df_r[df_r['Tipo']=='Despesa']['V_Num'].sum()
    rend = df_r[df_r['Tipo']=='Rendimento']['V_Num'].sum()
    pend = df_r[df_r['Status']=='Pendente']['V_Num'].sum()
    
    bancos_txt = ""
    for b in sorted(df_base['Banco'].unique()):
        s_b = df_base[df_base['Banco'] == b]['V_Real'].sum()
        bancos_txt += f"• {b}: {m_fmt(s_b)}\n"

    msg = (f"*Relatório Wilson*\n"
           f"📅 Período: {ini_r.strftime('%d/%m/%Y')} - {fim_r.strftime('%d/%m/%Y')}\n\n"
           f"✅ *RESUMO:*\n"
           f"➕ Receitas: {m_fmt(rec)}\n"
           f"➖ Despesas: {m_fmt(-des)}\n"
           f"💰 Rendimentos: {m_fmt(rend)}\n"
           f"⏳ Pendências: {m_fmt(pend)}\n\n"
           f"🏦 *SALDOS POR BANCO:*\n{bancos_txt}\n"
           f"💎 *PATRIMÔNIO:* {m_fmt(df_base['V_Real'].sum())}")
    
    st.text_area("Conteúdo do Relatório:", msg, height=350)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:15px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">📲 ENVIAR TUDO PARA WHATSAPP</button></a>', unsafe_allow_html=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.metric("Total Gasto", m_fmt(df_p['V_Num'].sum()))
    st.table(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])
