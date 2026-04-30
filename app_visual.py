import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO CSS PARA VALORES DISCRETOS
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 1.1rem !important;}</style>", unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique as chaves nos Secrets!"); st.stop()
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
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# IDENTIFICAÇÃO DAS ABAS
ws_base = sh.get_worksheet(0) # Aba de Lançamentos
try:
    ws_bancos = sh.worksheet("Bancos") # Sua nova aba
except:
    ws_bancos = None

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=2)
def carregar_base():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    # Limpeza de valores para cálculo
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

@st.cache_data(ttl=2)
def carregar_bancos():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 0:
            # Pega o que você preencheu na aba Bancos exatamente como está lá
            return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

df_base = carregar_base()
df_bancos = carregar_bancos()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🏦 Bancos & Cartões", "🐾 Pets", "🚗 Veículo"])

# FORMULÁRIO DE LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet", "Veículo", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "XP"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS
if "💰" in aba:
    st.title("🛡️ FinançasPro")
    if not df_base.empty:
        # Cálculo de Saldo
        receitas = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesas = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO TOTAL: {m_fmt(receitas - despesas)}")
        
        # Filtro do mês
        df_m = df_base[df_base['Mes_Ano'] == mes_atual]
        m1, m2 = st.columns(2)
        m1.metric("📉 Gastos do Mês", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m2.metric("📈 Entradas do Mês", m_fmt(df_m[df_m['Tipo'] != 'Despesa']['V_Num'].sum()))
        
        st.dataframe(df_base.iloc[::-1].head(10), use_container_width=True, hide_index=True)

elif "🏦" in aba:
    st.title("🏦 Bancos & Cartões")
    
    # TABELA DA ABA BANCOS (O que você preencheu manualmente)
    st.subheader("📋 Minhas Contas (Informação Manual)")
    if not df_bancos.empty:
        st.dataframe(df_bancos, use_container_width=True, hide_index=True)
    else:
        st.warning("⚠️ Wilson, preencha a aba 'Bancos' no Sheets para ver os dados aqui.")

    st.divider()

    # SALDOS CALCULADOS (O que o sistema soma sozinho)
    st.subheader("💰 Saldo Real (Soma dos Lançamentos)")
    if not df_base.empty:
        bancos = df_base['Banco'].unique()
        cols = st.columns(len(bancos) if len(bancos) < 5 else 4)
        for i, b in enumerate(bancos):
            s = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].isin(['Receita', 'Rendimento']))]['V_Num'].sum() - \
                df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
            cols[i % 4].metric(b, m_fmt(s))

elif "🐾" in aba:
    st.title("🐾 Pets")
    # Mostra tudo que tem "Pet" na categoria
    df_pet = df_base[df_base['Categoria'] == 'Pet']
    st.dataframe(df_pet, use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    df_car = df_base[df_base['Categoria'] == 'Veículo']
    st.dataframe(df_car, use_container_width=True, hide_index=True)
