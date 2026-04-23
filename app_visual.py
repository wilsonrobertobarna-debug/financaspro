import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="📊")

# 2. CHAVE DE ACESSO (Sua PK funcional)
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
    creds = Credentials.from_service_account_info({
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": "\n".join(PK_LIST)
    }, scopes=scope)
    return gspread.authorize(creds)

try:
    client = conectar()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    
    ws_gastos = sh.get_worksheet(0)
    ws_bancos = sh.worksheet("bancos")
    ws_cartoes = sh.worksheet("cartoes")
    ws_metas = sh.worksheet("metas")

    tab_lanc, tab_bancos, tab_cartoes, tab_metas, tab_relat = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas", "📊 Relatórios"
    ])

    # --- ABA 1: LANÇAMENTOS ---
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Gasto")
            data_sel = st.date_input("Data da Compra", datetime.now())
            valor = st.number_input("Valor Total", min_value=0.0, step=10.0)
            parc = st.number_input("Parcelas", min_value=1, value=1)
            bancos_data = ws_bancos.get_all_records()
            lista_bancos = [r['Nome do Banco'] for r in bancos_data] if bancos_data else ["Dinheiro"]
            banco_escolhido = st.selectbox("Onde pagou?", lista_bancos)
            forma = st.selectbox("Como pagou?", ["Crédito", "Débito", "Pix", "Dinheiro"])
            
            if st.button("🚀 Salvar Gasto", use_container_width=True):
                valor_p = valor / parc
                for i in range(parc):
                    dt = (data_sel + relativedelta(months=i)).strftime('%d/%m/%Y')
                    ws_gastos.append_row([dt, round(valor_p, 2), f"Gasto ({i+1}/{parc})", banco_escolhido, forma])
                st.success("Lançamento concluído!")
                st.rerun()

        with col_h:
            st.subheader("📊 Últimos Lançamentos")
            dados_g = ws_gastos.get_all_records()
            if dados_g:
                st.dataframe(pd.DataFrame(dados_g).tail(10), use_container_width=True, hide_index=True)

    # --- ABAS DE CADASTRO (BANCOS, CARTÕES, METAS) ---
    with tab_bancos:
        st.subheader("🏦 Cadastro de Bancos")
        with st.form("f_b"):
            n = st.text_input("Banco")
            s = st.number_input("Saldo")
            if st.form_submit_button("Salvar"):
                ws_bancos.append_row([n, s, "Corrente"])
                st.rerun()
        st.table(pd.DataFrame(ws_bancos.get_all_records()))

    with tab_cartoes:
        st.subheader("💳 Meus Cartões")
        with st.form("f_c"):
            nc = st.text_input("Nome")
            lim = st.number_input("Limite")
            ven = st.number_input("Vencimento", 1, 31)
            fec = st.number_input("Fechamento", 1, 31)
            if st.form_submit_button("Salvar"):
                ws_cartoes.append_row([nc, lim, ven, fec])
                st.rerun()
        st.table(pd.DataFrame(ws_cartoes.get_all_records()))

    with tab_metas:
        st.subheader("🎯 Minhas Metas")
        with st.form("f_m"):
            nm = st.text_input("Objetivo")
            va = st.number_input("Valor")
            if st.form_submit_button("Salvar"):
                ws_metas.append_row([nm, va, "Ativo"])
                st.rerun()
        st.table(pd.DataFrame(ws_metas.get_all_records()))

    # --- ABA 5: RELATÓRIOS (COM CORREÇÃO PARA DATA ISO) ---
    with tab_relat:
        st.header("📈 Relatórios")
        if dados_g:
            df = pd.DataFrame(dados_g)
            
            # CORREÇÃO DEFINITIVA: Converte qualquer formato e remove lixo
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df = df.dropna(subset=['Data'])
            
            df['Mes_Ano'] = df['Data'].dt.strftime('%m/%Y')
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("Gasto por Mês")
                df_m = df.groupby(['Mes_Ano', 'Forma'])['Valor'].sum().reset_index()
                st.plotly_chart(px.bar(df_m, x='Mes_Ano', y='Valor', color='Forma', barmode='stack'), use_container_width=True)
            
            with col2:
                st.subheader("Meta Termômetro")
                m_data = ws_metas.get_all_records()
                if m_data:
                    m_sel = st.selectbox("Selecione a Meta", [m['Nome da Meta'] for m in m_data])
                    alvo = next(float(m['Valor Alvo']) for m in m_data if m['Nome da Meta'] == m_sel)
                    atual = df['Valor'].sum() * 0.1 # Simulação 10% economia
                    fig = go.Figure(go.Indicator(mode="gauge+number", value=atual, gauge={'axis': {'range': [0, alvo]}, 'bar': {'color': "green"}}))
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Lance dados para ver gráficos.")

except Exception as e:
    st.error(f"Erro Crítico: {e}")
