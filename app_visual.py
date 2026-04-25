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

# 2. FUNÇÃO DE CONEXÃO BLINDADA (Lê do st.secrets)
@st.cache_resource(show_spinner="Acessando cofre de segurança...")
def conectar_google():
    try:
        # Puxa os dados que você salvou no painel 'Secrets' do Streamlit Cloud
        creds_info = st.secrets["connections"]["gsheets"]
        
        # O segredo do sucesso: o Python precisa que os \n sejam quebras reais
        # Isso resolve o erro 95 de uma vez por todas
        private_key = creds_info["private_key"].replace("\\n", "\n")
        
        # Monta o dicionário final para o Google
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
        st.info("💡 Certifique-se de que preencheu o campo 'Secrets' no painel do Streamlit Cloud.")
        st.stop()

# 3. INTERFACE PRINCIPAL
st.title("🛡️ FinançasPro Wilson")
st.markdown("---")

try:
    # Inicia conexão
    client = conectar_google()
    
    # Abre a sua planilha pelo ID (mantive o ID que estávamos usando)
    # Dica: Você também pode colocar esse ID nos Secrets se quiser!
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0) # Pega a primeira aba
    
    st.success("✅ Conexão Automática Ativa!")

    # 4. ÁREA DE VISUALIZAÇÃO
    st.subheader("📊 Resumo de Lançamentos")
    dados = ws.get_all_records()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Pequeno resumo financeiro
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Registros", len(df))
        
        # Mostra a tabela limpa
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("A planilha parece estar vazia ou não foi lida corretamente.")

except Exception as e:
    st.error(f"Erro na execução do app: {e}")
