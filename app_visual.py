import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
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
        st.error(f"Erro de conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 2. FUNÇÕES DE SUPORTE
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    # ID_Linha para manter a ordem de inserção original
    df['ID_Linha'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento', 'Entrada'] else -r['V_Num'], axis=1)
    return df.sort_values(['DT', 'ID_Linha'])

def m_fmt(n): 
    if n == "" or pd.isna(n) or n == 0: return ""
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf(df, banco, p_ini, p_fim):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, f"EXTRATO: {banco}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 7, f"Periodo: {p_ini} a {p_fim}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho
    pdf.set_fill_color(230, 230, 230)
    cols = [("Data", 25), ("Descricao", 75), ("Tipo", 25), ("Valor", 30), ("Saldo", 35)]
    for txt, larg in cols:
        pdf.cell(larg, 8, txt, 1, 0, "C", True)
    pdf.ln()
    
    pdf.set_font("Arial", "", 9)
    for _, r in df.iterrows():
        pdf.cell(25, 7, str(r['Data']), 1, 0, "C")
        pdf.cell(75, 7, str(r['Descrição'])[:40], 1, 0, "L")
        pdf.cell(25, 7, str(r['Tipo']), 1, 0, "C")
        pdf.cell(30, 7, r['Valor_Exibir'], 1, 0, "R")
        pdf.cell(35, 7, r['Saldo_Exibir'], 1, 1, "R")
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()

# 3. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

if aba == "📊 Extrato Diário":
    st.title("📊 Extrato com Fechamento Diário")
    
    c1, c2, c3 = st.columns([1,1,2])
    d_ini = c1.date_input("Início", datetime.now().replace(day=1))
    d_fim_sel = c2.date_input("Fim", datetime.now())
    b_sel = st.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    
    # Filtro e Processamento
    df_b = df_base[df_base['Banco'] == b_sel].copy()
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    
    df_f = df_b[(df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_fim_sel)].copy()
    
    # Lógica de Fechamento: Identifica a ÚLTIMA linha (maior ID) de cada dia
    df_f['Ultima_Linha_Dia'] = False
    if not df_f.empty:
        idx_ultimas = df_f.groupby('Data')['ID_Linha'].idxmax()
        df_f.loc[idx_ultimas, 'Ultima_Linha_Dia'] = True
    
    # Formatação de campos
    df_f['Valor_Exibir'] = df_f.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['V_Real'] < 0 else m_fmt(r['V_Num']), axis=1)
    df_f['Saldo_Exibir'] = df_f.apply(lambda r: m_fmt(r['Saldo_Acum']) if r['Ultima_Linha_Dia'] else "", axis=1)

    if not df_f.empty:
        pdf_bytes = gerar_pdf(df_f, b_sel, d_ini.strftime('%d/%m/%Y'), d_fim_sel.strftime('%d/%m/%Y'))
        st.download_button("📥 Baixar PDF do Extrato", pdf_bytes, f"extrato_{b_sel}.pdf", "application/pdf")

    st.divider()
    
    # Função de Cores
    def aplicar_estilo(row):
        estilo = [''] * len(row)
        # Cor do Valor
        v_idx = row.index.get_loc('Valor_Exibir')
        estilo[v_idx] = 'color: red' if '-' in str(row['Valor_Exibir']) else 'color: green'
        
        # Cor do Saldo no fechamento
        s_idx = row.index.get_loc('Saldo_Exibir')
        if row['Ultima_Linha_Dia']:
            estilo[s_idx] = 'color: red; font-weight: bold' if row['Saldo_Acum'] < 0 else 'color: blue; font-weight: bold'
        return estilo

    # Exibição com Colunas Descrição e Tipo
    st.dataframe(
        df_f.iloc[::-1].style.apply(aplicar_estilo, axis=1),
        column_order=("Data", "Descrição", "Tipo", "Valor_Exibir", "Saldo_Exibir"),
        column_config={
            "Data": st.column_config.TextColumn("Data", width="small"),
            "Descrição": st.column_config.TextColumn("Descrição", width="large"),
            "Tipo": st.column_config.TextColumn("Tipo", width="medium"),
            "Valor_Exibir": st.column_config.TextColumn("Valor", width="medium"),
            "Saldo_Exibir": st.column_config.TextColumn("Saldo", width="medium"),
        },
        use_container_width=True, 
        hide_index=True
    )

elif aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    st.success(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(df_base['V_Real'].sum())}")

else:
    st.title(f"{aba}")
    st.info("Tela pronta para configuração de novos filtros.")
