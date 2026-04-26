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
        background-color: #007bff; color: white; padding: 8px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px; line-height: 1.1;
    }
    .saldo-container h2 { margin: 0; font-size: 1.8rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e0e0e0; }
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

# 3. CARREGAMENTO DE CADASTROS
@st.cache_data(ttl=60)
def carregar_cadastros():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    except:
        df_b = pd.DataFrame(columns=['Nome do Banco', 'Saldo Inicial'])
    try:
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    except:
        df_c = pd.DataFrame(columns=['Nome'])
    try:
        df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
    except:
        df_ct = pd.DataFrame(columns=['Nome do Cartão'])
    return df_b, df_c, df_ct

df_bancos_cad, df_cats_cad, df_cartoes_cad = carregar_cadastros()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        # Identificação dinâmica de colunas
        c_tipo, c_cat, c_bnc, c_stat = df_base.columns[3], df_base.columns[2], df_base.columns[4], df_base.columns[5]

        # Tratamento de Dados
        df_base['Valor_Num'] = pd.to_numeric(df_base['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df_base['Data_DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # Filtro de Banco
        bancos_filtro = ["Todos"] + sorted(df_bancos_cad['Nome do Banco'].unique().tolist()) if not df_bancos_cad.empty else ["Todos"]
        banco_sel = st.selectbox("🔍 Filtrar por Banco:", bancos_filtro)
        df = df_base[df_base[c_bnc] == banco_sel].copy() if banco_sel != "Todos" else df_base.copy()

        # Dashboard de Valores
        s_inicial = pd.to_numeric(df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if banco_sel != "Todos" else pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()
        
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum()
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum()
        saldo_final = s_inicial + rec - desp

        st.markdown(f'<div class="saldo-container"><small>Saldo Atual em {banco_sel}</small><h2>R$ {saldo_final:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)
        
        # --- ÁREA DE GRÁFICOS RESTAURADA ---
        st.write("---")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("🍕 Gastos por Categoria (Mês)")
            df_mes = df[(df['Mes_Ano'] == mes_atual) & (df[c_tipo] == 'Despesa')]
            if not df_mes.empty:
                g_cat = df_mes.groupby(c_cat)['Valor_Num'].sum()
                st.bar_chart(g_cat, color='#ffc107')
            else:
                st.info("Sem despesas este mês.")

        with col_g2:
            st.subheader("📊 Receita x Despesa")
            if not df.empty:
                g_comp = df.groupby(['Mes_Ano', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
                st.line_chart(g_comp)
        
        st.subheader("🏦 Resumo por Banco")
        if not df_base.empty:
            g_banco = df_base[df_base[c_tipo] == 'Despesa'].groupby(c_bnc)['Valor_Num'].sum()
            st.bar_chart(g_banco, color='#007bff')

        # Histórico
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # FORMULÁRIO (DINÂMICO)
    with st.sidebar.form("novo_lan"):
        st.write("### 🚀 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        f_bnc = st.selectbox("Banco/Cartão", sorted(df_bancos_cad['Nome do Banco'].tolist() + df_cartoes_cad['Nome do Cartão'].tolist() + ["Dinheiro"]))
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
            st.cache_data.clear(); st.rerun()

# Manutenção abas Pets e Veículo (sem alterações)
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    # ... (código anterior preservado)
else:
    st.title("🚗 Controle: Veículo")
    # ... (código anterior preservado)
