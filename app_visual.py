import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
# DICA: Pode colar o que quiser aqui, o código abaixo vai "garimpar" a chave real.
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP
... COLE O RESTO DA SUA CHAVE AQUI ...
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # --- HIGIENIZAÇÃO CIRÚRGICA ---
    raw_key = CHAVE_PRIVADA_BRUTA.strip()
    
    # 1. Busca apenas o que está entre os marcadores oficiais
    # Isso ignora automaticamente e-mails, underlines e outros textos que causam o erro 95.
    padrao = r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----"
    match = re.search(padrao, raw_key)
    
    if match:
        chave_extraida = match.group(0)
    else:
        # Se não achar os marcadores, tenta limpar o básico (fallback)
        chave_extraida = raw_key.replace("\\n", "\n")

    # 2. Garante que cada linha esteja limpa de espaços invisíveis
    linhas = [l.strip() for l in chave_extraida.split('\n') if l.strip()]
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

# --- FUNÇÕES DE AÇÃO ---
def acao_salvar():
    v = st.session_state.valor_input
    if v > 0:
        data_br = st.session_state.data_input.strftime('%d/%m/%Y')
        desc_final = f"{st.session_state.desc_input} ({st.session_state.parcela_input})" if st.session_state.parcela_input != "1/1" else st.session_state.desc_input
        
        # Estrutura de 11 colunas da sua planilha original
        nova_linha = [
            data_br, v, st.session_state.cat_input, st.session_state.banco_input, 
            desc_final, st.session_state.benef_input, "Pessoal", "", "", 
            st.session_state.status_input, st.session_state.tipo_input
        ]
        
        ws_lanc.append_row(nova_linha)
        st.toast("✅ Lançamento realizado!")
        
        st.session_state.valor_input = 0.0
        st.session_state.desc_input = ""
        st.session_state.benef_input = ""

def acao_excluir():
    id_alvo = st.session_state.id_excluir_input
    ws_lanc.delete_rows(int(id_alvo))
    st.toast(f"🗑️ Registro {id_alvo} removido.")

# --- INTERFACE PRINCIPAL ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    
    df = pd.DataFrame(ws_lanc.get_all_records())
    
    if not df.empty:
        df.columns = [str(c).strip() for c in df.columns]
        df['Data_dt'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce').dt.date
        df['Valor_num'] = pd.to_numeric(df['Valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), errors='coerce').fillna(0)
        df['ID'] = range(2, len(df) + 2)

    st.title("🛡️ FinançasPro Wilson")

    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            periodo = st.date_input("📅 Filtrar por Data:", value=(date(date.today().year, date.today().month, 1), date.today()), format="DD/MM/YYYY")
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_view = df[(df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)].copy()
            
            rec = df_view[df_view['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_view[df_view['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            with col2:
                st.metric("Saldo do Período", f"R$ {rec - desp:,.2f}")

    st.divider()

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
        st.button("🚀 Gravar no Google Sheets", use_container_width=True, on_click=acao_salvar)

    with col_h:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df_view[['ID', 'Data', 'Valor', 'Tipo', 'Descrição', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
            st.divider()
            st.number_input("ID para Excluir:", min_value=2, step=1, key="id_excluir_input")
            st.button("🔴 Remover Registro", use_container_width=True, on_click=acao_excluir)

except Exception as e:
    st.error(f"Erro na conexão: {e}")
