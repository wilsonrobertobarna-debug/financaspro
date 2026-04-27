import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta, timezone

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", page_icon="🛡️", layout="wide")

# Estilos CSS (Simples e funcional para não quebrar)
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (Sem rodeios)
@st.cache_resource
def conectar():
    try:
        info = st.secrets["connections"]["gsheets"]
        creds = Credentials.from_service_account_info(info, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", 
            "https://www.googleapis.com/auth/drive"
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO DE DADOS
def limpar_v(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

@st.cache_data(ttl=60)
def carregar_dados():
    # Carrega as abas principais
    df_l = pd.DataFrame(sh.get_worksheet(0).get_all_records())
    df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
    df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
    return df_l, df_b, df_c

df_base, df_bancos_cad, df_cats_cad = carregar_dados()
hoje_br = (datetime.now(timezone.utc) - timedelta(hours=3)).date()

# 4. BARRA LATERAL (LANÇAMENTOS)
st.sidebar.header("🚀 Lançamentos")

with st.sidebar.form("form_novo"):
    f_dat = st.date_input("Data", hoje_br)
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        # DATA: Enviamos como string pura. O segredo é o 'USER_ENTERED' abaixo.
        data_str = f_dat.strftime("%d/%m/%Y")
        sh.get_worksheet(0).append_row(
            [data_str, str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_sta],
            value_input_option='USER_ENTERED'
        )
        st.cache_data.clear()
        st.rerun()

st.sidebar.write("---")
aba = st.sidebar.radio("Navegação", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

# 5. TELA DE FINANÇAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro")
    
    if not df_base.empty:
        # Padroniza nomes de colunas (remove espaços extras)
        df_base.columns = [c.strip() for c in df_base.columns]
        
        # Identifica colunas por posição para evitar erro de nome
        c_dat, c_val, _, c_tip, c_bnc, c_sta = df_base.columns[0:6]
        
        df_base['V_Num'] = df_base[c_val].apply(limpar_v)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')

        # Filtro de Banco
        banco_sel = st.selectbox("Filtrar Banco:", ["Todos"] + sorted(df_base[c_bnc].unique().tolist()))
        df_f = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculo de Saldo (Simplificado)
        saldo_pago = df_f[df_f[c_sta] == 'Pago']
        entradas = saldo_pago[saldo_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        saidas = saldo_pago[saldo_pago[c_tip] == 'Despesa']['V_Num'].sum()
        
        st.markdown(f"""
            <div class="saldo-container">
                <small>Saldo Disponível ({banco_sel})</small>
                <h2>R$ {entradas - saidas:,.2f}</h2>
            </div>
        """.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # MÉTRICAS (TAGS)
        m1, m2, m3 = st.columns(3)
        m1.metric("📈 Receitas", f"R$ {entradas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {saidas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("⏳ Pendente", f"R$ {df_f[df_f[c_sta] == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # GRÁFICO (Sem erro de cor)
        st.write("---")
        st.subheader("📊 Evolução Mensal")
        evol = df_f.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
        if not evol.empty:
            # Se der erro de cor de novo, o Streamlit usará as cores padrão dele
            try:
                st.bar_chart(evol, color=["#dc3545", "#28a745", "#2ecc71"][:len(evol.columns)])
            except:
                st.bar_chart(evol)

        # TABELA
        st.write("---")
        st.subheader("📋 Lançamentos")
        st.dataframe(df_f.drop(columns=['V_Num', 'DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)
