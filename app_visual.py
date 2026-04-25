import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua chave real)
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

# --- CONEXÃO ---
@st.cache_resource
def conectar_google():
    private_key = "\n".join([l.strip() for l in PK_LIST])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": private_key
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- FUNÇÃO SALVAR (Zera campos e organiza colunas) ---
def salvar_registro():
    # 1. Pegamos os dados AGORA (antes de limpar)
    val = st.session_state.valor_input
    if val > 0:
        d_txt = st.session_state.data_input.strftime('%d/%m/%Y')
        desc_txt = st.session_state.desc_input
        parc_txt = st.session_state.parcela_input
        benef_txt = st.session_state.benef_input
        cat_txt = st.session_state.cat_input
        banco_txt = st.session_state.banco_input
        status_txt = st.session_state.status_input
        tipo_txt = st.session_state.tipo_input
        
        # Formata descrição
        final_desc = f"{desc_txt} ({parc_txt})" if parc_txt != "1/1" else desc_txt
        
        # 2. MAPA DE COLUNAS (Ajustado para sua planilha)
        # A=Data | B=Valor | C=Cat | D=Banco | E=Desc | F=Benef | G=Conta | H=Obs1 | I=Obs2 | J=STATUS | K=TIPO
        nova_linha = [
            d_txt, val, cat_txt, banco_txt, final_desc, benef_txt, 
            "Pessoal",  # Coluna G
            "",         # Coluna H (Vazia para não empurrar o Status)
            "",         # Coluna I (Vazia para não empurrar o Status)
            status_txt, # Coluna J (Aqui cai o Pago/Pendente)
            tipo_txt    # Coluna K (Aqui cai Receita/Despesa)
        ]
        
        ws_lanc.append_row(nova_linha)
        
        # 3. ZERAR CAMPOS
        st.session_state.valor_input = 0.0
        st.session_state.benef_input = ""
        st.session_state.desc_input = ""
        st.session_state.parcela_input = "1/1"
        st.toast("✅ Lançamento gravado!")

# --- APP PRINCIPAL ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)

    # Carregar dados para os gráficos (Parte de Cima)
    data = ws_lanc.get_all_records()
    df = pd.DataFrame(data)
    
    st.title("🛡️ FinançasPro Wilson")

    if not df.empty:
        # Filtros e Métricas
        df.columns = [str(c).strip() for c in df.columns]
        df['Valor_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(), errors='coerce').fillna(0)
        
        m1, m2 = st.columns(2)
        with m1:
            st.metric("Total Despesas", f"R$ {df[df['Tipo Movimentação'] == 'Despesa']['Valor_num'].sum():,.2f}")
        with m2:
            st.metric("Total Receitas", f"R$ {df[df['Tipo Movimentação'] == 'Receita']['Valor_num'].sum():,.2f}")

    st.divider()

    # Layout de formulário
    c_form, c_table = st.columns([1, 2.5])

    with c_form:
        st.subheader("📝 Lançamento")
        st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, key="tipo_input")
        st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_input")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="valor_input")
        st.text_input("Beneficiário", key="benef_input")
        st.text_input("Descrição", key="desc_input")
        st.text_input("Parcelamento", value="1/1", key="parcela_input")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"], key="cat_input")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"], key="banco_input")
        st.selectbox("Status", ["Pago", "Pendente"], key="status_input")
        
        st.button("🚀 Salvar na Planilha", use_container_width=True, on_click=salvar_registro)

    with c_table:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df.tail(15), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
