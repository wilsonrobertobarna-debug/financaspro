import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro", page_icon="🛡️", layout="wide")

# Estilos CSS (Estrutura 100% preservada)
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .resumo-card { padding: 8px; border-radius: 8px; text-align: center; border: 1px solid #ddd; background-color: #f8f9fa; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (Mantida conforme seus segredos)
@st.cache_resource
def conectar():
    try:
        info = st.secrets["connections"]["gsheets"]
        key = info["private_key"].replace("\\n", "\n").strip()
        creds = Credentials.from_service_account_info({
            "type": info["type"], "project_id": info["project_id"],
            "private_key_id": info["private_key_id"], "private_key": key,
            "client_email": info["client_email"], "token_uri": info["token_uri"],
        }, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. TRATAMENTO DE DADOS E DATA DO BRASIL
def limpar_v(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

# --- CÁLCULO DA DATA ATUAL NO BRASIL (GMT-3) ---
fuso_br = timezone(timedelta(hours=-3))
hoje_br = datetime.now(fuso_br).date()

@st.cache_data(ttl=60)
def carregar_dados():
    ws_l = sh.get_worksheet(0)
    dados_l = ws_l.get_all_values()
    df_l = pd.DataFrame(dados_l[1:], columns=dados_l[0]) if len(dados_l) > 1 else pd.DataFrame()
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    df_c.columns = [str(c).strip() for c in df_c.columns]
    df_c['Meta'] = df_c['Meta'].apply(limpar_v) if 'Meta' in df_c.columns else 0.0
    return df_b, df_c, df_l

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

# 4. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Menu:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]
        df_base['V_Num'] = df_base[c_val].apply(limpar_v)
        # Força a leitura correta da data que já está na planilha
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        
        # Filtros e Saldos
        bancos_lista = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculos de Métricas
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_v).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_v).sum()
        df_pago = df_filtrado[df_filtrado[c_sta] == 'Pago']
        saldo_atual = s_ini + df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()

        mes_f_atual = hoje_br.strftime('%m/%y')
        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_f_atual]

        st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📈 Receitas", f"R$ {df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("📉 Despesas", f"R$ {df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("💰 Rendimento", f"R$ {df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col4.metric("⏳ Pendente", f"R$ {df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- GRÁFICO MENSAL RECEITA X DESPESA (CORES FIXAS) ---
        st.write("---")
        st.subheader("📈 Evolução Mensal (Receita vs Despesa)")
        evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
        if not evol.empty:
            # Garante a ordem e as cores: Receita (Verde), Despesa (Vermelho)
            colunas_existentes = [c for c in ['Receita', 'Despesa'] if c in evol.columns]
            cores = []
            for c in colunas_existentes:
                cores.append("#28a745" if c == 'Receita' else "#dc3545")
            st.bar_chart(evol[colunas_existentes], color=cores)

        st.subheader("📋 Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # BARRA LATERAL - FORMULÁRIO COM DATA BRASIL
    with st.sidebar.form("novo"):
        st.write("### 🚀 Lançar")
        # Aqui a data já inicia com o dia de hoje no Brasil
        f_dat = st.date_input("Data", hoje_br)
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("SALVAR"):
            # O SEGREDO: Salvar como texto fixo DD/MM/AAAA para o Google Sheets não inverter
            data_formatada = f_dat.strftime("%d/%m/%Y")
            sh.get_worksheet(0).append_row([data_formatada, str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta], value_input_option='USER_ENTERED')
            st.cache_data.clear(); st.rerun()
