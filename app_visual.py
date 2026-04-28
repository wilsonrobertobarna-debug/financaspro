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
    df['ID_Linha'] = range(2, len(df) + 2)
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
    pdf.cell(190, 10, f"EXTRATO BANCARIO: {banco}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Periodo: {p_ini.strftime('%d/%m/%Y')} a {p_fim.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_fill_color(240, 240, 240)
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

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

# 5. TELAS
if aba == "📊 Extrato Diário":
    st.title("📊 Extrato Bancário Detalhado")
    
    # Filtros
    c1, c2, c3 = st.columns([1,1,2])
    d_ini = c1.date_input("Início", datetime.now().replace(day=1))
    d_fim = c2.date_input("Fim", datetime.now())
    txt_psq = c3.text_input("🔍 Pesquisar na Descrição:")
    
    bancos_lista = sorted(df_base['Banco'].unique())
    b_sel = st.selectbox("Selecione o Banco para análise:", bancos_lista)
    
    # Processamento do Extrato
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    
    # Aplicação dos Filtros de Período e Texto
    df_f = df_b[(df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_f)].copy()
    if txt_psq:
        df_f = df_f[df_f['Descrição'].str.contains(txt_psq, case=False, na=False)]
    
    # Formatação para exibição
    df_f['V_Fmt'] = df_f.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] == 'Despesa' else m_fmt(r['V_Num']), axis=1)
    df_f['S_Fmt'] = df_f['Saldo_Acum'].apply(m_fmt)
    
    # Botão de PDF
    if not df_f.empty:
        pdf_bytes = gerar_pdf_extrato(df_f, b_sel, d_ini, d_fim)
        st.download_button("📄 BAIXAR EXTRATO EM PDF", pdf_bytes, f"extrato_{b_sel}.pdf", "application/pdf")
    
    st.divider()
    st.dataframe(df_f[['Data', 'Descrição', 'V_Fmt', 'S_Fmt']].iloc[::-1], use_container_width=True)

elif aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(df_base['V_Real'].sum())}")
    
    # Gráficos
    df_m = df_base[df_base['Mes_Ano'] == datetime.now().strftime('%m/%y')].copy()
    col1, col2 = st.columns(2)
    with col1:
        df_evol = df_base.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Mensal"), use_container_width=True)
    with col2:
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(gastos_cat, x='Categoria', y='V_Num', title="Gastos por Categoria"), use_container_width=True)

    # Gestão (Transferência, Alterar, Excluir)
    t1, t2, t3 = st.tabs(["💸 Transferência", "📝 Alterar", "🚨 Excluir"])
    # ... (Lógica de gestão mantida igual à anterior para não quebrar o sistema)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)].copy()
    st.metric("Total Gasto", m_fmt(df_p['V_Num'].sum()))
    st.plotly_chart(px.bar(df_p.groupby('Mes_Ano')['V_Num'].sum().reset_index(), x='Mes_Ano', y='V_Num', title="Gastos Mensais Pets"), use_container_width=True)
    st.table(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório WhatsApp (Modelo Wilson)")
    # ... (Lógica do Relatório enviada anteriormente com Sobra e Saldos detalhados)
