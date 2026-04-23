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

# 3. FUNÇÃO PARA LER DADOS COM LIMPEZA DE COLUNAS
def get_data_safe(worksheet):
    raw_data = worksheet.get_all_records()
    if not raw_data:
        return pd.DataFrame()
    df = pd.DataFrame(raw_data)
    # Remove espaços e padroniza para "Title Case"
    df.columns = [str(c).strip().title() for c in df.columns]
    return df

try:
    client = conectar()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    
    ws_gastos = sh.get_worksheet(0)
    ws_bancos = sh.worksheet("bancos")
    ws_cartoes = sh.worksheet("cartoes")
    ws_metas = sh.worksheet("metas")

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
                
                df_b_list = get_data_safe(ws_bancos)
                df_c_list = get_data_safe(ws_cartoes)
                
                bancos = df_b_list['Nome'].tolist() if not df_b_list.empty else ["Dinheiro"]
                cartoes = df_c_list['Nome'].tolist() if not df_c_list.empty else []
                
                origem = st.selectbox("Conta/Cartão", bancos + cartoes)
                forma = st.selectbox("Forma", ["Pix", "Crédito", "Débito", "Dinheiro"])
                parc = st.number_input("Parcelas", 1, 12, 1)
                
                if st.form_submit_button("🚀 Salvar"):
                    v_unit = vl_l / parc
                    for i in range(parc):
                        data_parc = (dt_l + relativedelta(months=i)).strftime('%d/%m/%Y')
                        ws_gastos.append_row([data_parc, round(v_unit, 2), f"{ds_l} ({i+1}/{parc})", origem, forma])
                    st.success("Lançado!")
                    st.rerun()

        with col_h:
            st.subheader("📋 Histórico")
            df_g = get_data_safe(ws_gastos)
            if not df_g.empty:
                st.dataframe(df_g.tail(10), use_container_width=True)

    # --- ABA 2: BANCOS ---
    with tab_bancos:
        st.subheader("🏦 Bancos")
        with st.form("f_banco"):
            nb = st.text_input("Nome")
            sb = st.number_input("Saldo")
            if st.form_submit_button("Salvar"):
                ws_bancos.append_row([nb, sb])
                st.rerun()
        df_b = get_data_safe(ws_bancos)
        if not df_b.empty:
            st.table(df_b)
            idx_b = st.selectbox("Remover", range(len(df_b)), format_func=lambda x: df_b.iloc[x]['Nome'])
            if st.button("Remover Banco"):
                ws_bancos.delete_rows(idx_b + 2)
                st.rerun()

    # --- ABA 3: CARTÕES ---
    with tab_cartoes:
        st.subheader("💳 Cartões")
        with st.form("f_cartao"):
            nc = st.text_input("Nome")
            lc = st.number_input("Limite")
            fc = st.number_input("Fechamento", 1, 31, 5)
            vc = st.number_input("Vencimento", 1, 31, 15)
            if st.form_submit_button("Cadastrar"):
                ws_cartoes.append_row([nc, lc, fc, vc])
                st.rerun()
        df_c = get_data_safe(ws_cartoes)
        if not df_c.empty:
            st.table(df_c)
            idx_c = st.selectbox("Remover Cartão", range(len(df_c)), format_func=lambda x: df_c.iloc[x]['Nome'])
            if st.button("Remover Selecionado"):
                ws_cartoes.delete_rows(idx_c + 2)
                st.rerun()

    # --- ABA 4: METAS ---
    with tab_metas:
        st.subheader("🎯 Metas")
        with st.form("f_meta"):
            obj = st.text_input("Objetivo")
            alvo = st.number_input("Alvo")
            if st.form_submit_button("Salvar"):
                ws_metas.append_row([obj, alvo, "Ativo"])
                st.rerun()
        df_m = get_data_safe(ws_metas)
        if not df_m.empty:
            st.table(df_m)
            col_id = 'Objetivo' if 'Objetivo' in df_m.columns else df_m.columns[0]
            idx_m = st.selectbox("Remover Meta", range(len(df_m)), format_func=lambda x: df_m.iloc[x][col_id])
            if st.button("Excluir"):
                ws_metas.delete_rows(idx_m + 2)
                st.rerun()

    # --- ABA 5: RELATÓRIOS ---
    with tab_relat:
        st.header("📊 Painel")
        df_r = get_data_safe(ws_gastos)
        if not df_r.empty:
            df_r['Data'] = pd.to_datetime(df_r['Data'], dayfirst=True, errors='coerce')
            df_r = df_r.dropna(subset=['Data'])
            df_r['Valor'] = pd.to_numeric(df_r['Valor']).fillna(0)
            
            c1, c2 = st.columns(2)
            with c1:
                st.plotly_chart(px.pie(df_r, values='Valor', names='Forma', title="Formas de Pagamento"), use_container_width=True)
            with c2:
                df_mes = df_r.groupby(df_r['Data'].dt.strftime('%m/%Y'))['Valor'].sum().reset_index()
                st.plotly_chart(px.bar(df_mes, x='Data', y='Valor', title="Gastos Mensais"), use_container_width=True)
        else:
            st.info("Sem dados para gráficos.")

except Exception as e:
    st.error(f"Erro no sistema: {e}")
