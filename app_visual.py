import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 10px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .resumo-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO REFORÇADO
@st.cache_data(ttl=10)
def carregar_dados():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
        
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

# 4. INTERFACE LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# --- LÓGICA DE LANÇAMENTO COMUM ---
def formulario_lancamento(titulo_form, categorias_lista):
    with st.sidebar.form(f"f_{titulo_form}"):
        st.write(f"### 🚀 Novo Lançamento: {titulo_form}")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", categorias_lista)
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        f_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
        
        if st.form_submit_button("SALVAR"):
            ws = sh.get_worksheet(0)
            for i in range(f_parc):
                dt_p = f_dat + relativedelta(months=i)
                desc_p = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_p, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# --- LÓGICA DE GERENCIAMENTO COMUM ---
def gerenciar_lancamentos(df_referencia, col_dat, col_cat, col_val):
    st.sidebar.write("---")
    st.sidebar.write("### ⚙️ Gerenciar Lançamentos")
    if not df_referencia.empty:
        lista_edit = df_referencia.iloc[::-1].head(15) 
        opcoes = [f"{idx+2} | {row[col_dat]} | {row[col_cat]} | {row[col_val]}" for idx, row in lista_edit.iterrows()]
        item_sel = st.sidebar.selectbox("Selecione para editar:", [""] + opcoes)
        if item_sel:
            linha_idx = int(item_sel.split(" | ")[0])
            valor_atual_str = item_sel.split(" | ")[3].replace('R$', '').strip()
            novo_val = st.sidebar.number_input("Novo Valor:", value=limpar_valor(valor_atual_str))
            
            if st.sidebar.button("💾 Salvar Alteração"):
                sh.get_worksheet(0).update_cell(linha_idx, 2, str(novo_val).replace('.', ','))
                st.cache_data.clear(); st.rerun()
            
            c1, c2 = st.sidebar.columns(2)
            if c1.button("🗑️ Excluir"):
                sh.get_worksheet(0).delete_rows(linha_idx)
                st.cache_
