import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua chave original completa aqui)
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
    df_nuvem = pd.DataFrame(ws_lanc.get_all_records())
    if not df_nuvem.empty:
        df_nuvem.columns = [str(c).strip().lower() for c in df_nuvem.columns]

    # --- IMPORTAÇÃO ---
    st.sidebar.header("📁 Importar Arquivo")
    uploaded_file = st.sidebar.file_uploader("Upload financas_bruta", type=['csv'])

    df_local = pd.DataFrame()
    if uploaded_file is not None:
        try:
            df_local = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
            # Força mapeamento por posição
            df_local = df_local.rename(columns={
                df_local.columns[0]: 'data',
                df_local.columns[1]: 'valor',
                df_local.columns[10]: 'tipo'
            })
            # Tenta converter data (dia primeiro)
            df_local['data_dt'] = pd.to_datetime(df_local['data'], dayfirst=True, errors='coerce')
            df_local = df_local.dropna(subset=['data_dt'])
            
            # Limpa valor
            df_local['valor_num'] = pd.to_numeric(df_local['valor'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(), errors='coerce').fillna(0)
            
            st.sidebar.success(f"✅ {len(df_local)} linhas locais prontas!")
        except Exception as e:
            st.sidebar.error(f"Erro no CSV: {e}")

    # UNIÃO
    df_final = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_final.empty:
        df_final['data_dt'] = pd.to_datetime(df_final['data'], dayfirst=True, errors='coerce').dt.date
        
        st.title("🛡️ FinançasPro Wilson")

        # Seletor de Período
        periodo = st.date_input("📅 Filtrar por Data:", value=(date(2026, 3, 1), date(2026, 4, 30)), format="DD/MM/YYYY")

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df_final[(df_final['data_dt'] >= d_ini) & (df_final['data_dt'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # Dashboard
                if 'valor_num' not in df_filtrado.columns:
                    df_filtrado['valor_num'] = pd.to_numeric(df_filtrado['valor'], errors='coerce').fillna(0)

                rec = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('receita', case=False, na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Receitas", f"R$ {rec:,.2f}")
                c2.metric("Despesas", f"R$ {desp:,.2f}")
                c3.metric("Saldo", f"R$ {rec - desp:,.2f}")
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.warning(f"Nenhum dado para o filtro selecionado.")
                
                # DIAGNÓSTICO REAL: O que tem no arquivo?
                st.write("---")
                st.subheader("🔍 Diagnóstico do Arquivo")
                st.write("Aqui estão as datas que o sistema conseguiu ler do seu arquivo:")
                
                # Mostra as datas únicas para o Wilson conferir o ANO
                datas_lidas = df_final['data_dt'].dropna().unique()
                datas_lidas.sort()
                st.write(datas_lidas)
                
                st.info("Se você não vê datas de Março (03) ou Abril (04) de 2026 na lista acima, o problema está no arquivo Excel.")

except Exception as e:
    st.error(f"Erro: {e}")
