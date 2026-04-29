# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 1.7
# STATUS: RESTAURAÇÃO TOTAL + GESTÃO DE CARTÕES

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
st.sidebar.markdown(f"**Versão:** `V 1.7`")

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
    lista_final_bancos = df_config_bancos['Bancos'].astype(str).tolist()
except:
    lista_final_bancos = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"]
    df_config_bancos = pd.DataFrame()

# 3. CARREGAMENTO DE DADOS
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

# 4. SIDEBAR (PAINEL DE CONTROLE)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📋 Relatório PDF"])
st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco/Cartão", lista_final_bancos)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Resumo de Cartões
        if not df_config_bancos.empty:
            cartoes = df_config_bancos[df_config_bancos['tipo da conta'].astype(str).str.lower() == 'cartão']
            if not cartoes.empty:
                st.subheader("💳 Cartões e Limites")
                cols_c = st.columns(len(cartoes))
                for idx, row_c in cartoes.reset_index().iterrows():
                    gasto_c = df_base[(df_base['Banco'] == row_c['Bancos']) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
                    limite = p_float_limpo(row_c['saldo'])
                    cols_c[idx].metric(row_c['Bancos'], m_fmt(limite - gasto_c), f"Total: {m_fmt(limite)}")

        st.divider()
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        st.divider()
        with st.expander("🎯 Configurar Metas"):
            metas_map = {cat: st.number_input(f"Meta: {cat}", value=1000.0) for cat in sorted(df_base['Categoria'].unique())}
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo"), use_container_width=True)

        st.subheader("🔍 Busca e Lançamentos")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Banco:", lista_final_bancos)
        s_sta = c2.multiselect("Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Buscar:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Total Pets (Mês)", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0)
    gas = c2.number_input("Preço Gasolina", value=0.0)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("💡 ABASTEÇA COM ÁLCOOL")
        else: c3.warning("💡 ABASTEÇA COM GASOLINA")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Banco']].iloc[::-1], use_container_width=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Rápido Wilson")
    d_ini = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d_fim = st.date_input("Fim", datetime.now())
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)]
    if not df_per.empty:
        r_v = df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        saldos_txt = ""
        for b in lista_final_bancos:
            s = df_base[(df_base['Banco'] == b) & (df_base['Tipo'] != 'Despesa')]['V_Num'].sum() - df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
            saldos_txt += f"- {b}: {m_fmt(s)}\n"
        relat = f"RELATÓRIO WILSON\nREC: {m_fmt(r_v)}\nDES: {m_fmt(d_v)}\n\nSALDOS:\n{saldos_txt}"
        st.text_area("Texto para WhatsApp", relat, height=250)
        st.markdown(f'[📲 Enviar WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif aba == "📋 Relatório PDF":
    st.title("📋 Gerador de PDF Detalhado")
    c1, c2 = st.columns(2)
    b_ini = c1.date_input("Data Inicial", datetime.now() - relativedelta(months=1), key="pini")
    b_fim = c2.date_input("Data Final", datetime.now(), key="pfim")
    df_pdf = df_base[(df_base['DT'].dt.date >= b_ini) & (df_base['DT'].dt.date <= b_fim)]
    st.write(f"Lançamentos: {len(df_pdf)}")
    if st.button("📄 GERAR PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Relatorio Wilson", 0, 1, 'C')
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(30, 8, "Data", 1); pdf.cell(80, 8, "Descricao", 1); pdf.cell(40, 8, "Valor", 1); pdf.cell(40, 8, "Banco", 1); pdf.ln()
        pdf.set_font("Arial", '', 9)
        for _, r in df_pdf.iterrows():
            pdf.cell(30, 7, str(r['Data']), 1); pdf.cell(80, 7, str(r['Descrição'])[:35], 1); pdf.cell(40, 7, f"R$ {r['Valor']}", 1); pdf.cell(40, 7, str(r['Banco']), 1); pdf.ln()
        st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1', 'replace'), "relatorio.pdf")
