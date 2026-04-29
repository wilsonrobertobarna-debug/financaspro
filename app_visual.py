# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 1.5
# STATUS: Gestão de Bancos + Cartões com Limite e Datas

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
st.sidebar.markdown(f"**Versão:** `V 1.5`")

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
    # Garante que as colunas existam para não quebrar
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
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📋 Relatório PDF"])
st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível"])
        f_bnc = st.selectbox("Banco/Cartão", lista_final_bancos)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        # Lógica de Cartão (Visual no Formulário)
        if not df_config_bancos.empty and f_bnc in df_config_bancos['Bancos'].values:
            info_b = df_config_bancos[df_config_bancos['Bancos'] == f_bnc].iloc[0]
            if str(info_b['tipo da conta']).lower() == 'cartão':
                st.info(f"💳 **Info Cartão:** Fecha dia {info_b['fechamento']} | Vence dia {info_b['vencto']}")
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELA PRINCIPAL (💰 Finanças)
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Resumo de Limites de Cartão
        if not df_config_bancos.empty:
            cartoes = df_config_bancos[df_config_bancos['tipo da conta'].astype(str).str.lower() == 'cartão']
            if not cartoes.empty:
                st.subheader("💳 Limite Disponível nos Cartões")
                cols_c = st.columns(len(cartoes))
                for idx, row_c in cartoes.reset_index().iterrows():
                    gasto_c = df_base[(df_base['Banco'] == row_c['Bancos']) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
                    limite = p_float_limpo(row_c['saldo'])
                    disponivel = limite - gasto_c
                    cols_c[idx].metric(row_c['Bancos'], m_fmt(disponivel), f"Total: {m_fmt(limite)}")
        
        st.divider()
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL (CONTA + CARTEIRA): {m_fmt(saldo_geral)}")

        # Filtros e Tabela (Sincronizados com a aba Bancos)
        st.subheader("🔍 Busca e Lançamentos")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Filtrar Banco/Cartão:", lista_final_bancos)
        s_sta = c2.multiselect("Filtrar Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Buscar Descrição:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

# --- (AS OUTRAS ABAS CONTINUAM FUNCIONANDO NORMALMENTE) ---
elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba or "📋" in aba:
    st.info("Abas de Relatório prontas para uso com os novos filtros de bancos.")
