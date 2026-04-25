import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
# IMPORTANTE: Mantenha as aspas e as vírgulas em cada linha da sua chave real.
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
   "Ns8Le56t5Bed2PmfMGXjTLBed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4",
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

# --- FUNÇÕES DE CALLBACK ---
def acao_salvar():
    v = st.session_state.valor_input
    if v > 0:
        data_br = st.session_state.data_input.strftime('%d/%m/%Y')
        desc_final = f"{st.session_state.desc_input} ({st.session_state.parcela_input})" if st.session_state.parcela_input != "1/1" else st.session_state.desc_input
        
        # Ordem para sua planilha (A até K)
        # J: Status | K: Tipo
        nova_linha = [
            data_br, v, st.session_state.cat_input, st.session_state.banco_input, 
            desc_final, st.session_state.benef_input, "Pessoal", "", "", 
            st.session_state.status_input, st.session_state.tipo_input
        ]
        
        ws_lanc.append_row(nova_linha)
        st.toast("✅ Lançamento enviado!")
        
        # Limpeza segura dos campos
        st.session_state.valor_input = 0.0
        st.session_state.benef_input = ""
        st.session_state.desc_input = ""
        st.session_state.parcela_input = "1/1"

def acao_excluir():
    id_alvo = st.session_state.id_excluir_input
    ws_lanc.delete_rows(int(id_alvo))
    st.toast(f"🗑️ Registro {id_alvo} removido.")

@st.cache_resource
def conectar_google():
    # A MUDANÇA CRÍTICA ESTÁ AQUI:
    # 1. strip() limpa espaços no fim das linhas
    # 2. replace converte os textos '\n' em quebras reais que o Google entende
    chave_limpa = "\n".join([l.strip() for l in PK_LIST]).replace('\\n', '\n')
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": "service_account", 
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", 
        "private_key": chave_limpa
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- PROCESSAMENTO ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    raw_data = ws_lanc.get_all_records()
    df = pd.DataFrame(raw_data)
    
    # Tratamento básico dos dados lidos
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        # Ajuste o nome das colunas conforme sua planilha real
        col_tipo = 'Tipo' if 'Tipo' in df.columns else 'Tipo Movimentação'
        
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        df['Valor_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson")

    # Filtros e Saldo
    if not df.empty:
        c1, c2 = st.columns(2)
        with c1:
            periodo = st.date_input("📅 Filtro:", value=(date(date.today().year, date.today().month, 1), date.today()), format="DD/MM/YYYY")
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_view = df[(df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)].copy()
            
            # Cálculo de saldo (ajustado para o nome da sua coluna de Tipo)
            rec = df_view[df_view[col_tipo].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_view[df_view[col_tipo].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            st.info(f"### 💰 Saldo: R$ {rec - desp:,.2f}")

    st.divider()

    # Formulário e Tabela
    col_f, col_h = st.columns([1, 2.5])
    
    with col_f:
        st.subheader("📝 Lançamento")
        st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, key="tipo_input")
        st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_input")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="valor_input")
        st.text_input("Descrição", key="desc_input")
        st.text_input("Beneficiário", key="benef_input")
        st.text_input("Parcela", value="1/1", key="parcela_input")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Trabalho", "Outros"], key="cat_input")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco"], key="banco_input")
        st.selectbox("Status", ["Pago", "Pendente"], key="status_input")
        st.button("🚀 Gravar", use_container_width=True, on_click=acao_salvar)

    with col_h:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df_view[['ID', 'Data', 'Valor', col_tipo, 'Descrição', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
            st.divider()
            st.number_input("ID para remover:", min_value=2, step=1, key="id_excluir_input")
            st.button("🔴 Excluir", use_container_width=True, on_click=acao_excluir)

except Exception as e:
    st.error(f"Erro detectado: {e}) # Faltou fechar a aspa aqui! "
