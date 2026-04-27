import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", page_icon="🛡️", layout="wide")

# Estilos Visuais
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .resumo-card { padding: 8px; border-radius: 8px; text-align: center; border: 1px solid #ddd; background-color: #f8f9fa; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
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
        st.error(f"Erro na conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. TRATAMENTO DE DADOS
def limpar_v(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

@st.cache_data(ttl=60)
def carregar_dados():
    ws_l = sh.get_worksheet(0)
    df_l = pd.DataFrame(ws_l.get_all_records())
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    return df_l, df_b, df_c

df_base, df_bancos_cad, df_cats_cad = carregar_dados()

# Ajuste de Fuso Horário (Brasília)
hoje_br = (datetime.now(timezone.utc) - timedelta(hours=3)).date()

# 4. BARRA LATERAL (LANÇAMENTOS)
st.sidebar.title("🎮 Painel Wilson")

with st.sidebar.form("novo_lancamento"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", hoje_br)
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR LANÇAMENTO"):
        # O SEGREDO DA DATA: Salva como texto DD/MM/AAAA e força o Sheets a aceitar
        data_formatada = f_dat.strftime("%d/%m/%Y")
        sh.get_worksheet(0).append_row(
            [data_formatada, str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta], 
            value_input_option='USER_ENTERED'
        )
        st.cache_data.clear()
        st.success("Salvo com sucesso!")
        st.rerun()

st.sidebar.write("---")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

# 5. ABA PRINCIPAL: FINANÇAS
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Padronização de colunas e limpeza
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]
        
        df_base['V_Num'] = df_base[c_val].apply(limpar_v)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')

        # Filtro de Banco
        bancos_visiveis = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Visualizar Banco:", bancos_visiveis)
        df_f = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Métrica de Saldo
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_v).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_v).sum()
        df_pago = df_f[df_f[c_sta] == 'Pago']
        receitas = df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesas = df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_atual = s_ini + receitas - despesas

        st.markdown(f'<div class="saldo-container"><small>Saldo Disponível ({banco_sel})</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # --- GRÁFICO DE EVOLUÇÃO (CORES FIXAS) ---
        st.write("---")
        st.subheader("📈 Evolução Mensal")
        evol = df_f.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
        
        if not evol.empty:
            # Mapeamento para evitar o erro de cores
            cores_map = {"Receita": "#28a745", "Despesa": "#dc3545", "Rendimento": "#2ecc71"}
            cores_finais = [cores_map.get(col, "#808080") for col in evol.columns]
            st.bar_chart(evol, color=cores_finais)

        # --- TABELA DE LANÇAMENTOS ---
        st.write("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_f.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)
    else:
        st.warning("Aguardando dados da planilha...")
