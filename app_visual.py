import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (PK_LIST)
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

@st.cache_data(ttl=10)
def get_data_safe(spreadsheet_id, worksheet_name):
    try:
        client = conectar()
        sh = client.open_by_key(spreadsheet_id)
        all_ws = {w.title.lower().strip(): w for w in sh.worksheets()}
        ws = all_ws.get(worksheet_name.lower().strip())
        
        if ws:
            data = ws.get_all_records()
            if not data: return pd.DataFrame()
            df = pd.DataFrame(data)
            df.columns = [str(c).strip().lower() for c in df.columns]
            return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()

# --- INÍCIO DO APP ---
try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = conectar().open_by_key(SHEET_ID)

    tab_lanc, tab_bancos, tab_cartoes, tab_metas, tab_relat = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas", "📊 Relatórios"
    ])

    # 1. ABA LANÇAMENTOS
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Registro")
            with st.form("form_registro", clear_on_submit=True):
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                data_reg = st.date_input("Data", datetime.now())
                valor = st.number_input("Valor", min_value=0.0)
                desc = st.text_input("Descrição")
                
                # BUSCA DE BANCOS (Linha Corrigida abaixo)
                df_b_list = get_data_safe(SHEET_ID, "bancos")
                col_banco = next((c for c in df_b_list.columns if 'nome' in c or 'banco' in c), "nome")
                lista_bancos = df_b_list[col_banco].astype(str).tolist() if not df_b_list.empty else ["Dinheiro"]
                
                conta = st.selectbox("Qual Conta?", lista_bancos)
                
                if st.form_submit_button("Salvar"):
                    sh.get_worksheet(0).append_row([data_reg.strftime('%d/%m/%Y'), valor, desc, str(conta), tipo])
                    st.cache_data.clear()
                    st.success("Lançado com sucesso!")
                    st.rerun()

    # 2. ABA BANCOS
    with tab_bancos:
        st.subheader("🏦 Suas Contas")
        df_bancos = get_data_safe(SHEET_ID, "bancos")
        if not df_bancos.empty:
            st.dataframe(df_bancos, use_container_width=True)
        else:
            st.info("Aba 'bancos' não encontrada ou vazia.")

    # 3. ABA METAS
    with tab_metas:
        st.subheader("🎯 Suas Metas")
        df_metas = get_data_safe(SHEET_ID, "metas")
        if not df_metas.empty:
            col_nome = next((c for c in df_metas.columns if 'nome' in c or 'meta' in c), df_metas.columns[0])
            col_alvo = next((c for c in df_metas.columns if 'alvo' in c or 'valor' in c), None)
            
            if col_alvo:
                fig_m = px.bar(df_metas, x=col_nome, y=col_alvo, title="Objetivos")
                st.plotly_chart(fig_m, use_container_width=True)
            st.table(df_metas)
        else:
            st.info("Aba 'metas' vazia.")

    # 4. ABA RELATÓRIOS
    with tab_relat:
        st.subheader("📊 Resumo")
        df_l = get_data_safe(SHEET_ID, sh.get_worksheet(0).title)
        if not df_l.empty and 'tipo' in df_l.columns:
            resumo = df_l.groupby('tipo')['valor'].sum().reset_index()
            fig_pie = px.pie(resumo, values='valor', names='tipo', hole=.4, 
                            color_discrete_map={'Receita':'#00CC96', 'Despesa':'#EF553B'})
            st.plotly_chart(fig_pie, use_container_width=True)
        else:
            st.warning("Sem dados para o gráfico.")

except Exception as e:
    st.error("Erro detectado: " + str(e))
