# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 1.8
# STATUS: VISUAL SLIM + RELATÓRIOS COMPLETOS

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

# 4. SIDEBAR - NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📄 Relatórios", "📋 PDF"])
st.sidebar.divider()

# BARRINHA 1: NOVO (Tags curtas)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        c_f1, c_f2 = st.columns(2)
        f_dat = c_f1.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = c_f2.number_input("Valor", min_value=0.0, step=0.01)
        
        f_des = st.text_input("Descrição")
        
        c_f3, c_f4 = st.columns(2)
        f_tip = c_f3.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = c_f4.selectbox("Cat.", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Manutenção"])
        
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago"])
        
        c_f5, c_f6 = st.columns(2)
        f_sta = c_f5.selectbox("Status", ["Pago", "Pendente"])
        f_par = c_f6.number_input("Parc.", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# BARRINHA 2: TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferir", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_val = st.number_input("Valor", min_value=0.0)
        t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        t_dest = st.selectbox("Vai para:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
        if st.form_submit_button("EXECUTAR"):
            if t_orig != t_dest:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = datetime.now().strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, "Transferência", "Transf.", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, "Transferência", "Transf.", "Receita", t_dest, "Pago"])
                st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'] != 'Despesa']['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.subheader(f"🏦 Saldo: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        m1, m2, m3 = st.columns(3)
        m1.metric("Receitas", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', hole=0.4, title="Gastos"), use_container_width=True)
        with g2:
            fig_m = go.Figure()
            df_real = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            fig_m.add_trace(go.Bar(x=df_real['Categoria'], y=df_real['V_Num'], marker_color='#e74c3c'))
            fig_m.update_layout(title="Gastos por Categoria", height=300); st.plotly_chart(fig_m, use_container_width=True)

        st.subheader("🔍 Lançamentos")
        c1, c2 = st.columns([1,2])
        s_bnc = c1.multiselect("Banco:", sorted(df_base['Banco'].unique()))
        b_desc = c2.text_input("Busca rápida:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Pets")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Gasto do Mês", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
    st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Álcool", value=0.0)
    gas = c2.number_input("Gasolina", value=0.0)
    if alc > 0 and gas > 0:
        res = "⛽ ÁLCOOL" if (alc/gas) <= 0.7 else "⛽ GASOLINA"
        c3.info(f"Recomendação: {res}")
    st.dataframe(df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])].iloc[::-1], use_container_width=True)

elif "📄" in aba:
    st.title("📄 Relatório")
    d_ini = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d_fim = st.date_input("Fim", datetime.now())
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)]
    if not df_per.empty:
        relat = f"FINANÇAS WILSON\nREC: {m_fmt(df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum())}\nDES: {m_fmt(df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum())}"
        st.text_area("Relatório", relat, height=150)
        st.markdown(f'[📲 Enviar WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif "📋" in aba:
    st.title("📋 PDF")
    if st.button("Gerar Relatório Completo"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "FinançasPro Wilson", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        for _, r in df_base.tail(20).iterrows():
            pdf.cell(190, 8, f"{r['Data']} - {r['Descrição']} - R$ {r['Valor']}", 1, 1)
        st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1','replace'), "relatorio.pdf")
