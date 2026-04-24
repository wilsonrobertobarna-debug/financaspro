import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantida intacta)
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
    ws_lanc = sh.get_worksheet(0)
    
    # Busca categorias dinâmicas
    try:
        ws_cat = sh.worksheet("categorias")
        df_cat = pd.DataFrame(ws_cat.get_all_records())
    except:
        df_cat = pd.DataFrame(columns=["Tipo", "Nome"])

    st.title("💼 FinançasPro Wilson")

    # --- CARREGAMENTO DE DADOS ---
    dados = ws_lanc.get_all_records()
    if dados:
        df = pd.DataFrame(dados)
        df.columns = [c.strip().capitalize() for c in df.columns]
        
        # Conversão de Data e Valor para cálculos
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Valor_Num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['Tipo'] = df['Tipo'].replace('', 'Despesa').fillna('Despesa')
        
        # --- CARDS DO TOPO (Mês Atual) ---
        hoje = datetime.now()
        df_mes_atual = df[df['Data_dt'].dt.month == hoje.month]
        
        c1, c2, c3 = st.columns(3)
        
        # Card 1: Rendimentos (Somente Receitas do Mês)
        receitas_mes = df_mes_atual[df_mes_atual['Tipo'] == 'Receita']['Valor_Num'].sum()
        c1.metric("Rendimentos (Mês)", f"R$ {receitas_mes:,.2f}")
        
        # Card 2: Saldo (Receita - Despesa do Mês)
        despesas_mes = df_mes_atual[df_mes_atual['Tipo'] == 'Despesa']['Valor_Num'].sum()
        c2.metric("Saldo do Mês", f"R$ {receitas_mes - despesas_mes:,.2f}")
        
        # Card 3: Pendências (Despesas até hoje)
        pendencias = df[(df['Tipo'] == 'Despesa') & (df['Data_dt'] <= hoje)]['Valor_Num'].sum()
        c3.metric("Pendências Totais", f"R$ {pendencias:,.2f}", delta_color="inverse")

    st.divider()

    # --- TABS ---
    tab_lanc, tab_bancos, tab_metas, tab_config = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "🎯 Metas", "⚙️ Configurações"
    ])

    with tab_lanc:
        col_form, col_hist = st.columns([1, 2.5])
        
        with col_form:
            # FORMULÁRIO (MANTIDO CONFORME SOLICITADO)
            st.subheader("📝 Novo Registro")
            tipo_mov = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
            lista_filtrada = df_cat[df_cat['Tipo'] == tipo_mov]['Nome'].tolist()
            cat = st.selectbox("Categoria", lista_filtrada if lista_filtrada else ["Geral"])
            data_sel = st.date_input("Data", datetime.now())
            valor_total = st.number_input("Valor (R$)", min_value=0.0, step=10.0)
            parcelas = st.number_input("Nº Parcelas", min_value=1, value=1)
            beneficiario = st.text_input("Beneficiário/Origem")
            centro_custo = st.selectbox("Centro de Custo", ["Pessoal", "Família", "Trabalho"])
            banco = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
            km = st.number_input("KM", min_value=0, value=0)
            
            if st.button("🚀 Salvar", use_container_width=True):
                valor_parcela = valor_total / parcelas
                for i in range(parcelas):
                    data_p = data_sel + relativedelta(months=i)
                    ws_lanc.append_row([data_p.strftime('%d/%m/%Y'), round(valor_parcela, 2), f"{cat} ({i+1}/{parcelas})" if parcelas > 1 else cat, banco, "Automático", beneficiario, centro_custo, km, "", "", tipo_mov])
                st.success("Salvo!")
                st.rerun()

        with col_hist:
            st.subheader("📊 Histórico e Filtros")
            
            # --- BARRA DE FILTROS ---
            f1, f2 = st.columns([1, 2])
            
            # Filtro por Mês
            meses_disponiveis = df['Data_dt'].dt.strftime('%m/%Y').unique().tolist()
            mes_filtro = f1.selectbox("Filtrar Mês", ["Todos"] + sorted(meses_disponiveis, reverse=True))
            
            # Barra de Busca Global
            busca = f2.text_input("🔍 Buscar (Beneficiário, Banco ou Descrição)")
            
            # Aplicação dos Filtros
            df_view = df.copy()
            if mes_filtro != "Todos":
                df_view = df_view[df_view['Data_dt'].dt.strftime('%m/%Y') == mes_filtro]
            
            if busca:
                df_view = df_view[
                    df_view['Beneficiário'].str.contains(busca, case=False, na=False) |
                    df_view['Banco'].str.contains(busca, case=False, na=False) |
                    df_view['Descrição'].str.contains(busca, case=False, na=False)
                ]
            
            st.dataframe(df_view.sort_values('Data_dt', ascending=False), use_container_width=True)

    # ... (Abas de Bancos, Metas e Configurações mantidas com a lógica anterior)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
