import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
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
        st.error(f"Erro: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    
    # Campo 1: Define se é Receita ou Despesa (Coluna TIPO)
    f_tipo = st.sidebar.selectbox("Tipo:", ["Receita", "Despesa", "Rendimento", "Pendência"])
    
    # Campo 2: Define o Banco (Coluna BANCO)
    f_banco = st.sidebar.selectbox("Banco:", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
    
    categorias_dict = {
        "Receita": ["Salário", "Vendas", "Extras"],
        "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"],
        "Rendimento": ["Dividendos", "Juros"],
        "Pendência": ["Boleto", "Dívida"]
    }
    
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0)
        f_cat = st.selectbox("Categoria", categorias_dict.get(f_tipo, ["Geral"]))
        f_status = st.text_input("Status (Pago ou Pendente)", value="Pago") 
        
        if st.form_submit_button("🚀 SALVAR AGORA"):
            # A ordem na planilha deve ser: Data | Valor | Categoria | Tipo | Banco | Status
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear()
            st.rerun()

# --- PROCESSAMENTO DOS DADOS ---
try:
    dados_raw = ws.get_all_values()
    if len(dados_raw) > 1:
        df = pd.DataFrame(dados_raw[1:], columns=dados_raw[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            
            # Resumo de Saldo
            rec = df_v[df_v['Tipo'].isin(['Receita', 'Rendimento'])]['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {rec - des:,.2f}</span></div>', unsafe_allow_html=True)

            # TABELA DE HISTÓRICO CORRIGIDA
            st.subheader("📋 Últimos Lançamentos")
            df_display = df_v.copy()
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            
            # Organizando as colunas exatamente como você pediu
            # Verifique se os nomes das colunas na sua planilha são exatamente estes
            colunas_para_mostrar = ['Data', 'Valor', 'Categoria', 'Tipo', 'Banco', 'Descrição']
            df_final = df_display[colunas_para_mostrar].tail(15)
            
            # Renomeando 'Descrição' para 'Status' apenas na visualização
            df_final.columns = ['Data', 'Valor', 'Categoria', 'Tipo', 'Banco', 'Status']
            
            st.dataframe(df_final.iloc[::-1], use_container_width=True)

            # GRÁFICO MENSAL
            st.markdown("---")
            st.subheader("📊 Comparativo Mensal")
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            res_mensal = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Despesa'], name='Despesa', marker_color='#dc3545'))
            st.plotly_chart(fig1, use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")
