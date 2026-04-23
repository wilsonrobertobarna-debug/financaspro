import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. AUTENTICAÇÃO (Mantenha sua PK_LIST atualizada aqui)
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

    # --- ABA 1: LANÇAMENTOS (RESTAURADA) ---
    with tab_lanc:
        col_f, col_h = st.columns([1, 2])
        with col_f:
            st.subheader("📝 Novo Lançamento")
            with st.form("form_gasto", clear_on_submit=True):
                data_sel = st.date_input("Data", datetime.now())
                valor = st.number_input("Valor", min_value=0.0)
                desc = st.text_input("Descrição (Ex: Mercado)")
                
                # Carregar Bancos e Cartões dinamicamente
                b_list = [r['Nome'] for r in ws_bancos.get_all_records()] if ws_bancos.get_all_records() else ["Dinheiro"]
                c_list = [r['Nome'] for r in ws_cartoes.get_all_records()] if ws_cartoes.get_all_records() else []
                
                origem = st.selectbox("Conta/Cartão", b_list + c_list)
                forma = st.selectbox("Forma de Pagamento", ["Pix", "Crédito", "Débito", "Dinheiro"])
                parc = st.number_input("Parcelas", 1, 12, 1)
                
                if st.form_submit_button("Salvar"):
                    v_parc = valor / parc
                    for i in range(parc):
                        dt = (data_sel + relativedelta(months=i)).strftime('%d/%m/%Y')
                        ws_gastos.append_row([dt, round(v_parc, 2), f"{desc} ({i+1}/{parc})", origem, forma])
                    st.success("Lançado!")
                    st.rerun()

        with col_h:
            st.subheader("📋 Histórico")
            df_g = pd.DataFrame(ws_gastos.get_all_records())
            if not df_g.empty:
                st.dataframe(df_g.tail(10), use_container_width=True)
                if st.button("Limpar último lançamento"):
                    ws_gastos.delete_rows(len(df_g) + 1)
                    st.rerun()

    # --- ABA 2: BANCOS (COM EXCLUSÃO) ---
    with tab_bancos:
        st.subheader("🏦 Gerenciar Contas Bancárias")
        with st.form("f_banco"):
            n = st.text_input("Nome do Banco")
            s = st.number_input("Saldo Inicial")
            if st.form_submit_button("Adicionar"):
                ws_bancos.append_row([n, s])
                st.rerun()
        
        b_data = ws_bancos.get_all_records()
        if b_data:
            df_b = pd.DataFrame(b_data)
            st.table(df_b)
            idx_del = st.selectbox("Remover Banco", range(len(df_b)), format_func=lambda x: df_b.iloc[x]['Nome'])
            if st.button("Excluir Banco Selecionado"):
                ws_bancos.delete_rows(idx_del + 2)
                st.rerun()

    # --- ABA 3: CARTÕES (COM EXCLUSÃO) ---
    with tab_cartoes:
        st.subheader("💳 Gerenciar Cartões")
        with st.form("f_cartao"):
            c1, c2 = st.columns(2)
            n_c = c1.text_input("Nome do Cartão")
            l_c = c2.number_input("Limite")
            f_c = c1.number_input("Dia Fechamento", 1, 31, 5)
            v_c = c2.number_input("Dia Vencimento", 1, 31, 15)
            if st.form_submit_button("Cadastrar Cartão"):
                ws_cartoes.append_row([n_c, l_c, f_c, v_c])
                st.rerun()
        
        c_data = ws_cartoes.get_all_records()
        if c_data:
            df_c = pd.DataFrame(c_data)
            st.table(df_c)
            idx_c_del = st.selectbox("Remover Cartão", range(len(df_c)), format_func=lambda x: df_c.iloc[x]['Nome'])
            if st.button("Excluir Cartão Selecionado"):
                ws_cartoes.delete_rows(idx_c_del + 2)
                st.rerun()

    # --- ABA 4: METAS (COM EXCLUSÃO) ---
    with tab_metas:
        st.subheader("🎯 Gerenciar Metas")
        with st.form("f_meta"):
            obj = st.text_input("Objetivo")
            val = st.number_input("Valor Alvo")
            if st.form_submit_button("Salvar Meta"):
                ws_metas.append_row([obj, val, "Ativo"])
                st.rerun()
        
        m_data = ws_metas.get_all_records()
        if m_data:
            df_m = pd.DataFrame(m_data)
            st.table(df_m)
            idx_m_del = st.selectbox("Remover Meta", range(len(df_m)), format_func=lambda x: df_m.iloc[x]['Objetivo'])
            if st.button("Excluir Meta Selecionada"):
                ws_metas.delete_rows(idx_m_del + 2)
                st.rerun()

    # --- ABA 5: RELATÓRIOS (MULTI-GRÁFICOS) ---
    with tab_relat:
        st.header("📊 Inteligência Financeira")
        df_r = pd.DataFrame(ws_gastos.get_all_records())
        
        if not df_r.empty:
            df_r['Data'] = pd.to_datetime(df_r['Data'], dayfirst=True, errors='coerce')
            df_r['Valor'] = pd.to_numeric(df_r['Valor'])
            df_r['Mes'] = df_r['Data'].dt.strftime('%m/%Y')

            c1, c2 = st.columns(2)
            
            with c1:
                st.subheader("Gastos por Forma de Pagamento")
                fig1 = px.pie(df_r, values='Valor', names='Forma', hole=0.4)
                st.plotly_chart(fig1, use_container_width=True)

            with c2:
                st.subheader("Evolução Mensal")
                df_mes = df_r.groupby('Mes')['Valor'].sum().reset_index()
                fig2 = px.line(df_mes, x='Mes', y='Valor', markers=True)
                st.plotly_chart(fig2, use_container_width=True)
                
            st.markdown("---")
            st.subheader("💳 Faturas de Cartão (Mês Atual)")
            df_credito = df_r[(df_r['Forma'] == 'Crédito') & (df_r['Data'].dt.month == datetime.now().month)]
            if not df_credito.empty:
                fig3 = px.bar(df_credito.groupby('Banco')['Valor'].sum().reset_index(), x='Banco', y='Valor', color='Banco')
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.info("Sem gastos no crédito para este mês.")
        else:
            st.warning("Nenhum dado para exibir. Faça seu primeiro lançamento!")

except Exception as e:
    st.error(f"Ocorreu um erro: {e}")
