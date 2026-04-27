import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO COM LIMPEZA DE ESPAÇOS (BLINDAGEM)
@st.cache_resource
def conectar():
    # Tenta ler o dicionário de conexões
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    
    if not creds_dict:
        st.error("⚠️ Wilson, o Streamlit ainda não 'leu' seus segredos.")
        st.info("Dica: Clique em 'Reboot App' no painel do Streamlit Cloud para forçar a leitura.")
        st.stop()
        
    try:
        # Limpa possíveis espaços ou quebras de linha invisíveis
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        
        final_creds = {
            "type": creds_dict["type"],
            "project_id": creds_dict["project_id"],
            "private_key_id": creds_info["private_key_id"] if "private_key_id" in creds_dict else creds_dict.get("private_key_id"),
            "private_key": pk,
            "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro técnico na chave: {e}")
        st.stop()

# Tenta estabelecer o cliente
try:
    client = conectar()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
except:
    st.warning("Aguardando conexão com o Google...")
    st.stop()

# 3. CARREGAMENTO DE DADOS (ORDEM E SOMA CORRETAS)
@st.cache_data(ttl=2)
def carregar_tudo():
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df = df[df['Data'].str.strip() != ""].copy() # Mata linhas fantasmas
    
    def para_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(para_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar_tudo()
mes_atual = datetime.now().strftime('%m/%y')

# 4. LANÇAMENTO (SIDEBAR)
st.sidebar.header("🚀 Lançar")
with st.sidebar.form("f_novo", clear_on_submit=True):
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Outros"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear()
        st.rerun()

# 5. TELA PRINCIPAL (TAGS -> GRÁFICOS -> TABELA)
st.title("🛡️ FinançasPro Wilson")

if not df_base.empty:
    df_mes = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    
    # --- TAGS NO TOPO ---
    t1, t2, t3, t4 = st.columns(4)
    def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
    
    t1.metric("📈 Receitas", m_fmt(df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()))
    t2.metric("📉 Despesas", m_fmt(df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()))
    t3.metric("💰 Rendimento", m_fmt(df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum()))
    t4.metric("⏳ Pendente", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))

    st.divider()

    # --- GRÁFICOS NO MEIO ---
    g1, g2 = st.columns(2)
    with g1:
        df_p = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_p.empty:
            st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria", hole=0.4), use_container_width=True)
    with g2:
        df_b = df_mes.groupby('Tipo')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_b, x='Tipo', y='V_Num', color='Tipo', title="Resumo do Mês"), use_container_width=True)

    st.divider()

    # --- PESQUISA E TABELA EMBAIXO ---
    st.subheader("🔍 Filtros de Pesquisa")
    c1, c2, c3 = st.columns(3)
    s_bnc = c1.multiselect("Banco:", df_base['Banco'].unique())
    s_sta = c2.multiselect("Status:", ["Pago", "Pendente"])
    s_tip = c3.multiselect("Tipo:", ["Despesa", "Receita", "Rendimento"])

    df_f = df_base.copy()
    if s_bnc: df_f = df_f[df_f['Banco'].isin(s_bnc)]
    if s_sta: df_f = df_f[df_f['Status'].isin(s_sta)]
    if s_tip: df_f = df_f[df_f['Tipo'].isin(s_tip)]

    st.dataframe(df_f[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

# 8. GERENCIADOR (SIDEBAR)
st.sidebar.divider()
if not df_base.empty:
    df_aux = df_base.copy()
    df_aux['ID'] = df_aux.index + 2
    opcoes = {f"L{r['ID']} | {r['Descrição']}": r['ID'] for _, r in df_aux.tail(10).iterrows()}
    sel = st.sidebar.selectbox("Gerenciar Linha:", [""] + list(opcoes.keys()))
    if sel:
        if st.sidebar.button("🚨 APAGAR"):
            sh.get_worksheet(0).delete_rows(int(opcoes[sel]))
            st.cache_data.clear(); st.rerun()
