import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import base64

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v3.4", layout="wide")

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
    # Ajuste do sinal conforme o tipo
    df['V_Final'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. FUNÇÃO GERADORA DE PDF ---
def gerar_pdf(df_filtrado, periodo_txt):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, "RELATÓRIO FINANCEIRO - WILSON", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Periodo: {periodo_txt}", ln=True, align="C")
    pdf.ln(5)
    
    # Cabeçalho da Tabela
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Data", 1, 0, "C", True)
    pdf.cell(85, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(30, 8, "Banco", 1, 0, "C", True)
    pdf.cell(25, 8, "Valor", 1, 0, "R", True)
    pdf.cell(25, 8, "Saldo Dia", 1, 1, "R", True)
    
    pdf.set_font("Arial", "", 8)
    
    # Lógica de Saldo Diário
    df_pdf = df_filtrado.sort_values('DT')
    datas = df_pdf['DT'].unique()
    
    for d in datas:
        data_str = pd.to_datetime(d).strftime('%d/%m/%Y')
        itens_dia = df_pdf[df_pdf['DT'] == d]
        saldo_dia = 0
        
        for idx, row in itens_dia.iterrows():
            pdf.cell(25, 7, data_str, 1)
            pdf.cell(85, 7, str(row['Descrição'])[:50], 1)
            pdf.cell(30, 7, str(row['Banco']), 1)
            cor = (0, 128, 0) if row['V_Final'] > 0 else (150, 0, 0)
            pdf.set_text_color(*cor)
            pdf.cell(25, 7, m_fmt(row['V_Num']), 1, 0, "R")
            pdf.set_text_color(0, 0, 0)
            pdf.cell(25, 7, "", 1, 1) # Vazio enquanto não termina o dia
            saldo_dia += row['V_Final']
            
        # Linha de Saldo Diário
        pdf.set_fill_color(240, 240, 240)
        pdf.set_font("Arial", "B", 8)
        pdf.cell(140, 7, f"SALDO DO DIA {data_str}:", 1, 0, "R", True)
        pdf.cell(25, 7, "", 1, 0, "R", True)
        pdf.cell(25, 7, m_fmt(saldo_dia), 1, 1, "R", True)
        pdf.set_font("Arial", "", 8)
        pdf.ln(1)
        
    return pdf.output(dest="S").encode("latin-1")

# --- 3. INTERFACE ---
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📄 Relatório WhatsApp", "✏️ Exportar PDF", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# (Mantenha aqui os Expanders da barra lateral de Novo Lançamento, TR e Exclusão da v3.3)

if aba == "✏️ Exportar PDF":
    st.title("🖨️ Gerador de PDF Profissional")
    
    col1, col2, col3 = st.columns(3)
    d_ini = col1.date_input("De:", datetime.now() - relativedelta(days=30))
    d_fim = col2.date_input("Até:", datetime.now())
    banco_sel = col3.selectbox("Filtrar Banco:", ["Todos"] + list(df_base['Banco'].unique()))
    
    busca = st.text_input("Filtrar por Descrição (ex: Mercado, Obra, Milo):")
    
    # Aplicação dos Filtros
    df_f = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    if banco_sel != "Todos":
        df_f = df_f[df_f['Banco'] == banco_sel]
    if busca:
        df_f = df_f[df_f['Descrição'].str.contains(busca, case=False, na=False)]
        
    if not df_f.empty:
        st.subheader(f"📊 Prévia: {len(df_f)} lançamentos encontrados")
        st.dataframe(df_f.sort_values('DT'), use_container_width=True)
        
        pdf_bytes = gerar_pdf(df_f, f"{d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}")
        
        st.download_button(
            label="📥 BAIXAR RELATÓRIO EM PDF",
            data=pdf_bytes,
            file_name=f"Relatorio_Wilson_{datetime.now().strftime('%d_%m')}.pdf",
            mime="application/pdf"
        )
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

# (Mantenha as outras abas de Finanças, Pets e Veículo como na v3.3)
