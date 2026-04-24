import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
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
    private_key = "\n".join([l.strip() for l in PK_LIST])
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": private_key
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    dados_nuvem = ws_lanc.get_all_records()
    df = pd.DataFrame(dados_nuvem)
    
    if os.path.exists('financas_bruta.csv'):
        df_bruto = pd.read_csv('financas_bruta.csv')
        df = pd.concat([df, df_bruto], ignore_index=True)

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        df['Valor_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson")

    # --- FILTROS ---
    if not df.empty:
        c1, c2 = st.columns([2, 2])
        with c1:
            hoje = date.today()
            periodo = st.date_input("📅 Período:", value=(date(hoje.year, hoje.month, 1), hoje), format="DD/MM/YYYY")
        with c2:
            busca = st.text_input("🔎 Pesquisar:", placeholder="Ex: Milo, Aluguel...")

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df[(df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)].copy()
            if busca:
                df_filtrado = df_filtrado[df_filtrado.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)]

            # CÁLCULOS
            rec = df_filtrado[df_filtrado['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_filtrado[df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            rend = df_filtrado[df_filtrado['Categoria'].str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
            pend = df_filtrado[(df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)) & (df_filtrado['Status'] != 'Pago')]['Valor_num'].sum()
            saldo = rec - desp

            # --- DESTAQUE: SALDO LÍQUIDO (TARJA AZUL) ---
            st.info(f"### 💰 Saldo Líquido do Período: R$ {saldo:,.2f}")

            # OUTRAS MÉTRICAS
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {desp:,.2f}")
            m3.metric("Rendimentos", f"R$ {rend:,.2f}")
            m4.metric("Pendências", f"R$ {pend:,.2f}")

            st.divider()

            # --- GRÁFICOS ---
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("📊 Receitas vs Despesas")
                st.bar_chart(pd.DataFrame({'Total': [rec, desp]}, index=['Receitas', 'Despesas']))
            with g2:
                exibir_metas = st.checkbox("🔑 Ver Metas (Privado)")
                if exibir_metas:
                    st.subheader("🎯 Metas de Faturamento")
                    META = 10000.00
                    st.bar_chart(pd.DataFrame({'Valor': [META, rec]}, index=['Meta', 'Alcançado']), color="#3498db")
                else:
                    st.info("Painel de metas oculto.")

    st.divider()

    # --- FORMULÁRIO (ESTRUTURA ORIGINAL PRESERVADA) ---
    c_form, c_hist = st.columns([1, 2.5])
    with c_form:
        st.subheader("📝 Novo Lançamento")
        tipo_f = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        data_f = st.date_input("Data", date.today())
        valor_f = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        benef_f = st.text_input("Beneficiário")
        desc_f = st.text_input("Descrição")
        cat_f = st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"])
        banco_f = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
        status_f = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.button("🚀 Salvar na Nuvem", use_container_width=True):
            if valor_f > 0:
                ws_lanc.append_row([data_f.strftime('%d/%m/%Y'), valor_f, cat_f, banco_f, desc_f, benef_f, "Pessoal", 0, "", status_f, tipo_f])
                st.success("Registrado!")
                st.rerun()

    with c_hist:
        st.subheader("📋 Detalhes")
        if not df_filtrado.empty:
            st.dataframe(df_filtrado[['Data', 'Valor', 'Descrição', 'Beneficiário', 'Status']].sort_values('Data', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro: {e}")
