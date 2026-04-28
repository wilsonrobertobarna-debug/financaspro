import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
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

# 3. CARREGAMENTO E FUNÇÕES DE APOIO
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
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf_extrato(df, banco, p_ini, p_fim):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"EXTRATO BANCARIO - {banco}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Periodo: {p_ini.strftime('%d/%m/%Y')} ate {p_fim.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Data", 1, 0, "C", True)
    pdf.cell(80, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(40, 8, "Valor", 1, 0, "R", True)
    pdf.cell(45, 8, "Saldo", 1, 1, "R", True)
    
    pdf.set_font("Arial", "", 8)
    for _, r in df.iloc[::-1].iterrows():
        pdf.cell(25, 7, str(r['Data']), 1, 0, "C")
        pdf.cell(80, 7, str(r['Descrição'])[:45], 1, 0, "L")
        pdf.cell(40, 7, r['Valor Item'], 1, 0, "R")
        pdf.cell(45, 7, r['Saldo'], 1, 1, "R")
    
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
    f_bnc = st.selectbox("Banco/Cartão", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
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

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.metric("Total Acumulado Pets", m_fmt(df_pets['V_Num'].sum()))
    st.dataframe(df_pets[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Banco', 'Status']].iloc[::-1])

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Diário")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    data_ini = col1.date_input("Início", datetime.now().replace(day=1))
    data_fim = col2.date_input("Fim", datetime.now())
    busca = col3.text_input("Filtrar Descrição:")

    b_sel = st.selectbox("Escolha o Banco:", sorted(df_base['Banco'].unique()))
    
    # Processamento do Extrato
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b = df_b[(df_b['DT'].dt.date >= data_ini) & (df_b['DT'].dt.date <= data_fim)]
    if busca:
        df_b = df_b[df_b['Descrição'].str.contains(busca, case=False, na=False)]

    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Valor Item'] = df_b.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] == 'Despesa' else m_fmt(r['V_Num']), axis=1)
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    
    # Botões de Ação
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        pdf_data = gerar_pdf_extrato(df_b, b_sel, data_ini, data_fim)
        st.download_button("📄 BAIXAR EXTRATO PDF", pdf_data, f"extrato_{b_sel}.pdf", "application/pdf", use_container_width=True)
    with c_btn2:
        link_zap_ext = f"https://wa.me/?text={urllib.parse.quote('Wilson, segue extrato do banco ' + b_sel)}"
        st.markdown(f"""<a href="{link_zap_ext}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:10px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;">📲 NOTIFICAR VIA WHATSAPP</button></a>""", unsafe_allow_html=True)
    
    st.table(df_b[['Data', 'Descrição', 'Tipo', 'Valor Item', 'Saldo', 'Status']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Detalhado")
    d1, d2 = st.columns(2)
    ini = d1.date_input("Início Período", datetime.now().replace(day=1))
    fim = d2.date_input("Fim Período", datetime.now())
    
    df_p = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    
    rec = df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum()
    des = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
    rend = df_p[df_p['Tipo'] == 'Rendimento']['V_Num'].sum()
    pend = df_p[df_p['Status'] == 'Pendente']['V_Num'].sum()
    
    saldos_txt = ""
    total_pat = 0
    for b in sorted(df_base['Banco'].unique()):
        s = df_base[df_base['Banco'] == b]['V_Real'].sum()
        saldos_txt += f"- {b}: {m_fmt(s)}\n"
        total_pat += s

    relat = f"--- RELATÓRIO WILSON ---\nPeríodo: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n"
    relat += f"==========================\n📈 REC: {m_fmt(rec)}\n📉 DES: {m_fmt(-des)}\n💰 REND: {m_fmt(rend)}\n⏳ PEND: {m_fmt(pend)}\n💵 SOBRA: {m_fmt(df_p['V_Real'].sum())}\n"
    relat += f"==========================\n🏦 SALDO POR BANCOS:\n{saldos_txt}==========================\n🏦 PATRIMÔNIO: {m_fmt(total_pat)}"
    
    st.text_area("Relatório Wilson:", relat, height=350)
    link_zap = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f"""<a href="{link_zap}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:15px;border:none;border-radius:10px;font-weight:bold;cursor:pointer;">📲 ENVIAR PARA WHATSAPP</button></a>""", unsafe_allow_html=True)
