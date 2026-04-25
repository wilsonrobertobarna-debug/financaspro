import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="FinançasPro Wilson", 
    layout="wide", 
    page_icon="🛡️"
)

# 2. FUNÇÃO DE CONEXÃO AUTOMÁTICA (Busca no st.secrets)
@st.cache_resource(show_spinner="Acessando cofre de segurança...")
def conectar_google():
    try:
        # Puxa o bloco [connections.gsheets] que você salvou no Streamlit Cloud
        creds_info = st.secrets["connections"]["gsheets"]
        
        # O segredo do sucesso: o Python precisa que os \n sejam quebras reais
        # Isso garante que a biblioteca 'cryptography' não dê o erro 95
        private_key = creds_info["private_key"].replace("\\n", "\n")
        
        # Monta as credenciais finais
        final_creds = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": private_key,
            "client_email": creds_info["client_email"],
            "token_uri": creds_info["token_uri"],
        }
        
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro ao carregar segredos: {e}")
        st.info("💡 Wilson, verifique se você preencheu corretamente o painel 'Secrets' no Streamlit Cloud.")
        st.stop()

# 3. INTERFACE PRINCIPAL
st.title("🛡️ FinançasPro Wilson")
st.markdown("---")

try:
    # Inicia conexão
    client = conectar_google()
    
    # Abre a planilha pelo ID (ID da sua planilha FinançasPro)
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0)
    
    st.success("✅ Sistema Online e Automático!")

    # 4. EXIBIÇÃO DE DADOS
    st.subheader("📊 Lançamentos Recentes")
    dados = ws.get_all_records()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Métricas rápidas
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Registros", len(df))
        
        # Mostra a tabela (últimos 15 registros)
        st.dataframe(df.tail(15), use_container_width=True)
    else:
        st.warning("Nenhum dado encontrado na planilha.")

except Exception as e:
    st.error(f"Erro na execução: {e}")
