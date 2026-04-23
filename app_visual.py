import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Sua chave funcional de 26 linhas)
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
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    private_key = "\n".join([line.strip() for line in PK_LIST])
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": private_key
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# 3. EXECUÇÃO DO SISTEMA
try:
    client = conectar_google()
    # Usando o ID da sua planilha diretamente
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(SHEET_ID)
    ws = sh.get_worksheet(0)
    
    st.title("💰 FinançasPro - Painel de Controle")

    # --- BARRA LATERAL: FORMULÁRIO DE CADASTRO ---
    with st.sidebar:
        st.header("📝 Novo Lançamento")
        
        # Data com formato Brasil
        data_input = st.date_input("Data do Gasto", datetime.now())
        data_br = data_input.strftime('%d/%m/%Y')
        
        valor = st.number_input("Valor (R$)", min_value=0.0, step=0.50, format="%.2f")
        
        categoria = st.selectbox("Categoria", 
            ["Alimentação", "Lazer", "Casa", "Transporte", "Saúde", "Educação", "Assinaturas", "Outros"])
        
        banco = st.selectbox("Banco/Conta", 
            ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro Vivo", "Santander"])
        
        forma = st.selectbox("Forma de Pagamento", 
            ["Cartão de Crédito", "Cartão de Débito", "Pix", "Dinheiro", "Boleto"])

        if st.button("🚀 Salvar na Planilha"):
            # Ordem das colunas: Data, Valor, Categoria, Banco, Forma de Pagamento
            ws.append_row([data_br, valor, categoria, banco, forma])
            st.success(f"Salvo com sucesso: R$ {valor:.2f} em {data_br}")
            st.rerun()

    # --- ÁREA PRINCIPAL: VISUALIZAÇÃO ---
    dados = ws.get_all_records()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Garante que 'Valor' seja número para não dar erro de soma
        if 'Valor' in df.columns:
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        # Métricas no topo
        col1, col2, col3 = st.columns(3)
        with col1:
            total = df['Valor'].sum()
            st.metric("Total Gasto (Geral)", f"R$ {total:,.2f}")
        with col2:
            itens = len(df)
            st.metric("Nº de Lançamentos", itens)
        with col3:
            if not df.empty:
                media = total / itens
                st.metric("Média por Gasto", f"R$ {media:,.2f}")

        st.divider()
        st.subheader("📊 Histórico de Transações")
        
        # Exibe a tabela formatada
        st.dataframe(
            df.style.format({"Valor": "R$ {:.2f}"}), 
            use_container_width=True,
            hide_index=True
        )
        
    else:
        st.info("A planilha está conectada, mas não há dados. Faça seu primeiro lançamento na lateral!")

except Exception as e:
    st.error(f"Erro no sistema: {e}")
    st.info("💡 Dica: Verifique se a sua planilha no Google Sheets tem os cabeçalhos: Data, Valor, Categoria, Banco, Forma de Pagamento")
