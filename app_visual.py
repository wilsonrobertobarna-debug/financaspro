import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# CHAVE DE ACESSO (Sua chave original)
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
    
    st.title("🛡️ FinançasPro Wilson")

    # --- IMPORTAÇÃO ---
    with st.sidebar:
        st.header("📁 Importar Movimentação")
        uploaded_file = st.file_uploader("Suba seu arquivo CSV", type=['csv'])

    df_local = pd.DataFrame()
    if uploaded_file is not None:
        try:
            # Lê o CSV ignorando erros de linha e detectando separador
            df_local = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1', on_bad_lines='skip')
            
            # Força o mapeamento (0: Data, 1: Valor, 10: Tipo)
            df_local = df_local.rename(columns={
                df_local.columns[0]: 'data',
                df_local.columns[1]: 'valor',
                df_local.columns[10]: 'tipo'
            })
            
            # Limpeza do Valor para número
            v = df_local['valor'].astype(str).str.replace('R$', '', regex=False)
            v = v.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df_local['valor_num'] = pd.to_numeric(v, errors='coerce').fillna(0.0)
            
            st.sidebar.success(f"✅ CSV Lido: {len(df_local)} linhas.")
        except Exception as e:
            st.sidebar.error(f"Erro no CSV: {e}")

    # UNIÃO DOS DADOS
    df_final = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_final.empty:
        # PADRONIZAÇÃO DE COLUNAS
        df_final.columns = [str(c).strip().lower() for c in df_final.columns]
        
        # TENTA CONVERTER DATA DE VÁRIOS JEITOS
        # Jeito 1: Dia/Mês/Ano
        df_final['data_dt'] = pd.to_datetime(df_final['data'], dayfirst=True, errors='coerce')
        # Se falhou, tenta Jeito 2: Ano-Mês-Dia (comum em exportações)
        df_final['data_dt'] = df_final['data_dt'].fillna(pd.to_datetime(df_final['data'], errors='coerce'))
        
        # Converte para apenas data (sem hora) para o filtro
        df_final['data_so_dia'] = df_final['data_dt'].dt.date

        # SELETOR DE PERÍODO (Inicia em Março de 2026)
        periodo = st.date_input(
            "📅 Selecione o Período:",
            value=(date(2026, 3, 1), date(2026, 4, 30)),
            format="DD/MM/YYYY"
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            # Filtro rigoroso
            df_filtrado = df_final[(df_final['data_so_dia'] >= d_ini) & (df_final['data_so_dia'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # Dashboard
                rec = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('receita', case=False, na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Faturamento", f"R$ {rec:,.2f}")
                c2.metric("Gastos", f"R$ {desp:,.2f}")
                c3.metric("Resultado", f"R$ {rec - desp:,.2f}")

                st.subheader("📋 Detalhamento do Período")
                st.dataframe(df_filtrado[['data', 'valor', 'tipo']], use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado para o filtro selecionado.")
                
                # O SEGREDO ESTÁ AQUI: RAIO-X PARA O WILSON
                with st.expander("🔍 Ver o que o sistema encontrou (Diagnóstico)"):
                    st.write("Aqui estão as datas brutas que vieram do seu arquivo:")
                    st.write(df_final['data'].unique())
                    st.write("Aqui estão as datas que o sistema conseguiu entender:")
                    st.write(df_final['data_so_dia'].dropna().unique())

except Exception as e:
    st.error(f"Erro no sistema: {e}")
