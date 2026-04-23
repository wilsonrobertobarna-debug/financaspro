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
    ws = sh.get_worksheet(0)
    
    st.title("💼 FinançasPro Wilson - Desktop")
    
    tab_lanc, tab_bancos, tab_cartoes, tab_metas = st.tabs([
        "🚀 Lançamentos", 
        "🏦 Bancos", 
        "💳 Cartões", 
        "🎯 Metas"
    ])

    with tab_lanc:
        col_form, col_hist = st.columns([1, 2])
        
        with col_form:
            st.subheader("📝 Novo Registro")
            data_sel = st.date_input("Data da 1ª Parcela", datetime.now(), key="dt_lanc")
            valor_total = st.number_input("Valor Total (R$)", min_value=0.0, step=10.0, format="%.2f")
            parcelas = st.number_input("Nº de Parcelas", min_value=1, max_value=48, value=1)
            
            cat = st.selectbox("Categoria", ["Alimentação", "Transporte", "Casa", "Lazer", "Saúde", "Educação", "Outros"])
            
            # --- NOVOS CAMPOS ADICIONADOS AQUI ---
            beneficiario = st.text_input("Beneficiário", placeholder="Ex: Supermercado, Posto...")
            centro_custo = st.selectbox("Centro de Custo", ["Pessoal", "Família", "Trabalho", "Investimentos"])
            # -------------------------------------

            banco = st.selectbox("Banco Origem", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
            forma = st.selectbox("Forma de Pagamento", ["Cartão de Crédito", "Débito", "Pix", "Dinheiro"])
            
            if st.button("🚀 Salvar no Sistema", use_container_width=True):
                valor_parcela = valor_total / parcelas
                for i in range(parcelas):
                    data_p = data_sel + relativedelta(months=i)
                    data_str = data_p.strftime('%d/%m/%Y')
                    desc = f"{cat} ({i+1}/{parcelas})" if parcelas > 1 else cat
                    
                    # AGORA SALVANDO COM OS NOVOS CAMPOS (7 COLUNAS)
                    ws.append_row([data_str, round(valor_parcela, 2), desc, banco, forma, beneficiario, centro_custo])
                
                st.success(f"Registrado: {parcelas}x de R$ {valor_parcela:.2f}")
                st.rerun()

        with col_hist:
            st.subheader("📊 Últimos Movimentos")
            dados = ws.get_all_records()
            if dados:
                df = pd.DataFrame(dados)
                df.columns = [c.strip().capitalize() for c in df.columns]
                if 'Valor' in df.columns:
                    df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
                    st.dataframe(df.tail(10).style.format({"Valor": "R$ {:.2f}"}), use_container_width=True)
                else:
                    st.warning("Coluna 'Valor' não encontrada na planilha.")
            else:
                st.info("Nenhum dado encontrado.")

    # As outras abas permanecem exatamente iguais para manter a estabilidade
    with tab_bancos:
        st.subheader("🏦 Gestão de Contas Bancárias")
        if 'df' in locals():
            resumo_bancos = df.groupby('Banco')['Valor'].sum().reset_index()
            st.table(resumo_bancos.style.format({"Valor": "R$ {:.2f}"}))
        else:
            st.info("Lance dados para ver o resumo por banco.")

    with tab_cartoes:
        st.subheader("💳 Faturas e Limites")
        st.info("Em breve: Integração de limites e vencimento de faturas.")
        col_c1, col_c2 = st.columns(2)
        col_c1.metric("Fatura Nubank (Prox)", "R$ 1.250,00", delta="R$ 150,00")
        col_c2.metric("Limite Disponível", "R$ 5.000,00")

    with tab_metas:
        st.subheader("🎯 Minhas Metas Financeiras")
        meta_nome = "Reserva de Emergência"
        meta_valor = 10000.00
        saldo_atual = df['Valor'].sum() if 'df' in locals() else 0
        progresso = min(saldo_atual / meta_valor, 1.0)
        st.write(f"**Meta:** {meta_nome}")
        st.progress(progresso)
        st.write(f"Você já atingiu {progresso*100:.1f}% da sua meta de R$ {meta_valor:,.2f}")

except Exception as e:
    st.error(f"Erro no sistema: {e}")
