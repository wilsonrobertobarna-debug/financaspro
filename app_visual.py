import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF # Certifique-se de ter 'fpdf2' no requirements.txt

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

# 3. FUNÇÕES DE APOIO
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

def gerar_pdf_extrato(df, banco):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"Extrato Bancario - {banco}", ln=True, align="C")
    pdf.set_font("Arial", "B", 10)
    pdf.ln(5)
    # Cabeçalho
    pdf.cell(30, 10, "Data", 1)
    pdf.cell(80, 10, "Descricao", 1)
    pdf.cell(40, 10, "Valor", 1)
    pdf.cell(40, 10, "Saldo", 1)
    pdf.ln()
    # Dados
    pdf.set_font("Arial", "", 10)
    for _, row in df.iloc[::-1].iterrows():
        pdf.cell(30, 10, str(row['Data']), 1)
        pdf.cell(80, 10, str(row['Descrição'])[:40], 1)
        pdf.cell(40, 10, row['Valor Formatado'], 1)
        pdf.cell(40, 10, row['Saldo Diário'], 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "📄 Relatórios"])

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Bancário")
    b_sel = st.selectbox("Escolha o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Valor Formatado'] = df_b.apply(lambda r: f"-R$ {r['V_Num']:.2f}".replace('.', ',') if r['Tipo'] == 'Despesa' else f"R$ {r['V_Num']:.2f}".replace('.', ','), axis=1)
    
    df_b['Saldo Diário'] = df_b['Saldo_Acum'].apply(m_fmt)
    df_mostrar = df_b[['Data', 'Descrição', 'Tipo', 'Valor Formatado', 'Saldo Diário']].iloc[::-1]
    
    # Botão de PDF
    pdf_bytes = gerar_pdf_extrato(df_b, b_sel)
    st.download_button(label="📄 Baixar Extrato em PDF", data=pdf_bytes, file_name=f"extrato_{b_sel}.pdf", mime="application/pdf")
    
    st.table(df_mostrar)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    d1, d2 = st.columns(2)
    ini = d1.date_input("Início", datetime.now().replace(day=1))
    fim = d2.date_input("Fim", datetime.now())
    
    df_p = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    
    bancos_lista = sorted(df_base['Banco'].unique())
    saldos_txt = ""
    total_consolidado = 0
    for b in bancos_lista:
        s = df_base[df_base['Banco'] == b]['V_Real'].sum()
        saldos_txt += f"- {b}: {m_fmt(s)}\n"
        total_consolidado += s

    relat = f"RELATÓRIO WILSON\nPeríodo: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n"
    relat += "========================================\n"
    relat += f"REC: {m_fmt(df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum())}\n"
    relat += f"DES: {m_fmt(-df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum())}\n"
    relat += f"SOBRA: {m_fmt(df_p['V_Real'].sum())}\n"
    relat += "========================================\n\nSALDOS POR BANCO:\n"
    relat += saldos_txt
    relat += "========================================\n"
    relat += f"PATRIMÔNIO TOTAL: {m_fmt(total_consolidado)}\n" # ADICIONADO AQUI
    
    st.text_area("Copiar Relatório:", relat, height=400)
    zap_url = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f'''<a href="{zap_url}" target="_blank"><button style="width:100%; height:50px; background-color:#25D366; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">📲 ENVIAR PARA WHATSAPP</button></a>''', unsafe_allow_html=True)
