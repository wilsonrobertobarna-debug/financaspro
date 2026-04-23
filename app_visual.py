import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    "MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP",
    "gcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu",
    "BPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx",
    "74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox",
    "Ke7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m",
    "kJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs",
    "rwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0",
    "FRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7",
    "nroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq",
    "xlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au",
    "fWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t",
    "McYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL",
    "YGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ",
    "BsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT",
    "qwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS",
    "Ns8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB",
    "N9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw",
    "GW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC",
    "IXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA",
    "o/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz",
    "MXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4",
    "qQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN",
    "Irq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA",
    "VnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW",
    "O02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb",
    "1GHhDwH33nMtylvbUkBN8pBU",
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "private_key": "\n".join(PK_LIST),
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=20)
def get_data_safe(spreadsheet_id, worksheet_name):
    client = conectar()
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    raw_data = ws.get_all_records()
    if not raw_data: return pd.DataFrame()
    df = pd.DataFrame(raw_data)
    df.columns = [str(c).strip().title() for c in df.columns]
    return df

def limpar_cache():
    st.cache_data.clear()

try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    client = conectar()
    sh = client.open_by_key(SHEET_ID)

    tab_lanc, tab_bancos, tab_cartoes, tab_metas, tab_relat = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas", "📊 Relatórios"
    ])

    # --- ABA 1: LANÇAMENTOS (Com campo Tipo para Receita/Despesa) ---
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Lançamento")
            with st.form("form_gasto", clear_on_submit=True):
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                dt_l = st.date_input("Data", datetime.now())
                vl_l = st.number_input("Valor", min_value=0.0)
                ds_l = st.text_input("Descrição")
                
                df_b = get_data_safe(SHEET_ID, "bancos")
                bancos = df_b['Nome'].tolist() if not df_b.empty else ["Dinheiro"]
                origem = st.selectbox("Conta", bancos)
                
                if st.form_submit_button("🚀 Salvar"):
                    ws_g = sh.get_worksheet(0)
                    ws_g.append_row([dt_l.strftime('%d/%m/%Y'), vl_l, ds_l, origem, tipo])
                    limpar_cache()
                    st.success("Salvo!")
                    st.rerun()

        with col_h:
            st.subheader("📋 Histórico")
            df_hist = get_data_safe(SHEET_ID, sh.get_worksheet(0).title)
            if not df_hist.empty:
                st.dataframe(df_hist.tail(10), use_container_width=True)

    # --- ABA 4: METAS (Com visualização em Barras) ---
    with tab_metas:
        st.subheader("🎯 Metas de Economia")
        with st.form("f_meta"):
            obj = st.text_input("Objetivo")
            alvo = st.number_input("Valor Alvo")
            atual = st.number_input("Valor Já Guardado", min_value=0.0)
            if st.form_submit_button("Salvar Meta"):
                sh.worksheet("metas").append_row([obj, alvo, atual])
                limpar_cache()
                st.rerun()
        
        df_m = get_data_safe(SHEET_ID, "metas")
        if not df_m.empty:
            df_m['Progresso (%)'] = (df_m['Atual'] / df_m['Alvo'] * 100).round(1)
            fig_meta = px.bar(df_m, x='Objetivo', y=['Atual', 'Alvo'], barmode='group', title="Progresso das Metas")
            st.plotly_chart(fig_meta, use_container_width=True)
            st.table(df_m)

    # --- ABA 5: RELATÓRIOS (Mes a Mes: Receitas vs Despesas) ---
    with tab_relat:
        st.header("📊 Evolução Mensal")
        df_rel = get_data_safe(SHEET_ID, sh.get_worksheet(0).title)
        
        if not df_rel.empty and 'Tipo' in df_rel.columns:
            df_rel['Data'] = pd.to_datetime(df_rel['Data'], dayfirst=True, errors='coerce')
            df_rel['Mes'] = df_rel['Data'].dt.strftime('%Y-%m')
            df_rel['Valor'] = pd.to_numeric(df_rel['Valor'], errors='coerce').fillna(0)

            # Agrupamento Mes a Mes
            df_mes = df_rel.groupby(['Mes', 'Tipo'])['Valor'].sum().reset_index()
            
            fig_evolucao = px.bar(df_mes, x='Mes', y='Valor', color='Tipo', 
                                  barmode='group', title="Receitas vs Despesas por Mês",
                                  color_discrete_map={'Receita': '#00CC96', 'Despes
