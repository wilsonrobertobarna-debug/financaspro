import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantida)
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
    "Ns8Le56t5Bed2PmfMGXjTLBed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB",
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
    
    # --- PROCESSAMENTO SEGURO ---
    dados = ws_lanc.get_all_records()
    df = pd.DataFrame(dados)
    
    if not df.empty:
        # LIMPEZA CRÍTICA: Remove espaços invisíveis e padroniza para "Centro de custo"
        df.columns = [str(c).strip().replace('  ', ' ') for c in df.columns]
        
        # Converte Data sem o erro 00:00:00
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df['Data_limpa'] = df['Data_dt'].dt.strftime('%d/%m/%Y')
        
        # Valor numérico
        df['Valor_num'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        # Garante coluna de Tipo
        if 'Tipo' not in df.columns:
            df['Tipo'] = 'Despesa'

    # --- CARDS (ORDEM SOLICITADA) ---
    st.title("💼 FinançasPro Wilson")
    c1, c2, c3 = st.columns(3)
    
    if not df.empty:
        hoje = datetime.now()
        df_mes = df[df['Data_dt'].dt.month == hoje.month]
        
        # Filtros insensíveis a maiúsculas/minúsculas
        rec = df_mes[df_mes['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
        desp = df_mes[df_mes['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
        
        c1.metric("Saldo do Mês (R - D)", f"R$ {rec - desp:,.2f}")
        c2.metric("Rendimentos (Mês)", f"R$ {rec:,.2f}")
        pend = df[(df['Tipo'].str.contains('Despesa', case=False, na=False)) & (df['Data_dt'] <= hoje)]['Valor_num'].sum()
        c3.metric("Pendências (Atual + Anterior)", f"R$ {pend:,.2f}")

    st.divider()

    # --- LAYOUT ---
    col_form, col_hist = st.columns([1, 2.5])
    
    with col_form:
        st.subheader("📝 Novo Registro")
        t_mov = st.radio("Tipo", ["Despesa", "Receita"], horizontal=True)
        dt_input = st.date_input("Data", datetime.now())
        vlr_input = st.number_input("Valor (R$)", min_value=0.0)
        benef_input = st.text_input("Beneficiário")
        
        # Verifica se a coluna existe na planilha para evitar o erro do "índice"
        lista_cc = ["Pessoal", "Família", "Trabalho"]
        cc_input = st.selectbox("Centro de Custo", lista_cc)
        
        banco_input = st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"])
        km_input = st.number_input("KM", min_value=0, value=0)
        
        if st.button("🚀 Salvar", use_container_width=True):
            ws_lanc.append_row([
                dt_input.strftime('%d/%m/%Y'), vlr_input, "Geral", banco_input, 
                "Automático", benef_input, cc_input, km_input, "", "", t_mov
            ])
            st.success("Salvo!")
            st.rerun()

    with col_hist:
        st.subheader("📊 Relatório")
        busca = st.text_input("🔎 Pesquisa (Data, Mês ou Beneficiário):")
        
        # Lista de colunas para exibir (apenas as que existirem de fato)
        cols_desejadas = ['Data_limpa', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Beneficiário', 'Centro de custo', 'Tipo']
        cols_para_ver = [c for c in cols_desejadas if c in df.columns]
        
        df_view = df[cols_para_ver].copy()
        
        if busca:
            mask = df_view.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)
            df_view = df_view[mask]
        
        st.dataframe(df_view.sort_values('Data_limpa', ascending=False), use_container_width=True, hide_index=True)

    # --- RODAPÉ: SALDO BANCOS ---
    if not df.empty:
        st.divider()
        st.subheader("🏦 Saldo por Banco")
        df['S_calc'] = df.apply(lambda x: x['Valor_num'] if "Receita" in str(x['Tipo']) else -x['Valor_num'], axis=1)
        res_banco = df.groupby('Banco')['S_calc'].sum().reset_index()
        
        cols = st.columns(len(res_banco) if len(res_banco) > 0 else 1)
        for i, r in res_banco.iterrows():
            with cols[i % len(cols)]:
                st.metric(r['Banco'], f"R$ {r['S_calc']:,.2f}")

except Exception as e:
    st.error(f"Erro corrigido: {e}")
