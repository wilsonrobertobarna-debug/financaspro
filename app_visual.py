# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 1.6
# STATUS: SISTEMA COMPLETO (Bancos, Cartões, Gráficos, Metas e PDF)

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
st.sidebar.markdown(f"**Versão:** `V 1.6`")

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

# --- BUSCA DINÂMICA DE BANCOS E CARTÕES ---
def p_float_limpo(v):
    try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
    except: return 0.0

try:
    ws_bancos = sh.worksheet("Bancos")
    dados_bancos = ws_bancos.get_all_records()
    df_config_bancos = pd.DataFrame(dados_bancos)
    for col in ['Bancos', 'saldo', 'tipo da conta', 'fechamento', 'vencto']:
        if col not in df_config_bancos.columns: df_config_bancos[col] = ""
    lista_final_bancos = df_config_bancos['Bancos'].astype(str).tolist()
except:
    lista_final_bancos = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"]
    df_config_bancos = pd.DataFrame()

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    df['V_Num'] = df['Valor'].apply(p_float_limpo)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📄 Relatórios", "📋 Relatório PDF"])
st.sidebar.divider()

# FORMULÁRIO DE LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Lazer"])
        f_bnc = st.selectbox("Banco/Cartão", lista_final_bancos)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Cartões
        if not df_config_bancos.empty:
            cartoes = df_config_bancos[df_config_bancos['tipo da conta'].astype(str).str.lower() == 'cartão']
            if not cartoes.empty:
                st.subheader("💳 Limites")
                cols_c = st.columns(len(cartoes))
                for idx, row_c in cartoes.reset_index().iterrows():
                    gasto_c = df_base[(df_base['Banco'] == row_c['Bancos']) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
                    limite = p_float_limpo(row_c['saldo'])
                    cols_c[idx].metric(row_c['Bancos'], m_fmt(limite - gasto_c), f"Limite {m_fmt(limite)}")
        
        # Dashboard
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        st.info(f"### 🏦 Saldo Geral: {m_fmt(df_base[df_base['Tipo'] != 'Despesa']['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum())}")
        
        # Metas
        with st.expander("🎯 Metas do Mês"):
            todas_cats = sorted(df_base['Categoria'].unique())
            metas_map = {cat: st.number_input(f"Meta {cat}", value=500.0) for cat in todas_cats}
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', hole=0.4, title="Gastos"), use_container_width=True)
        with g2:
            fig_m = go.Figure()
            df_real = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            fig_m.add_trace(go.Bar(x=df_real['Categoria'], y=df_real['V_Num'], name='Real', marker_color='#e74c3c'))
            st.plotly_chart(fig_m, use_container_width=True)

        # Busca
        st.subheader("🔍 Lançamentos")
        c1, c2 = st.columns(2)
        s_bnc = c1.multiselect("Banco:", lista_final_bancos)
        b_desc = c2.text_input("Buscar:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Gestão Wilson")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Álcool", value=0.0)
    gas = c2.number_input("Gasolina", value=0.0)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("⛽ ABASTEÇA COM ÁLCOOL")
        else: c3.warning("⛽ ABASTEÇA COM GASOLINA")
    df_car = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível'])]
    st.dataframe(df_car.iloc[::-1], use_container_width=True)

elif aba == "📋 Relatório PDF":
    st.title("📋 Gerar PDF")
    c1, c2 = st.columns(2)
    b_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1))
    b_fim = c2.date_input("Fim", datetime.now())
    df_pdf = df_base[(df_base['DT'].dt.date >= b_ini) & (df_base['DT'].dt.date <= b_fim)]
    st.write(f"Encontrados: {len(df_pdf)}")
    if st.button("📄 BAIXAR PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "Relatorio Wilson", 0, 1, 'C')
        for _, row in df_pdf.iterrows():
            pdf.set_font("Arial", '', 10)
            pdf.cell(190, 8, f"{row['Data']} - {row['Descrição']} - R$ {row['Valor']}", 1, 1)
        st.download_button("📥 Clique aqui", pdf.output(dest='S').encode('latin-1','replace'), "relatorio.pdf")

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Rápido")
    # (Código de resumo para WhatsApp)
    st.write("Filtre as datas e copie o texto para enviar.")
