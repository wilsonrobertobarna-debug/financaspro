import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# CHAVE DE ACESSO (Mantenha sua chave real aqui)
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
    "Ns8Le56t5Bed2PmfMGXjTLBed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4",
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
def conectar_google():
    private_key = "\n".join([l.strip() for l in PK_LIST])
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": private_key
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

def salvar_registro():
    if st.session_state.v_valor > 0:
        # Captura antes da limpeza
        v_desc = st.session_state.v_desc
        
        # Ordem rigorosa das 11 colunas (A-K)
        nova_linha = [
            st.session_state.v_data.strftime('%d/%m/%Y'), # A: Data
            st.session_state.v_valor,                      # B: Valor
            st.session_state.v_cat,                        # C: Categoria
            st.session_state.v_banco,                      # D: Banco
            v_desc,                                        # E: Descrição
            st.session_state.v_benef,                      # F: Beneficiário
            "Pessoal",                                      # G: Conta
            "", "",                                         # H, I: Vazios
            st.session_state.v_status,                     # J: Status
            st.session_state.v_tipo                        # K: Tipo
        ]
        ws.append_row(nova_linha)
        
        # Limpeza automática
        st.session_state.v_valor = 0.0
        st.session_state.v_desc = ""
        st.session_state.v_benef = ""
        st.toast("✅ Lançamento enviado com sucesso!")

# --- EXECUÇÃO ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)
    
    st.title("🛡️ FinançasPro Wilson")

    # Colunas de Layout
    c_form, c_view = st.columns([1, 2.5])

    with c_form:
        st.subheader("📝 Novo Registro")
        st.radio("Tipo", ["Despesa", "Receita"], key="v_tipo", horizontal=True)
        st.date_input("Data", date.today(), key="v_data", format="DD/MM/YYYY")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="v_valor")
        st.text_input("Descrição", key="v_desc")
        st.text_input("Beneficiário", key="v_benef")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"], key="v_cat")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"], key="v_banco")
        st.selectbox("Status", ["Pago", "Pendente"], key="v_status")
        st.button("🚀 Gravar na Planilha", use_container_width=True, on_click=salvar_registro)

    with c_view:
        st.subheader("📋 Histórico Recente")
        dados = ws.get_all_records()
        if dados:
            df = pd.DataFrame(dados)
            st.dataframe(df.tail(15), use_container_width=True, hide_index=True)
        else:
            st.info("Aguardando novos lançamentos para exibir o histórico.")

except Exception as e:
    st.error(f"Erro de conexão ou estrutura: {e}")
