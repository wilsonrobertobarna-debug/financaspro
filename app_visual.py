import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Use a sua chave real aqui)
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

# --- CONEXÃO GOOGLE ---
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

# --- FUNÇÃO SALVAR (Resolve o sumiço e a troca de colunas) ---
def salvar_registro():
    # 1. Capturamos os dados IMEDIATAMENTE (Não limpamos nada agora)
    v_valor = st.session_state.valor_input
    
    if v_valor > 0:
        v_data = st.session_state.data_input.strftime('%d/%m/%Y')
        v_desc = st.session_state.desc_input
        v_parc = st.session_state.parcela_input
        v_benef = st.session_state.benef_input
        v_cat = st.session_state.cat_input
        v_banco = st.session_state.banco_input
        v_status = st.session_state.status_input
        v_tipo = st.session_state.tipo_input
        
        # Formata a descrição para não ir vazia
        desc_final = f"{v_desc} ({v_parc})" if v_parc != "1/1" else v_desc
        
        # 2. MONTAGEM DA LINHA (Padrão exato de 11 colunas)
        # A: Data | B: Valor | C: Cat | D: Banco | E: Desc | F: Benef | G: Conta | H: Obs1 | I: Obs2 | J: STATUS | K: TIPO
        nova_linha = [
            v_data, v_valor, v_cat, v_banco, desc_final, v_benef, 
            "Pessoal", # Coluna G (Fixo)
            "",        # Coluna H (Vazio)
            "",        # Coluna I (Vazio)
            v_status,  # Coluna J (Aqui cai o PAGO / PENDENTE)
            v_tipo     # Coluna K (Aqui cai RECEITA / DESPESA)
        ]
        
        # 3. Envia para o Google
        ws_lanc.append_row(nova_linha)
        
        # 4. SÓ AGORA LIMPAMOS OS CAMPOS
        st.session_state.valor_input = 0.0
        st.session_state.benef_input = ""
        st.session_state.desc_input = ""
        st.session_state.parcela_input = "1/1"
        st.toast("✅ Lançamento gravado e campos limpos!")

# --- INÍCIO DO APP ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    # Busca os dados para a tabela e métricas
    lista_dados = ws_lanc.get_all_records()
    df = pd.DataFrame(lista_dados)

    st.title("🛡️ FinançasPro Wilson")

    # --- PARTE DE CIMA (Métricas) ---
    if not df.empty:
        # Limpeza rápida das colunas
        df.columns = [str(c).strip() for c in df.columns]
        
        # Cálculo de métricas básicas
        if 'Valor' in df.columns and 'Tipo Movimentação' in df.columns:
            # Converte valor para número (remove R$, pontos e troca vírgula)
            df['V_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(), errors='coerce').fillna(0)
            
            c1, c2, c3 = st.columns(3)
            receitas = df[df['Tipo Movimentação'] == 'Receita']['V_num'].sum()
            despesas = df[df['Tipo Movimentação'] == 'Despesa']['V_num'].sum()
            
            c1.metric("Receitas", f"R$ {receitas:,.2f}")
            c2.metric("Despesas", f"R$ {despesas:,.2f}")
            c3.metric("Saldo", f"R$ {receitas - despesas:,.2f}", delta_color="normal")
    
    st.divider()

    # --- PARTE DE BAIXO (Formulário e Tabela) ---
    col_form, col_hist = st.columns([1, 2.5])

    with col_form:
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
        
        st.button("🚀 Salvar na Nuvem", use_container_width=True, on_click=salvar_registro)

    with col_hist:
        st.subheader("📋 Histórico")
        if not df.empty:
            # Mostra as últimas 15 linhas
            st.dataframe(df.tail(15), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum dado encontrado na planilha.")

except Exception as e:
    st.error(f"Erro no sistema: {e}")
    st.info("Dica: Verifique se os nomes das colunas na sua planilha batem com o código.")
