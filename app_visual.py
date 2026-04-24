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
    
    st.title("🛡️ FinançasPro Wilson")

    # --- SIDEBAR: IMPORTAÇÃO ---
    with st.sidebar:
        st.header("📁 Importar Movimentação")
        uploaded_file = st.file_uploader("Upload financas_bruta", type=['csv'])

    df_local = pd.DataFrame()
    if uploaded_file is not None:
        try:
            # Tenta ler com separador automático
            df_local = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
            
            # NORMALIZAÇÃO RADICAL: Coloca tudo em minúsculo e remove espaços
            df_local.columns = [str(c).strip().lower() for c in df_local.columns]
            
            # SE AS COLUNAS NÃO FOREM ENCONTRADAS PELO NOME, USA A POSIÇÃO
            mapa_colunas = {
                'data': df_local.columns[0],
                'valor_bruto': df_local.columns[1],
                'tipo': df_local.columns[10] if len(df_local.columns) > 10 else df_local.columns[-1]
            }
            
            # Limpeza de Valor (Criação do valor_num)
            v = df_local[mapa_colunas['valor_bruto']].astype(str).str.replace('R$', '', regex=False)
            v = v.str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
            df_local['valor_num'] = pd.to_numeric(v, errors='coerce').fillna(0.0)
            
            # Limpeza de Data
            df_local['data_dt'] = pd.to_datetime(df_local[mapa_colunas['data']], dayfirst=True, errors='coerce')
            
            # Garante que a coluna 'tipo' exista no formato esperado
            df_local['tipo_limpo'] = df_local[mapa_colunas['tipo']].astype(str).str.lower()
            
            st.sidebar.success(f"✅ {len(df_local)} linhas lidas do CSV.")
        except Exception as e:
            st.sidebar.error(f"Erro no CSV: {e}")

    # UNIÃO DOS DADOS
    # Padroniza a nuvem para o mesmo formato do local
    if not df_nuvem.empty:
        df_nuvem.columns = [str(c).strip().lower() for c in df_nuvem.columns]
        if 'valor' in df_nuvem.columns:
            df_nuvem['valor_num'] = pd.to_numeric(df_nuvem['valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
        if 'data' in df_nuvem.columns:
            df_nuvem['data_dt'] = pd.to_datetime(df_nuvem['data'], dayfirst=True, errors='coerce')
        if 'tipo' in df_nuvem.columns:
            df_nuvem['tipo_limpo'] = df_nuvem['tipo'].astype(str).str.lower()

    df_final = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_final.empty:
        df_final['data_so_dia'] = df_final['data_dt'].dt.date

        # FILTRO DE PERÍODO
        periodo = st.date_input("📅 Selecione o Período:", value=(date(2026, 3, 1), date(2026, 4, 30)), format="DD/MM/YYYY")

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df_final[(df_final['data_so_dia'] >= d_ini) & (df_final['data_so_dia'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # CÁLCULOS USANDO AS COLUNAS NORMALIZADAS
                rec = df_filtrado[df_filtrado['tipo_limpo'].str.contains('receita', na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo_limpo'].str.contains('despesa', na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Receitas", f"R$ {rec:,.2f}")
                c2.metric("Despesas", f"R$ {desp:,.2f}")
                c3.metric("Saldo", f"R$ {rec - desp:,.2f}")

                st.subheader("📋 Lançamentos do Período")
                # Mostra as colunas originais de data e valor para o usuário conferir
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.warning("Nenhum lançamento encontrado entre as datas selecionadas.")
                with st.expander("🔍 Verifique se as datas foram lidas corretamente"):
                    st.write("Datas encontradas no arquivo:", df_final['data_dt'].dropna().unique())

except Exception as e:
    st.error(f"Erro Geral do Sistema: {e}")
