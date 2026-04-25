import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# 2. CONEXÃO SEGURA
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

# Inicializa conexão
client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# --- CONFIGURAÇÃO DE METAS (Exemplo) ---
# Você pode ajustar esses valores conforme seu planejamento mensal
META_GASTO_MENSAL = 3000.00 

# --- BARRA LATERAL (Inalterada para manter o que já funciona) ---
st.sidebar.header("📝 Novo Lançamento")
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Investimentos", "Presente", "Outros"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Outros"]
}
tipo = st.sidebar.radio("Tipo:", ["Despesa", "Receita"], horizontal=True)

with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data = st.date_input("Data", datetime.now())
    valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    categoria = st.selectbox("Categoria", categorias_dict[tipo])
    descricao = st.text_input("Descrição")
    
    if st.form_submit_button("Salvar"):
        if valor > 0:
            ws.append_row([data.strftime("%d/%m/%Y"), valor, categoria, tipo, descricao])
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
        df['Mês/Ano'] = df['Data'].dt.strftime('%m/%Y')

        # Cálculos de Meta
        resumo_mensal = df.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
        
        # 📊 GRÁFICO DE BARRAS COM META
        st.subheader("📊 Acompanhamento de Metas de Gastos")
        
        fig = go.Figure()

        # Barra de Despesa Real
        if 'Despesa' in resumo_mensal.columns:
            fig.add_trace(go.Bar(
                x=resumo_mensal['Mês/Ano'], 
                y=resumo_mensal['Despesa'], 
                name='Gasto Realizado',
                marker_color='#dc3545'
            ))

        # Linha ou Barra de Meta
        fig.add_trace(go.Scatter(
            x=resumo_mensal['Mês/Ano'], 
            y=[META_GASTO_MENSAL] * len(resumo_mensal),
            name='Meta de Gastos',
            line=dict(color='#ffc107', width=4, dash='dash')
        ))

        fig.update_layout(
            barmode='group', 
            height=400, 
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig, use_container_width=True)

        # Alerta de Meta
        if 'Despesa' in resumo_mensal.columns:
            ultimo_gasto = resumo_mensal['Despesa'].iloc[-1]
            if ultimo_gasto > META_GASTO_MENSAL:
                st.warning(f"⚠️ Atenção: Você ultrapassou a meta de gastos este mês em R$ {ultimo_gasto - META_GASTO_MENSAL:,.2f}!")
            else:
                st.success(f"✅ Parabéns! Você está R$ {META_GASTO_MENSAL - ultimo_gasto:,.2f} abaixo da sua meta.")

    else:
        st.info("Aguardando lançamentos para gerar os gráficos...")

except Exception as e:
    st.error(f"Erro ao processar dados: {e}")
