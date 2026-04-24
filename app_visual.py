import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import os
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Sua PK_LIST original)
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

# --- INÍCIO DA EXECUÇÃO ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    # Carregamento e União de Dados
    df = pd.DataFrame(ws_lanc.get_all_records())
    if os.path.exists('financas_bruta.csv'):
        df = pd.concat([df, pd.read_csv('financas_bruta.csv')], ignore_index=True)

    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        
        # Limpeza robusta do valor
        df['Valor_num'] = pd.to_numeric(
            df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), 
            errors='coerce'
        ).fillna(0)
        
        df['ID'] = range(2, len(df) + 2)

    # --- INTERFACE VISUAL ---
    st.title("🛡️ FinançasPro Wilson")
    st.caption("Controle Estratégico & Metas")

    # ZONA DE FILTROS (Calendário e Busca na mesma linha)
    c_data, c_busca = st.columns([2, 2])
    with c_data:
        hoje = date.today()
        # Inicia no dia 1 do mês atual
        periodo = st.date_input("📅 Escolha o Período:", value=(date(hoje.year, hoje.month, 1), hoje), format="DD/MM/YYYY")
    
    with c_busca:
        busca = st.text_input("🔎 Pesquisar:", placeholder="Ex: Milo, Mercado, Aluguel...")

    if isinstance(periodo, tuple) and len(periodo) == 2:
        d_ini, d_fim = periodo
        mask = (df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)
        
        if busca:
            mask = mask & df.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
        
        df_filtrado = df[mask].copy()

        # MÉTRICAS RÁPIDAS
        rec = df_filtrado[df_filtrado['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
        desp = df_filtrado[df_filtrado['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
        saldo = rec - desp

        st.write("---")
        m1, m2, m3 = st.columns(3)
        m1.metric("📈 Entradas", f"R$ {rec:,.2f}")
        m2.metric("📉 Saídas", f"R$ {desp:,.2f}")
        m3.metric("💰 Saldo Líquido", f"R$ {saldo:,.2f}", delta=f"{saldo:,.2f}")

        st.divider()

        # --- GRÁFICOS LADO A LADO ---
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader("📊 Movimentação do Período")
            chart_data = pd.DataFrame({'Tipo': ['Receitas', 'Despesas'], 'Total': [rec, desp]})
            st.bar_chart(chart_data.set_index('Tipo'), color="#2ecc71" if rec > desp else "#e74c3c")

        with col_g2:
            # Trava de Segurança para as Metas
            exibir_metas = st.checkbox("🔑 Ver Metas (Privado)")
            
            if exibir_metas:
                st.subheader("🎯 Metas de Faturamento")
                
                # Wilson, ajuste sua meta aqui (Valor em R$)
                META_ALVO = 10000.00 
                
                progresso = (rec / META_ALVO) * 100 if META_ALVO > 0 else 0
                
                meta_data = pd.DataFrame({
                    'Status': ['Objetivo', 'Alcançado'],
                    'Valor': [META_ALVO, rec]
                })
                
                st.bar_chart(meta_data.set_index('Status'), color="#3498db")
                st.info(f"Faturamento atual: {progresso:.1f}% da meta mensal.")
            else:
                st.info("Painel de metas oculto.")

        st.divider()

        # TABELA DE DETALHES
        st.subheader("📋 Detalhamento")
        colunas_exibir = ['Data', 'Valor', 'Tipo', 'Categoria', 'Descrição', 'Status']
        st.dataframe(
            df_filtrado[colunas_exibir].sort_values('Data', ascending=False),
            use_container_width=True,
            hide_index=True
        )

except Exception as e:
    st.error(f"Erro no sistema: {e}")
