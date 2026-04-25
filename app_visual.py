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
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

def salvar_registro():
    if st.session_state.valor_in > 0:
        # Pega a descrição antes de limpar
        desc_limpa = st.session_state.desc_in
        
        # Monta a linha com 11 colunas exatas (A até K)
        nova_linha = [
            st.session_state.data_in.strftime('%d/%m/%Y'), # A
            st.session_state.valor_in,                      # B
            st.session_state.cat_in,                        # C
            st.session_state.banco_in,                      # D
            desc_limpa,                                     # E (Descrição)
            st.session_state.benef_in,                      # F (Beneficiário)
            "Pessoal",                                      # G (Conta)
            "", "",                                         # H e I (Espaçadores/Obs)
            st.session_state.status_in,                     # J (STATUS - Pago/Pendente)
            st.session_state.tipo_in                        # K (TIPO - Receita/Despesa)
        ]
        ws_lanc.append_row(nova_linha)
        
        # Limpa os campos
        st.session_state.valor_in = 0.0
        st.session_state.desc_in = ""
        st.session_state.benef_in = ""
        st.toast("✅ Salvo com sucesso!")

# --- EXECUÇÃO PRINCIPAL ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    st.title("💰 FinançasPro Wilson")
    st.info("Sistema simplificado para recuperação de dados.")

    col_esq, col_dir = st.columns([1, 2])

    with col_esq:
        st.subheader("📝 Lançamento")
        st.radio("Tipo", ["Despesa", "Receita"], key="tipo_in", horizontal=True)
        st.date_input("Data", date.today(), key="data_in", format="DD/MM/YYYY")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="valor_in")
        st.text_input("Descrição", key="desc_in")
        st.text_input("Beneficiário", key="benef_in")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"], key="cat_in")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"], key="banco_in")
        st.selectbox("Status", ["Pago", "Pendente"], key="status_in")
        st.button("🚀 Gravar Dados", use_container_width=True, on_click=salvar_registro)

    with col_dir:
        st.subheader("📋 Visualização da Planilha")
        dados_brutos = ws_lanc.get_all_records()
        if dados_brutos:
            df_view = pd.DataFrame(dados_brutos)
            st.dataframe(df_view.tail(15), use_container_width=True, hide_index=True)
        else:
            st.warning("Nenhum dado encontrado na planilha.")

except Exception as e:
    st.error(f"Erro ao conectar: {e}")
