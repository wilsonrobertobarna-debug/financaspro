import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua chave privada real aqui)
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

# --- FUNÇÕES DE APOIO ---
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

def carregar_dados(ws):
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        df['Data_dt'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce').dt.date
        # Limpeza do valor para cálculo
        df['Valor_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)
    return df

# --- FUNÇÕES DE INTERAÇÃO (CALLBACKS) ---
def salvar_registro():
    """Esta função roda quando o botão de salvar é clicado."""
    if st.session_state.valor_input > 0:
        data_br = st.session_state.data_input.strftime('%d/%m/%Y')
        desc = st.session_state.desc_input
        parc = st.session_state.parcela_input
        desc_final = f"{desc} ({parc})" if parc != "1/1" else desc
        
        # Ordem corrigida para não trocar Status por 'Pessoal'
        # Estrutura: Data, Valor, Categoria, Banco, Descrição, Beneficiário, Conta, Aux1, Aux2, STATUS, TIPO
        nova_linha = [
            data_br, 
            st.session_state.valor_input, 
            st.session_state.cat_input, 
            st.session_state.banco_input, 
            desc_final, 
            st.session_state.benef_input, 
            "Pessoal", 0, "", 
            st.session_state.status_input, # Coluna J
            st.session_state.tipo_input   # Coluna K
        ]
        
        ws_lanc.append_row(nova_linha)
        
        # LIMPANDO OS CAMPOS (Zerar memória)
        st.session_state.valor_input = 0.0
        st.session_state.benef_input = ""
        st.session_state.desc_input = ""
        st.session_state.parcela_input = "1/1"
        st.toast("✅ Salvo com sucesso!")

def excluir_registro():
    """Esta função roda quando o botão de excluir é clicado."""
    id_alvo = st.session_state.id_excluir_input
    ws_lanc.delete_rows(int(id_alvo))
    st.toast(f"🗑️ Registro {id_alvo} removido!")
    st.session_state.id_excluir_input = 2

# --- INÍCIO DO APP ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    df = carregar_dados(ws_lanc)
    st.title("🛡️ FinançasPro Wilson")

    # --- ÁREA SUPERIOR (FILTROS E GRÁFICOS) ---
    if not df.empty:
        c1, c2 = st.columns([2, 2])
        with c1:
            hoje = date.today()
            periodo = st.date_input("📅 Período:", value=(date(hoje.year, hoje.month, 1), hoje), format="DD/MM/YYYY")
        
        with c2:
            st.write("🚀 Atalhos:")
            col_b1, col_b2 = st.columns(2)
            btn_matilha = col_b1.button("🐶 Matilha", use_container_width=True)
            btn_geral = col_b2.button("📄 Geral", use_container_width=True)

        # Lógica de Filtro
        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_view = df[(df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)].copy()
            if btn_matilha:
                df_view = df_view[df_view.astype(str).apply(lambda x: x.str.contains('Milo|Bolt', case=False)).any(axis=1)]

            # Métricas
            rec = df_view[df_view['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_view[df_view['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            rend = df_view[df_view['Categoria'].str.contains('Rendimento', case=False, na=False)]['Valor_num'].sum()
            pend = df_view[(df_view['Tipo'].str.contains('Despesa', case=False, na=False)) & (df_view['Status'] != 'Pago')]['Valor_num'].sum()

            st.info(f"### 💰 Saldo do Período: R$ {rec - desp:,.2f}")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Receitas", f"R$ {rec:,.2f}")
            m2.metric("Despesas", f"R$ {desp:,.2f}")
            m3.metric("Rendimentos", f"R$ {rend:,.2f}")
            m4.metric("Pendências", f"R$ {pend:,.2f}")

            # Gráficos
            st.divider()
            g1, g2 = st.columns(2)
            with g1:
                st.subheader("📊 Movimentação")
                st.bar_chart(pd.DataFrame({'Total': [rec, desp]}, index=['Receitas', 'Despesas']))
            with g2:
                if st.checkbox("🔑 Ver Metas"):
                    st.subheader("🎯 Meta vs Real")
                    st.bar_chart(pd.DataFrame({'Valor': [10000.0, rec]}, index=['Meta', 'Realizado']), color="#3498db")

    st.divider()

    # --- ÁREA INFERIOR (FORMULÁRIO E TABELA) ---
    c_form, c_table = st.columns([1, 2.5])

    with c_form:
        st.subheader("📝 Lançamento")
        st.radio("Tipo", ["Despesa", "Receita"], horizontal=True, key="tipo_input")
        st.date_input("Data", date.today(), format="DD/MM/YYYY", key="data_input")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="valor_input")
        st.text_input("Beneficiário", key="benef_input")
        st.text_input("Descrição", key="desc_input")
        st.text_input("Parcelamento", value="1/1", key="parcela_input")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"], key="cat_input")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"], key="banco_input")
        st.selectbox("Status", ["Pago", "Pendente"], key="status_input")
        
        # BOTÃO COM CALLBACK (Limpa tudo sozinho)
        st.button("🚀 Salvar na Nuvem", use_container_width=True, on_click=salvar_registro)

    with c_table:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df_view[['ID', 'Data', 'Valor', 'Tipo', 'Descrição', 'Beneficiário', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
            
            st.divider()
            st.subheader("🗑️ Excluir Registro")
            st.number_input("ID do registro:", min_value=2, step=1, key="id_excluir_input")
            st.button("🔴 Confirmar Exclusão", use_container_width=True, on_click=excluir_registro)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
