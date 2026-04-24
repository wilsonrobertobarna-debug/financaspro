import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
import os

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Sua chave original)
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
    
    # --- CARREGAMENTO DOS DADOS ---
    dados_nuvem = ws_lanc.get_all_records()
    df = pd.DataFrame(dados_nuvem)
    
    if os.path.exists('financas_bruta.csv'):
        df_bruto = pd.read_csv('financas_bruta.csv')
        df = pd.concat([df, df_bruto], ignore_index=True)

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        colunas_vitais = ['Data', 'Valor', 'Tipo', 'Status', 'Categoria', 'Banco', 'Beneficiário', 'Descrição']
        for col in colunas_vitais:
            if col not in df.columns: df[col] = ""

        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Valor_num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson (Visão Geral Completa)")

    # --- INDICADORES COMPLETOS ---
    if not df.empty:
        hoje = datetime.now()
        df_mes = df[df['Data_dt'].dt.month == hoje.month].copy()
        
        rec_mes = df_mes[df_mes['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
        desp_mes = df_mes[df_mes['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
        
        # Lógica para Rendimento (Categoria que contém a palavra Rendimento)
        rend_mes = df_mes[df_mes['Categoria'].astype(str).str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
        
        # Lógica para Pendências (Tudo que é despesa e não está "Pago")
        pend_total = df[(df['Tipo'].str.contains('Despesa', case=False, na=False)) & (df['Status'] != 'Pago')]['Valor_num'].sum()

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Receitas", f"R$ {rec_mes:,.2f}")
        m2.metric("Despesas", f"R$ {desp_mes:,.2f}")
        m3.metric("Saldo", f"R$ {rec_mes - desp_mes:,.2f}")
        m4.metric("Rendimentos", f"R$ {rend_mes:,.2f}")
        m5.metric("Pendências", f"R$ {pend_total:,.2f}")

        st.write("### 📊 Balanço Mensal")
        chart_df = pd.DataFrame({'Tipo': ['Receitas', 'Despesas'], 'Total': [rec_mes, desp_mes]})
        st.bar_chart(chart_df.set_index('Tipo'))

    st.divider()

    c_form, c_hist = st.columns([1, 2.5])
    
    with c_form:
        st.subheader("📝 Novo Lançamento")
        tipo_f = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        data_f = st.date_input("Data", datetime.now())
        valor_f = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        benef_f = st.text_input("Beneficiário")
        desc_f = st.text_input("Descrição")
        cat_f = st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"])
        banco_f = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
        status_f = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.button("🚀 Salvar", use_container_width=True):
            if valor_f > 0:
                ws_lanc.append_row([data_f.strftime('%d/%m/%Y'), valor_f, cat_f, banco_f, desc_f, benef_f, "Pessoal", 0, "", status_f, tipo_f])
                st.success("Salvo na Nuvem!")
                st.rerun()

    with c_hist:
        st.subheader("🔍 Histórico")
        if not df.empty:
            f1, f2 = st.columns(2)
            with f1: btn_pets = st.button("🐶 Filtro Milo & Bolt", use_container_width=True)
            with f2: btn_limpar = st.button("📄 Mostrar Tudo", use_container_width=True)
            
            busca = st.text_input("🔎 Pesquisar:")
            
            df_view = df[['ID', 'Data', 'Valor', 'Descrição', 'Beneficiário', 'Status']].copy()
            
            if btn_pets:
                mask = df.astype(str).apply(lambda x: x.str.contains('Milo|Bolt', case=False)).any(axis=1)
                df_view = df_view[mask]
            elif btn_limpar:
                st.rerun()
            elif busca:
                mask = df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
                df_view = df_view[mask]
            
            st.dataframe(df_view.sort_values('ID', ascending=False), use_container_width=True, hide_index=True)

            with st.expander("🗑️ Excluir Testes"):
                id_del = st.number_input("ID para apagar:", min_value=2, step=1)
                confirma = st.checkbox("Confirmar exclusão")
                if st.button("🔴 Apagar", use_container_width=True):
                    if confirma:
                        ws_lanc.delete_rows(int(id_del))
                        st.success(f"ID {id_del} removido!")
                        st.rerun()
        else:
            st.info("Sem dados.")

except Exception as e:
    st.error(f"Erro detectado: {e}")
