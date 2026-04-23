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
    
    # Conectando as abas (agora todas em minúsculo para facilitar)
    ws_gastos = sh.get_worksheet(0)
    ws_bancos = sh.worksheet("bancos")
    ws_cartoes = sh.worksheet("cartoes")
    ws_metas = sh.worksheet("metas")

    st.title("💼 FinançasPro Wilson")
    tab_lanc, tab_bancos, tab_cartoes, tab_metas = st.tabs(["🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas"])

    # --- ABA 1: LANÇAMENTOS ---
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Gasto")
            data_sel = st.date_input("Data da Compra", datetime.now())
            valor = st.number_input("Valor Total", min_value=0.0, step=10.0)
            parc = st.number_input("Parcelas", min_value=1, value=1)
            
            # Busca dinâmica: lê a aba 'bancos' para preencher as opções
            bancos_data = ws_bancos.get_all_records()
            lista_bancos = [r['Nome do Banco'] for r in bancos_data] if bancos_data else ["Dinheiro"]
            banco_escolhido = st.selectbox("Onde pagou?", lista_bancos)
            
            forma = st.selectbox("Como pagou?", ["Crédito", "Débito", "Pix", "Dinheiro"])
            
            if st.button("🚀 Salvar Gasto", use_container_width=True):
                valor_p = valor / parc
                for i in range(parc):
                    dt = (data_sel + relativedelta(months=i)).strftime('%d/%m/%Y')
                    desc = f"Gasto ({i+1}/{parc})" if parc > 1 else "Gasto Único"
                    ws_gastos.append_row([dt, round(valor_p, 2), desc, banco_escolhido, forma])
                st.success("Lançamento concluído com sucesso!")
                st.rerun()

        with col_h:
            st.subheader("📊 Histórico Recente")
            dados_g = ws_gastos.get_all_records()
            if dados_g:
                df_g = pd.DataFrame(dados_g)
                st.dataframe(df_g.tail(15), use_container_width=True, hide_index=True)
            else:
                st.info("Nenhum gasto registrado ainda.")

    # --- ABA 2: BANCOS ---
    with tab_bancos:
        st.subheader("🏦 Cadastro de Bancos")
        with st.form("form_bancos"):
            n_banco = st.text_input("Nome do Banco (ex: Itaú)")
            s_inicial = st.number_input("Saldo Atual", step=100.0)
            if st.form_submit_button("Cadastrar"):
                ws_bancos.append_row([n_banco, s_inicial, "Corrente"])
                st.success("Banco cadastrado!")
                st.rerun()
        
        st.write("### Meus Bancos Cadastrados")
        b_list = ws_bancos.get_all_records()
        if b_list:
            st.table(pd.DataFrame(b_list))

    # --- ABA 3: CARTÕES ---
    with tab_cartoes:
        st.subheader("💳 Meus Cartões")
        with st.form("form_cartao"):
            n_cartao = st.text_input("Nome do Cartão")
            v_limite = st.number_input("Limite Total")
            v_venc = st.number_input("Dia de Vencimento", 1, 31, 10)
            v_fech = st.number_input("Dia de Fechamento", 1, 31, 3)
            if st.form_submit_button("Salvar Cartão"):
                ws_cartoes.append_row([n_cartao, v_limite, v_venc, v_fech])
                st.success("Cartão salvo!")
                st.rerun()
        
        st.write("### Cartões Ativos")
        c_list = ws_cartoes.get_all_records()
        if c_list:
            st.table(pd.DataFrame(c_list))

    # --- ABA 4: METAS ---
    with tab_metas:
        st.subheader("🎯 Metas de Economia")
        with st.form("form_metas"):
            meta_n = st.text_input("Objetivo (ex: Trocar Carro)")
            meta_v = st.number_input("Valor Necessário")
            if st.form_submit_button("Criar Meta"):
                ws_metas.append_row([meta_n, meta_v, "Em andamento"])
                st.success("Meta criada!")
                st.rerun()
        
        st.write("### Suas Metas")
        m_list = ws_metas.get_all_records()
        if m_list:
            st.table(pd.DataFrame(m_list))

except Exception as e:
    st.error(f"Erro no sistema: {e}")
    st.info("💡 Verifique se as abas 'bancos', 'cartoes' e 'metas' estão criadas exatamente com esses nomes em minúsculo.")
