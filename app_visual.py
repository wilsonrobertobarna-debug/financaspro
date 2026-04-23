import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua PK_LIST atualizada abaixo)
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
    info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "private_key": "\n".join(PK_LIST),
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token"
    }
    creds = Credentials.from_service_account_info(info, scopes=scope)
    return gspread.authorize(creds)

# 3. FUNÇÃO PARA LER DADOS COM CACHE (O segredo para evitar o erro 429)
@st.cache_data(ttl=20) # Atualiza a cada 20 segundos se houver navegação
def get_data_safe(spreadsheet_id, worksheet_name):
    client = conectar()
    sh = client.open_by_key(spreadsheet_id)
    ws = sh.worksheet(worksheet_name)
    raw_data = ws.get_all_records()
    if not raw_data:
        return pd.DataFrame()
    df = pd.DataFrame(raw_data)
    df.columns = [str(c).strip().title() for c in df.columns]
    return df

# 4. FUNÇÃO PARA LIMPAR O CACHE APÓS UM SALVAMENTO
def limpar_cache():
    st.cache_data.clear()

try:
    SHEET_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    client = conectar()
    sh = client.open_by_key(SHEET_ID)

    st.title("💼 FinançasPro Wilson")

    tab_lanc, tab_bancos, tab_cartoes, tab_metas, tab_relat = st.tabs([
        "🚀 Lançamentos", "🏦 Bancos", "💳 Cartões", "🎯 Metas", "📊 Relatórios"
    ])

    # --- ABA 1: LANÇAMENTOS ---
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Lançamento")
            with st.form("form_gasto", clear_on_submit=True):
                dt_l = st.date_input("Data", datetime.now())
                vl_l = st.number_input("Valor", min_value=0.0)
                ds_l = st.text_input("Descrição")
                
                df_b = get_data_safe(SHEET_ID, "bancos")
                df_c = get_data_safe(SHEET_ID, "cartoes")
                
                bancos = df_b['Nome'].tolist() if not df_b.empty else ["Dinheiro"]
                cartoes = df_c['Nome'].tolist() if not df_c.empty else []
                
                origem = st.selectbox("Conta/Cartão", bancos + cartoes)
                forma = st.selectbox("Forma", ["Pix", "Crédito", "Débito", "Dinheiro"])
                parc = st.number_input("Parcelas", 1, 12, 1)
                
                if st.form_submit_button("🚀 Salvar"):
                    v_unit = vl_l / parc
                    ws_g = sh.get_worksheet(0)
                    for i in range(parc):
                        data_parc = (dt_l + relativedelta(months=i)).strftime('%d/%m/%Y')
                        ws_g.append_row([data_parc, round(v_unit, 2), f"{ds_l} ({i+1}/{parc})", origem, forma])
                    limpar_cache()
                    st.success("Lançado!")
                    st.rerun()

        with col_h:
            st.subheader("📋 Histórico")
            df_hist = get_data_safe(SHEET_ID, sh.get_worksheet(0).title)
            if not df_hist.empty:
                st.dataframe(df_hist.tail(10), use_container_width=True)

    # --- ABA 2: BANCOS ---
    with tab_bancos:
        st.subheader("🏦 Gestão de Contas")
        with st.form("f_banco"):
            nb = st.text_input("Nome do Banco")
            sb = st.number_input("Saldo")
            if st.form_submit_button("Adicionar"):
                sh.worksheet("bancos").append_row([nb, sb])
                limpar_cache()
                st.rerun()
        
        df_b_view = get_data_safe(SHEET_ID, "bancos")
        if not df_b_view.empty:
            st.table(df_b_view)
            idx_b = st.selectbox("Selecione para remover", range(len(df_b_view)), format_func=lambda x: df_b_view.iloc[x]['Nome'])
            if st.button("Remover Banco"):
                sh.worksheet("bancos").delete_rows(idx_b + 2)
                limpar_cache()
                st.rerun()

    # --- ABA 3: CARTÕES ---
    with tab_cartoes:
        st.subheader("💳 Cartões")
        with st.form("f_cartao"):
            nc = st.text_input("Nome do Cartão")
            lc = st.number_input("Limite")
            fc = st.number_input("Dia Fechamento", 1, 31, 5)
            vc = st.number_input("Dia Vencimento", 1, 31, 15)
            if st.form_submit_button("Cadastrar"):
                sh.worksheet("cartoes").append_row([nc, lc, fc, vc])
                limpar_cache()
                st.rerun()
        
        df_c_view = get_data_safe(SHEET_ID, "cartoes")
        if not df_c_view.empty:
            st.table(df_c_view)
            idx_c = st.selectbox("Selecione para remover", range(len(df_c_view)), format_func=lambda x: df_c_view.iloc[x]['Nome'], key="del_c")
            if st.button("Remover Selecionado"):
                sh.worksheet("cartoes").delete_rows(idx_c + 2)
                limpar_cache()
                st.rerun()

    # --- ABA 4: METAS ---
    with tab_metas:
        st.subheader("🎯 Suas Metas")
        with st.form("f_meta"):
            obj = st.text_input("Objetivo")
            alvo = st.number_input("Valor Alvo")
            if st.form_submit_button("Salvar Meta"):
                sh.worksheet("metas").append_row([obj, alvo, "Ativo"])
                limpar_cache()
                st.rerun()
        
        df_m_view = get_data_safe(SHEET_ID, "metas")
        if not df_m_view.empty:
            st.table(df_m_view)
            col_id = 'Objetivo' if 'Objetivo' in df_m_view.columns else df_m_view.columns[0]
            idx_m = st.selectbox("Remover", range(len(df_m_view)), format_func=lambda x: df_m_view.iloc[x][col_id])
            if st.button("Excluir Meta"):
                sh.worksheet("metas").delete_rows(idx_m + 2)
                limpar_cache()
                st.rerun()

    # --- ABA 5: RELATÓRIOS ---
    with tab_relat:
        st.header("📊 Painel Financeiro")
        df_rel = get_data_safe(SHEET_ID, sh.get_worksheet(0).title)
        if not df_rel.empty:
            df_rel['Data'] = pd.to_datetime(df_rel['Data'], dayfirst=True, errors='coerce')
            df_rel['Valor'] = pd.to_numeric(df_rel['Valor'], errors='coerce').fillna(0)
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(df_rel, values='Valor', names='Forma', title="Gastos por Pagamento"), use_container_width=True)
            with c2:
                df_m = df_rel.groupby(df_rel['Data'].dt.strftime('%m/%Y'))['Valor'].sum().reset_index()
                st.plotly_chart(px.bar(df_m, x='Data', y='Valor', title="Total por Mês"), use_container_width=True)
        else:
            st.info("Sem dados para análise.")

except Exception as e:
    # Se o erro for de cota, mostra uma mensagem amigável
    if "429" in str(e):
        st.error("🛑 Limite de leitura do Google atingido. Por favor, aguarde 60 segundos e recarregue a página.")
    else:
        st.error(f"Erro inesperado: {e}")
