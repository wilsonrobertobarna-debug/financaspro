import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO
# Cole aqui o conteúdo da sua "private_key" do arquivo .json
CHAVE_PRIVADA_BRUTA = """-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP
... (COLE O RESTO DA SUA CHAVE AQUI) ...
-----END PRIVATE KEY-----"""

@st.cache_resource
def conectar_google():
    # LIMPEZA PROFUNDA: 
    # 1. Remove espaços em branco no início e fim
    # 2. Converte o texto "\n" literal em quebras de linha reais
    # 3. Limpa espaços invisíveis no final de cada linha interna
    linhas = CHAVE_PRIVADA_BRUTA.strip().replace('\\n', '\n').split('\n')
    chave_limpa = "\n".join([l.strip() for l in linhas if l.strip()])
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    
    creds_info = {
        "type": "service_account", 
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", 
        "private_key": chave_limpa
    }
    
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

# --- FUNÇÕES DE INTERAÇÃO ---
def acao_salvar():
    v = st.session_state.valor_input
    if v > 0:
        data_br = st.session_state.data_input.strftime('%d/%m/%Y')
        desc_final = f"{st.session_state.desc_input} ({st.session_state.parcela_input})" if st.session_state.parcela_input != "1/1" else st.session_state.desc_input
        
        # Estrutura de 11 colunas para manter sua planilha organizada
        nova_linha = [
            data_br, v, st.session_state.cat_input, st.session_state.banco_input, 
            desc_final, st.session_state.benef_input, "Pessoal", "", "", 
            st.session_state.status_input, st.session_state.tipo_input
        ]
        
        ws_lanc.append_row(nova_linha)
        st.toast("✅ Lançamento gravado!")
        
        # Limpeza automática dos campos
        st.session_state.valor_input = 0.0
        st.session_state.desc_input = ""
        st.session_state.benef_input = ""

def acao_excluir():
    id_alvo = st.session_state.id_excluir_input
    ws_lanc.delete_rows(int(id_alvo))
    st.toast(f"🗑️ Registro {id_alvo} removido.")

# --- LÓGICA PRINCIPAL ---
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
        periodo = st.date_input("📅 Filtrar Data:", value=(date(date.today().year, date.today().month, 1), date.today()), format="DD/MM/YYYY")
        
        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_view = df[(df['Data_dt'] >= d_ini) & (df['Data_dt'] <= d_fim)].copy()
            
            rec = df_view[df_view['Tipo'].str.contains('Receita', case=False, na=False)]['Valor_num'].sum()
            desp = df_view[df_view['Tipo'].str.contains('Despesa', case=False, na=False)]['Valor_num'].sum()
            st.info(f"### 💰 Saldo Atual: R$ {rec - desp:,.2f}")

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
        st.button("🚀 Gravar", use_container_width=True, on_click=acao_salvar)

    with col_h:
        st.subheader("📋 Histórico")
        if not df.empty:
            st.dataframe(df_view[['ID', 'Data', 'Valor', 'Tipo', 'Descrição', 'Status']].sort_values('ID', ascending=False), use_container_width=True, hide_index=True)
            st.divider()
            st.number_input("Excluir ID:", min_value=2, step=1, key="id_excluir_input")
            st.button("🔴 Remover Registro", use_container_width=True, on_click=acao_excluir)

except Exception as e:
    st.error(f"Erro detectado: {e}")
