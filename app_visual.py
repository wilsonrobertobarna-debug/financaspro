# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 1.9
# STATUS: VISUAL SLIM + TAGS REDUZIDAS

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
st.sidebar.markdown(f"**Versão:** `V 1.9`")

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
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📄 Relatórios", "📋 PDF"])
st.sidebar.divider()

# BARRINHA 1: NOVO (Tags Curtas)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        c1, c2 = st.columns(2)
        f_dat = c1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = c2.number_input("Valor", min_value=0.0, step=0.01)
        
        f_des = st.text_input("Desc.")
        
        c3, c4 = st.columns(2)
        f_tip = c3.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = c4.selectbox("Cat.", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Manutenção"])
        
        f_bnc = st.selectbox("Bco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago"])
        
        c5, c6 = st.columns(2)
        f_sta = c5.selectbox("Status", ["Pago", "Pendente"])
        f_par = c6.number_input("Parc.", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# BARRINHA 2: TRANSFERIR
with st.sidebar.expander("💸 Transferir", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_val = st.number_input("Valor", min_value=0.0)
        t_orig = st.selectbox("Sai:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        t_dest = st.selectbox("Entra:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
        if st.form_submit_button("OK"):
            if t_orig != t_dest:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = datetime.now().strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, "Transf.", "Transf.", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, "Transf.", "Transf.", "Receita", t_dest, "Pago"])
                st.cache_data.clear(); st.rerun()

# 5. TELAS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo = df_base[df_base['Tipo'] != 'Despesa']['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.subheader(f"🏦 Saldo Geral: {m_fmt(saldo)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        m1, m2, m3 = st.columns(3)
        m1.metric("Rec.", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("Desp.", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("Pend.", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', hole=0.4, title="Gastos (%)"), use_container_width=True)
        with g2:
            df_g = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            fig = go.Figure(go.Bar(x=df_g['Categoria'], y=df_g['V_Num'], marker_color='#e74c3c'))
            fig.update_layout(title="Gastos/Cat", height=300); st.plotly_chart(fig, use_container_width=True)

        st.subheader("🔍 Busca")
        c1, c2 = st.columns([1,2])
        s_bnc = c1.multiselect("Bco:", sorted(df_base['Banco'].unique()))
        b_desc = c2.text_input("Busca:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Pets")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Gasto Mês", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
    st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Álcool", value=0.0)
    gas = c2.number_input("Gasolina", value=0.0)
    if alc > 0 and gas > 0:
        c3.info(f"Dica: {'⛽ ÁLCOOL' if (alc/gas) <= 0.7 else '⛽ GASOLINA'}")
    st.dataframe(df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])].iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba:
    st.title("📄 Relatório")
    d1 = st.date_input("De", datetime.now() - relativedelta(months=1))
    d2 = st.date_input("Até", datetime.now())
    df_per = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    if not df_per.empty:
        rel = f"WILSON: REC {m_fmt(df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum())} | DESP {m_fmt(df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum())}"
        st.text_area("Relatório Zap", rel, height=100)
        st.markdown(f'[📲 Enviar WhatsApp](https://wa.me/?text={urllib.parse.quote(rel)})')

elif "📋" in aba:
    st.title("📋 PDF")
    if st.button("Gerar PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(190, 10, "FinançasPro Wilson", 0, 1, 'C')
        for _, r in df_base.tail(20).iterrows():
            pdf.set_font("Arial", '', 9)
            pdf.cell(190, 7, f"{r['Data']} - {r['Descrição']} - R$ {r['Valor']}", 1, 1)
        st.download_button("📥 Baixar", pdf.output(dest='S').encode('latin-1','replace'), "relatorio.pdf")
