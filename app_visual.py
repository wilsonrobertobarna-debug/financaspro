import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua chave original aqui)
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
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": "\n".join(PK_LIST)
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    dados = ws_lanc.get_all_records()
    df = pd.DataFrame(dados)
    
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Data_limpa'] = df['Data_dt'].dt.strftime('%d/%m/%Y')
        df['Valor_num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        if 'Tipo' not in df.columns: df['Tipo'] = 'Despesa'
        if 'Categoria' not in df.columns: df['Categoria'] = 'Outros'
        if 'Status' not in df.columns: df['Status'] = 'Pendente'

    # --- TAGS INDICADORAS ---
    st.title("💼 FinançasPro Wilson")
    if not df.empty:
        hoje = datetime.now()
        df_mes = df[df['Data_dt'].dt.month == hoje.month]
        
        rec_mes = df_mes[df_mes['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
        desp_mes = df_mes[df_mes['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
        
        rendimentos = df_mes[df_mes['Categoria'].astype(str).str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
        # Pendências: Despesas não marcadas como "Pago"
        pendencias = df[(df['Tipo'].str.contains('Despesa', case=False, na=False)) & (df['Status'] != 'Pago')]['Valor_num'].sum()

        t1, t2, t3, t4, t5 = st.columns(5)
        t1.metric("Receitas (Mês)", f"R$ {rec_mes:,.2f}")
        t2.metric("Despesas (Mês)", f"R$ {desp_mes:,.2f}")
        t3.metric("Saldo (R - D)", f"R$ {rec_mes - desp_mes:,.2f}")
        t4.metric("Rendimentos", f"R$ {rendimentos:,.2f}")
        t5.metric("Pendências", f"R$ {pendencias:,.2f}")

    st.divider()

    # --- FORMULÁRIO COM LIMPEZA AUTOMÁTICA ---
    col_form, col_hist = st.columns([1, 2.5])
    
    with col_form:
        st.subheader("📝 Novo Lançamento")
        
        # O segredo para limpar é o st.rerun() no final do botão 'Salvar'
        tipo_f = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        data_f = st.date_input("Data", datetime.now())
        valor_f = st.number_input("Valor (R$)", min_value=0.0, step=0.01, value=0.0)
        benef_f = st.text_input("Beneficiário/Origem", value="")
        cat_f = st.selectbox("Categoria", ["Aluguel", "Mercado", "Rendimento", "Trabalho", "Lazer", "Outros"])
        banco_f = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
        status_f = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.button("🚀 Salvar Lançamento", use_container_width=True):
            if valor_f > 0:
                ws_lanc.append_row([
                    data_f.strftime('%d/%m/%Y'), valor_f, cat_f, banco_f, 
                    "Manual", benef_f, "Pessoal", 0, "", status_f, tipo_f
                ])
                st.success("Dados gravados com sucesso!")
                # Este comando limpa a memória do formulário e recarrega a página com campos zerados
                st.rerun()
            else:
                st.warning("Por favor, insira um valor maior que zero.")

    with col_hist:
        st.subheader("🔍 Histórico Recente")
        if not df.empty:
            cols_ver = ['Data_limpa', 'Valor', 'Tipo', 'Banco', 'Beneficiário', 'Status']
            cols_e = [c for c in cols_ver if c in df.columns]
            st.dataframe(df[cols_e].sort_values('Data_dt', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
