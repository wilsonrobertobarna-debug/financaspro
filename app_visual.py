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

# DIMINUIR O VALOR (Métricas)
st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

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
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO
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
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📲 WhatsApp", "📄 Relatório PDF"])

st.sidebar.divider()

# Formulários de entrada na Sidebar
with st.sidebar.expander("🚀 Novo", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parc.", min_value=1, value=1)
        f_des = st.text_input("Desc.")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Cat.", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Bco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("⚙️ Ajustar", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} | {r['Data']} | {r['Descrição']}": r for _, r in df_base.tail(20).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione:", [""] + list(lista_edit.keys()))
        if escolha:
            item = lista_edit[escolha]
            if st.button("🚨 EXCLUIR"):
                ws_base.delete_rows(int(item['ID']))
                st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("Despesas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        st.subheader("🔍 Lançamentos")
        st.dataframe(df_base[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Pets (Mês)", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.dataframe(df_pet[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    
    # VOLTA DO CÁLCULO DE COMBUSTÍVEL
    st.subheader("⛽ Álcool ou Gasolina?")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
    preco_alc = col_c1.number_input("Preço Álcool", min_value=0.0, step=0.01, format="%.2f")
    preco_gas = col_c2.number_input("Preço Gasolina", min_value=0.0, step=0.01, format="%.2f")
    
    if preco_alc > 0 and preco_gas > 0:
        resultado = preco_alc / preco_gas
        if resultado <= 0.7:
            col_c3.success(f"✅ VAI DE ÁLCOOL! (Proporção: {resultado:.2%})")
        else:
            col_c3.warning(f"✅ VAI DE GASOLINA! (Proporção: {resultado:.2%})")
    
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.subheader("Histórico do Veículo")
        st.dataframe(df_car[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

elif "📲" in aba:
    st.title("📲 WhatsApp")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("De", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = c2.date_input("Até", datetime.now(), format="DD/MM/YYYY")
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    if not df_per.empty:
        r_v = df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        rend_v = df_per[df_per['Tipo'] == 'Rendimento']['V_Num'].sum()
        relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n========================================\nREC: {m_fmt(r_v)}\nDES: {m_fmt(d_v)}\nREND: {m_fmt(rend_v)}\nSOBRA: {m_fmt((r_v+rend_v)-d_v)}"
        st.text_area("Cópia para WhatsApp", relat, height=300)
        st.markdown(f'[📲 Enviar via WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif "📄" in aba:
    st.title("📄 Relatório PDF")
    c1, c2 = st.columns(2)
    b_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY", key="pdf_ini")
    b_fim = c2.date_input("Fim", datetime.now(), format="DD/MM/YYYY", key="pdf_fim")
    
    if st.button("📄 GERAR PDF"):
        df_pdf = df_base[(df_base['DT'].dt.date >= b_ini) & (df_base['DT'].dt.date <= b_fim)]
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "FinançasPro - Relatório PDF", 0, 1, 'C')
        pdf.ln(10)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 8, "Data", 1); pdf.cell(100, 8, "Descricao", 1); pdf.cell(60, 8, "Valor", 1, 1)
        pdf.set_font("Arial", '', 9)
        for _, row in df_pdf.iterrows():
            pdf.cell(30, 7, str(row['Data']), 1); pdf.cell(100, 7, str(row['Descrição'])[:50], 1); pdf.cell(60, 7, f"R$ {row['Valor']}", 1, 1)
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 Baixar PDF", data=pdf_output, file_name="relatorio.pdf", mime="application/pdf")
