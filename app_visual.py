import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2rem; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
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

# 3. CARREGAMENTO DE CADASTROS (COM COLUNA META)
@st.cache_data(ttl=60)
def carregar_cadastros():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    except:
        df_b = pd.DataFrame(columns=['Nome do Banco', 'Saldo Inicial'])
    
    try:
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        # Garante que a coluna Meta existe e é numérica
        if 'Meta' in df_c.columns:
            df_c['Meta'] = pd.to_numeric(df_c['Meta'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        else:
            df_c['Meta'] = 0
    except:
        df_c = pd.DataFrame(columns=['Nome', 'Meta'])
    
    try:
        df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
    except:
        df_ct = pd.DataFrame(columns=['Nome do Cartão'])
        
    return df_b, df_c, df_ct

df_bancos_cad, df_cats_cad, df_cartoes_cad = carregar_cadastros()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        c_dat, c_val, c_cat, c_tip, c_bnc = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4]

        # Tratamento
        df_base['Valor_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_foco = datetime.now().strftime('%m/%y')

        # Saldo Total (Independente de Filtro para referência rápida)
        s_ini_total = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if not df_bancos_cad.empty else 0
        rec_total = df_base[df_base[c_tip] == 'Receita']['Valor_Num'].sum()
        desp_total = df_base[df_base[c_tip] == 'Despesa']['Valor_Num'].sum()
        saldo_geral = s_ini_total + rec_total - desp_total

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Consolidado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # --- ÁREA DE METAS (BARRAS EFICIENTES) ---
        st.write("---")
        st.subheader(f"📊 Desempenho por Categoria ({mes_foco})")
        
        # Prepara dados de Gasto Real vs Meta
        df_gasto_mes = df_base[(df_base['Mes_Ano'] == mes_foco) & (df_base[c_tip] == 'Despesa')]
        gasto_por_cat = df_gasto_mes.groupby(c_cat)['Valor_Num'].sum().reset_index()
        
        # Junta com as metas cadastradas
        df_metas = pd.merge(df_cats_cad[['Nome', 'Meta']], gasto_por_cat, left_on='Nome', right_on=c_cat, how='left').fillna(0)
        df_metas.columns = ['Categoria', 'Meta Planejada', 'Lixo', 'Gasto Real']
        df_metas = df_metas[['Categoria', 'Meta Planejada', 'Gasto Real']].set_index('Categoria')
        
        # Só mostra se houver meta ou gasto
        df_metas = df_metas[(df_metas['Meta Planejada'] > 0) | (df_metas['Gasto Real'] > 0)]
        
        if not df_metas.empty:
            st.bar_chart(df_metas, color=['#007bff', '#ff4b4b'], horizontal=True)
            st.caption("🔵 Meta Planejada | 🔴 Gasto Real")
        else:
            st.info("Cadastre metas na aba 'Categoria' para visualizar o gráfico de desempenho.")

        # Histórico
        st.write("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_base.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1].head(15), use_container_width=True)

    # Sidebar Lançamento Rápido
    with st.sidebar.form("quick_add"):
        st.write("### ➕ Lançamento Rápido")
        n_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        n_val = st.number_input("Valor", min_value=0.0)
        n_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        n_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        
        bancos = df_bancos_cad['Nome do Banco'].tolist() if not df_bancos_cad.empty else []
        cartoes = df_cartoes_cad['Nome do Cartão'].tolist() if not df_cartoes_cad.empty else []
        n_bnc = st.selectbox("Origem", sorted(bancos + cartoes + ["Dinheiro"]))
        
        if st.form_submit_button("SALVAR"):
            ws.append_row([n_dat.strftime("%d/%m/%Y"), str(n_val).replace('.', ','), n_cat, n_tip, n_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# Manutenção Milo e Veículo
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    # ... (restante do código preservado)
else:
    st.title("🚗 Meu Veículo")
    # ... (restante do código preservado)
