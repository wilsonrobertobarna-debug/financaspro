import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO PERSONALIZADO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Estilo da Tarja Azul de Saldo */
    .saldo-container {
        background-color: #007bff;
        color: white;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    /* Estilo dos Cartões de Tags */
    .tag-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA (Secrets)
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": private_key,
            "client_email": creds_info["client_email"],
            "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# --- CONFIGURAÇÃO DE CATEGORIAS ---
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Extras"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer"],
    "Rendimento": ["Dividendos", "Juros", "Aplicações"],
    "Pendência": ["Boleto a Pagar", "Empréstimo", "Dívida"]
}

# --- BARRA LATERAL ---
st.sidebar.header("📝 Novo Lançamento")
tipo = st.sidebar.selectbox("Tipo de Movimentação:", list(categorias_dict.keys()))

with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data_input = st.date_input("Data", datetime.now())
    valor_input = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    categoria_input = st.selectbox("Categoria", categorias_dict[tipo])
    descricao_input = st.text_input("Descrição")
    
    if st.form_submit_button("Salvar no FinançasPro"):
        if valor_input > 0:
            ws.append_row([data_input.strftime("%d/%m/%Y"), valor_input, categoria_input, tipo, descricao_input])
            st.cache_data.clear()
            st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    lista_dados = ws.get_all_values()
    if len(lista_dados) > 1:
        df = pd.DataFrame(lista_dados[1:], columns=lista_dados[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df_valid = df.dropna(subset=['Data']).copy()

        # CÁLCULOS
        receitas = df_valid[df_valid['Tipo'] == 'Receita']['Valor'].sum()
        despesas = df_valid[df_valid['Tipo'] == 'Despesa']['Valor'].sum()
        rendimentos = df_valid[df_valid['Tipo'] == 'Rendimento']['Valor'].sum()
        pendencias = df_valid[df_valid['Tipo'] == 'Pendência']['Valor'].sum()
        
        saldo_final = (receitas + rendimentos) - despesas

        # --- EXIBIÇÃO: TARJA AZUL DE SALDO ---
        st.markdown(f"""
            <div class="saldo-container">
                <h2 style='margin:0; font-size: 1.2rem;'>SALDO ATUAL</h2>
                <h1 style='margin:0; font-size: 2.8rem;'>R$ {saldo_final:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        # --- EXIBIÇÃO: TAGS ABAIXO ---
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("<div class='tag-card' style='border-left-color: #28a745;'>", unsafe_allow_html=True)
            st.metric("Receitas", f"R$ {receitas:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='tag-card' style='border-left-color: #dc3545;'>", unsafe_allow_html=True)
            st.metric("Despesas", f"R$ {despesas:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col3:
            st.markdown("<div class='tag-card' style='border-left-color: #17a2b8;'>", unsafe_allow_html=True)
            st.metric("Rendimentos", f"R$ {rendimentos:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

        with col4:
            st.markdown("<div class='tag-card' style='border-left-color: #ffc107;'>", unsafe_allow_html=True)
            st.metric("Pendências", f"R$ {pendencias:,.2f}")
            st.markdown("</div>", unsafe_allow_html=True)

        # --- GRÁFICOS ---
        st.markdown("---")
        df_valid['Mês/Ano'] = df_valid['Data'].dt.strftime('%m/%Y')
        resumo = df_valid.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()

        st.subheader("📊 Evolução Mensal")
        fig = go.Figure()
        for t in ["Receita", "Despesa", "Rendimento"]:
            if t in resumo.columns:
                fig.add_trace(go.Bar(x=resumo['Mês/Ano'], y=resumo[t], name=t))
        
        fig.update_layout(barmode='group', height=350)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        st.subheader("📋 Histórico")
        st.dataframe(df.tail(10), use_container_width=True)
        
    else:
        st.info("Lance os dados para ativar o painel.")
except Exception as e:
    st.error(f"Erro ao processar: {e}")
