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

# 2. FUNÇÃO DE CONEXÃO AUTOMÁTICA
@st.cache_resource(show_spinner="Conectando ao cofre de segurança...")
def conectar_google():
    try:
        # Tenta acessar o bloco principal de conexões
        if "connections" in st.secrets and "gsheets" in st.secrets["connections"]:
            creds_info = st.secrets["connections"]["gsheets"]
        else:
            st.error("❌ Erro: A estrutura [connections.gsheets] não foi encontrada no painel de Secrets.")
            st.stop()
            
        # Limpa e formata a chave privada (resolve o erro 95)
        # O .strip() remove espaços extras que podem vir na colagem
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        
        # Mapeamento rigoroso das chaves do dicionário
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
    
    except KeyError as e:
        st.error(f"❌ Erro: A chave {e} está faltando no seu painel de Secrets.")
        st.info("Verifique se você digitou exatamente: type, project_id, private_key_id, private_key, client_email e token_uri.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erge de conexão: {e}")
        st.stop()

# 3. INTERFACE PRINCIPAL
st.title("🛡️ FinançasPro Wilson")
st.markdown("---")

try:
    # Chama a conexão
    client = conectar_google()
    
    # ID da sua planilha (Já validado anteriormente)
    PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
    sh = client.open_by_key(PLANILHA_ID)
    ws = sh.get_worksheet(0)
    
    st.success("✅ Sistema Online! Conexão automática via Secrets estabelecida.")

    # 4. EXIBIÇÃO DE DADOS
    st.subheader("📊 Lançamentos Recentes")
    dados = ws.get_all_records()
    
    if dados:
        df = pd.DataFrame(dados)
        
        # Métricas de resumo
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total de Registros", len(df))
        
        # Tabela interativa
        st.dataframe(df.tail(20), use_container_width=True)
    else:
        st.warning("Conectado com sucesso, mas a planilha não retornou dados.")

except Exception as e:
    st.error(f"Erro ao carregar os dados da planilha: {e}")
    st.info("Dica: Verifique se a planilha foi compartilhada com o e-mail da conta de serviço.")
