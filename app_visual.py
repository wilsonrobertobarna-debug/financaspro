import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Sua chave funcional)
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
    private_key = "\n".join(PK_LIST)
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": private_key
    }
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
    return gspread.authorize(creds)

# 3. LÓGICA PRINCIPAL
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0) # Aba de Lançamentos
    
    # Busca categorias da aba 'categorias' (Crie esta aba na sua planilha!)
    try:
        ws_cat = sh.worksheet("categorias")
        dados_cat = ws_cat.get_all_records()
        df_cat = pd.DataFrame(dados_cat)
    except:
        # Se não existir, cria uma base temporária para não quebrar o app
        df_cat = pd.DataFrame({"Tipo": ["Receita", "Despesa"], "Nome": ["Salário", "Aluguel"]})
        st.warning("⚠️ Aba 'categorias' não encontrada. Crie-a na sua planilha com as colunas 'Tipo' e 'Nome'.")

    st.title("💼 FinançasPro Wilson")
    
    tab_lanc, tab_bancos, tab_metas, tab_config = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "🎯 Metas", "⚙️ Configurações"
    ])

    with tab_lanc:
        col_form, col_hist = st.columns([1, 2])
        
        with col_form:
            st.subheader("📝 Novo Registro")
            tipo_mov = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            
            # FILTRO DINÂMICO DE CATEGORIA
            lista_filtrada = df_cat[df_cat['Tipo'] == tipo_mov]['Nome'].tolist()
            cat = st.selectbox("Categoria", lista_filtrada if lista_filtrada else ["Sem categorias cadastradas"])
            
            data_sel = st.date_input("Data", datetime.now())
            valor_total = st.number_input("Valor (R$)", min_value=0.0, step=10.0, format="%.2f")
            parcelas = st.number_input("Nº Parcelas", min_value=1, value=1)
            beneficiario = st.text_input("Beneficiário/Origem")
            centro_custo = st.selectbox("Centro de Custo", ["Pessoal", "Família", "Trabalho"])
            banco = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
            
            if st.button("🚀 Salvar", use_container_width=True):
                valor_parcela = valor_total / parcelas
                for i in range(parcelas):
                    data_p = data_sel + relativedelta(months=i)
                    data_str = data_p.strftime('%d/%m/%Y')
                    desc = f"{cat} ({i+1}/{parcelas})" if parcelas > 1 else cat
                    ws_lanc.append_row([data_str, round(valor_parcela, 2), desc, banco, "Automático", beneficiario, centro_custo, tipo_mov])
                st.success("Salvo!")
                st.rerun()

        with col_hist:
            st.subheader("📊 Histórico")
            dados = ws_lanc.get_all_records()
            if dados:
                df = pd.DataFrame(dados)
                st.dataframe(df.tail(10), use_container_width=True)

    with tab_config:
        st.subheader("🛠️ Gerenciar Categorias")
        
        # Formulário para criar categoria
        with st.form("nova_cat"):
            c1, c2 = st.columns(2)
            nova_cat_nome = c1.text_input("Nome da Categoria")
            nova_cat_tipo = c2.selectbox("Tipo da Categoria", ["Despesa", "Receita"])
            if st.form_submit_button("➕ Adicionar"):
                ws_cat.append_row([nova_cat_tipo, nova_cat_nome])
                st.success(f"{nova_cat_nome} adicionada!")
                st.rerun()
        
        st.divider()
        
        # Lista para excluir categoria
        st.write("### Lista Atual")
        if not df_cat.empty:
            for index, row in df_cat.iterrows():
                cols = st.columns([3, 1])
                cols[0].write(f"**{row['Nome']}** ({row['Tipo']})")
                if cols[1].button("🗑️", key=f"del_{index}"):
                    # O gspread usa índice começando em 2 (1 é cabeçalho)
                    ws_cat.delete_rows(index + 2)
                    st.rerun()

except Exception as e:
    st.error(f"Erro no sistema: {e}")
