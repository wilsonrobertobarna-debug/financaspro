import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import re

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE (COLE EXATAMENTE O QUE ESTÁ ENTRE AS ASPAS NO JSON)
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
COLE_SUA_CHAVE_AQUI
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # --- LIMPEZA RADICAL ---
    # 1. Resolve o problema do \n literal
    passo1 = CHAVE_PRIVADA_BRUTA.strip().replace("\\n", "\n")
    
    # 2. Extrai APENAS o que está entre os marcadores BEGIN e END
    # Isso joga fora qualquer e-mail (@) ou ponto (.) que tenha vindo junto
    match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", passo1)
    if not match:
        raise ValueError("Marcadores BEGIN/END não encontrados na chave!")
    
    chave_isolada = match.group(0)
    
    # 3. Limpa espaços invisíveis de cada linha
    linhas = [l.strip() for l in chave_isolada.split('\n') if l.strip()]
    chave_final = "\n".join(linhas)
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_info = {
        "type": "service_account", 
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", 
        "private_key": chave_final
    }
    
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- FUNÇÕES DE INTERAÇÃO ---
def acao_salvar():
    v = st.session_state.valor_input
    if v > 0:
        data_br = st.session_state.data_input.strftime('%d/%m/%Y')
        desc_final = f"{st.session_state.desc_input} ({st.session_state.parcela_input})" if st.session_state.parcela_input != "1/1" else st.session_state.desc_input
        
        nova_linha = [
            data_br, v, st.session_state.cat_input, st.session_state.banco_input, 
            desc_final, st.session_state.benef_input, "Pessoal", "", "", 
            st.session_state.status_input, st.session_state.tipo_input
        ]
        
        ws_lanc.append_row(nova_linha)
        st.toast("✅ Gravado com sucesso!")
        st.session_state.valor_input = 0.0
        st.session_state.desc_input = ""

# --- INTERFACE PRINCIPAL ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    df = pd.DataFrame(ws_lanc.get_all_records())
    
    st.title("🛡️ FinançasPro Wilson")

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
        st.button("🚀 Gravar Dados", use_container_width=True, on_click=acao_salvar)

    with col_h:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df.tail(10), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Erro na conexão: {e}")
