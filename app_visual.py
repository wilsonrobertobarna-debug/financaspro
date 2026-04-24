import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
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
    
    # Diagnóstico do CSV Local
    if os.path.exists('financas_bruta.csv'):
        df_bruto = pd.read_csv('financas_bruta.csv')
        # Tenta converter a coluna Data de forma flexível
        df_bruto['Data'] = pd.to_datetime(df_bruto['Data'], dayfirst=True, errors='coerce').dt.strftime('%d/%m/%Y')
        df = pd.concat([df, df_bruto], ignore_index=True)
        st.sidebar.success(f"✅ {len(df_bruto)} registros carregados do arquivo local.")
    else:
        st.sidebar.warning("⚠️ Arquivo 'financas_bruta.csv' não encontrado na pasta.")

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        # Converte para objeto de data real para o filtro do calendário funcionar
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        df['Valor_num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson")

    # --- SELETOR DE PERÍODO ---
    if not df.empty:
        # Pega a data mínima e máxima disponível nos dados para ajudar o usuário
        data_min = df['Data_dt'].min() if not df['Data_dt'].isnull().all() else date(2026, 1, 1)
        data_max = date.today()

        st.info(f"Dica: Seus dados começam em {data_min.strftime('%d/%m/%Y')}. Ajuste o calendário abaixo.")
        
        periodo = st.date_input(
            "📅 Selecione o intervalo (Início e Fim):",
            value=(data_min, data_max),
            format="DD/MM/YYYY"
        )
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            data_inicio, data_fim = periodo
            df_filtrado = df[(df['Data_dt'] >= data_inicio) & (df['Data_dt'] <= data_fim)].copy()
            
            # MÉTRICAS
            rec = df_filtrado[df_filtrado['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_filtrado[df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            rend = df_filtrado[df_filtrado['Categoria'].astype(str).str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
            pend = df_filtrado[(df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)) & (df_filtrado['Status'] != 'Pago')]['Valor_num'].sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {desp:,.2f}")
            m3.metric("Saldo", f"R$ {rec - desp:,.2f}")
            m4.metric("Rendimentos", f"R$ {rend:,.2f}")
            m5.metric("Pendências", f"R$ {pend:,.2f}")

            st.bar_chart(pd.DataFrame({'Tipo': ['Receitas', 'Despesas'], 'Total': [rec, desp]}).set_index('Tipo'))
            
            # HISTÓRICO
            st.divider()
            st.subheader(f"🔍 Registros de {data_inicio.strftime('%d/%m')} a {data_fim.strftime('%d/%m')}")
            st.dataframe(df_filtrado[['ID', 'Data', 'Valor', 'Descrição', 'Beneficiário', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning("Selecione as duas datas no calendário para ver os resultados.")

except Exception as e:
    st.error(f"Erro: {e}")
