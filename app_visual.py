import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO
@st.cache_resource
def conectar():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        pk = creds_info["private_key"].replace("\\n", "\n").strip()
        if pk.startswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": pk,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. DADOS SEM DUPLICAÇÃO
@st.cache_data(ttl=1)
def get_data():
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    
    df = pd.DataFrame(dados[1:], columns=dados[0])
    # Remove linhas totalmente vazias ou sem data
    df = df[df['Data'].str.strip() != ""].copy()
    
    def conv(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(conv)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = get_data()
mes_atual = datetime.now().strftime('%m/%y')

# 4. LANÇAMENTO (SIDEBAR)
st.sidebar.title("🚀 Lançar")
with st.sidebar.form("novo", clear_on_submit=True):
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Outros"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        # Salva formatando o valor corretamente para a planilha
        valor_str = f"{f_val:.2f}".replace('.', ',')
        sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), valor_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear()
        st.rerun()

# 5. TELA PRINCIPAL (TAGS -> GRÁFICOS -> PESQUISA)
st.title("🛡️ FinançasPro Wilson")

if not df_base.empty:
    df_mes = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    
    # --- TAGS (CORRIGIDAS) ---
    c1, c2, c3, c4 = st.columns(4)
    
    def fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

    c1.metric("📈 Receitas", fmt(df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()))
    c2.metric("📉 Despesas", fmt(df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()))
    c3.metric("💰 Rendimento", fmt(df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum()))
    c4.metric("⏳ Pendente", fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))

    st.divider()

    # --- GRÁFICOS ---
    g1, g2 = st.columns(2)
    with g1:
        df_p = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_p.empty:
            st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria"), use_container_width=True)
    with g2:
        df_b = df_mes.groupby('Tipo')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_b, x='Tipo', y='V_Num', color='Tipo', title="Fluxo do Mês"), use_container_width=True)

    st.divider()

    # --- PESQUISA E TABELA ---
    st.subheader("🔍 Lançamentos")
    f1, f2 = st.columns(2)
    sel_bnc = f1.multiselect("Filtrar Banco:", df_base['Banco'].unique())
    sel_sta = f2.multiselect("Filtrar Status:", ["Pago", "Pendente"])

    df_v = df_base.copy()
    if sel_bnc: df_v = df_v[df_v['Banco'].isin(sel_bnc)]
    if sel_sta: df_v = df_v[df_v['Status'].isin(sel_sta)]

    st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

# 6. GERENCIADOR (MENU LATERAL)
st.sidebar.divider()
if not df_base.empty:
    st.sidebar.subheader("⚙️ Ações")
    df_aux = df_base.copy()
    df_aux['ID'] = df_aux.index + 2
    lista = {f"L{r['ID']} | {r['Descrição']}": r['ID'] for _, r in df_aux.tail(10).iterrows()}
    escolha = st.sidebar.selectbox("Selecionar Linha:", [""] + list(lista.keys()))
    if escolha:
        if st.sidebar.button("🚨 APAGAR"):
            sh.get_worksheet(0).delete_rows(int(lista[escolha]))
            st.cache_data.clear(); st.rerun()
        if st.sidebar.button("✅ MARCAR COMO PAGO"):
            sh.get_worksheet(0).update_cell(int(lista[escolha]), 7, "Pago")
            st.cache_data.clear(); st.rerun()
