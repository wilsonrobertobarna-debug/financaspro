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
    
    # Barra Lateral para Upload (Resolução do problema do arquivo sumido)
    st.sidebar.header("📁 Importar Março/Abril")
    uploaded_file = st.sidebar.file_uploader("Selecione o arquivo financas_bruta", type=['csv'])

    if uploaded_file is not None:
        try:
            # Tenta ler com vírgula, se falhar tenta ponto e vírgula
            try:
                df_bruto = pd.read_csv(uploaded_file, sep=',')
            except:
                df_bruto = pd.read_csv(uploaded_file, sep=';')
            
            # LIMPEZA DAS COLUNAS: Tira espaços e padroniza os nomes
            df_bruto.columns = [str(c).strip().title() for c in df_bruto.columns]
            
            # Verifica se a coluna Data existe após a limpeza
            if 'Data' in df_bruto.columns:
                df_bruto['Data_dt'] = pd.to_datetime(df_bruto['Data'], dayfirst=True, errors='coerce')
                df_bruto['Data'] = df_bruto['Data_dt'].dt.strftime('%d/%m/%Y')
                df = pd.concat([df, df_bruto], ignore_index=True)
                st.sidebar.success(f"✅ {len(df_bruto)} registros carregados!")
            else:
                st.sidebar.error(f"Coluna 'Data' não encontrada. Colunas lidas: {list(df_bruto.columns)}")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler arquivo: {e}")

    if not df.empty:
        df.columns = [str(c).strip().title() for c in df.columns]
        # Garante colunas mínimas para não dar erro no gráfico
        for col in ['Data', 'Valor', 'Tipo', 'Status', 'Categoria']:
            if col not in df.columns: df[col] = ""
            
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        df['Valor_num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson")

    # --- SELETOR DE PERÍODO ---
    if not df.empty:
        data_min = df['Data_dt'].min() if not pd.isnull(df['Data_dt'].min()) else date.today()
        data_max = date.today()
        
        st.info(f"📅 Dados disponíveis desde: {data_min.strftime('%d/%m/%Y')}")
        
        periodo = st.date_input(
            "Selecione o intervalo no calendário:",
            value=(data_min, data_max),
            format="DD/MM/YYYY"
        )
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            data_ini, data_fim = periodo
            df_filtrado = df[(df['Data_dt'] >= data_ini) & (df['Data_dt'] <= data_fim)].copy()
            
            # CÁLCULO DAS 5 TAGS (Métricas)
            rec = df_filtrado[df_filtrado['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_filtrado[df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            rend = df_filtrado[df_filtrado['Categoria'].str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
            pend = df_filtrado[(df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)) & (df_filtrado['Status'] != 'Pago')]['Valor_num'].sum()

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {desp:,.2f}")
            m3.metric("Saldo", f"R$ {rec - desp:,.2f}")
            m4.metric("Rendimentos", f"R$ {rend:,.2f}")
            m5.metric("Pendências", f"R$ {pend:,.2f}")

            st.write(f"### 📊 Balanço de {data_ini.strftime('%d/%m')} até {data_fim.strftime('%d/%m')}")
            chart_df = pd.DataFrame({'Tipo': ['Receitas', 'Despesas'], 'Total': [rec, desp]})
            st.bar_chart(chart_df.set_index('Tipo'))

            st.divider()
            st.subheader("🔍 Histórico do Período")
            st.dataframe(df_filtrado[['ID', 'Data', 'Valor', 'Descrição', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
        else:
            st.warning("⚠️ Selecione a data final no calendário.")

except Exception as e:
    st.error(f"Erro crítico no sistema: {e}")
