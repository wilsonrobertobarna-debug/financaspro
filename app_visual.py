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
            [connections.gsheets]
type = "service_account"
project_id = "financaspro-wilson"
private_key_id = "723758e211e3ddf6c43ec9fbad55d0c933e3cc34"
private_key = """-----BEGIN PRIVATE KEY-----
\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP\ngcN1MxhHMlXJsmswR16gqEtwNmj1s4mLqZhifwA8qu7M16i6q0IU0RnQVufHfqNu\nBPQh74sLQ1/xrvNZ8q/A4fO/QqJCAhlqtYo3djsVRfDI/LOoUiP+clQzN3M+1Qdx\n74Df9cW6ELv3t8WpcCzBgkLX/3+V91dayvp+dr9OGRMTrVqDNRH8AnWDXdWlvhox\nKe7s3lFgk0JYU1ql6ffs0mdp9fJ6gB/MsKWcwZmbSIUGkrbiN5rfV9s8jANcNa1m\nkJ2tr3XsPsqpGcgOWF4pOrY0P++Xse4pgwppGa3WbBuPg4OzzK1LIgCuIvsGuRhs\nrwn3KZidAgMBAAECggEAB48kDKWPrPW5/BD57DM/xZQz92gzNJw9Dkhu3QGO33b0\nFRusQHKWCTsDtFm1zS717oKPiEeRQSpiRjS1N8iEWDFB7CIgk7ozINvf6Vk7hea7\nnroA5Z5DokvR5nLTz2UXj8NA2NXQtkD/MEgTdTnWy4SREOP5Db/FTbxSHhpY/lpq\nxlTlOIoKkk6gZyt3oCZAUzLo+R0CfG6jEJy+pwwk6stjRVKp8DnP/mrJV8LaU8Au\nfWxytSywY7XRxEjRHp2RplgVpQckuga3vbOcU0Y+FJNpkGT49DdH7PP7EEe/5J/t\nMcYkWUR1lvWDdlv/EzbO0GxqZ6FpPIA4MBO/krvPNwKBgQDwVqpWk48OkajwuMUL\nYGFE1dTWk0axmbiZa3bxK+laqBTt0sfuaiKemgRqQSy5kJS7f9qC02Evc+RC7nnQ\nBsSYeijNQiHwNcrjcbq6NGbCzYTcXu7FajM490tet7YF3XfGGTfuyA6GRYYpyNNT\nqwBeVGNtP4iXBeT3DSHaR3n/awKBgQDS3RVh1whP4Cu6CEOheUgQuMxEWdEbnQQS\nNs8Le56t5Bed2PmfMGXjTLBzDXPYiemGnDnPwm5SErTE0emZUo4+mzljSHAirpTB\nN9sNRi3pnLTnZ4YSHrmQlW3UxkNpgph+VMxmUM+HlKw0lutfoeYIjzIWa2ZImLGw\nGW7W8eJyFwKBgQCkOqR1OqnDy9cEf03uYzK0ZeXlpoflLmTNOXjyfg4ca8S5apJC\nIXZ8qEQiE10rhFeN9GTthuHfGjM9ZVYJx8YpZzhgYjNswGVenEV7nfkmXmfOanSA\no/xSjfGLzL9uLJL+5BarbTs3l2SBQwDdKHm8+69hZMvCXz3Bb9DVJoh/9wKBgDTz\nMXBdOAgeybwwYRNGSlNwpFKxnzHo7uHIA5vlkgYmlcucdaqE08ENO+3YPfPtRcf4\nqQfD0kIn0l7uO1O2CGQuRG3q/cWnw1D1vrsJmXPlVwQY2fDo6D4nV+orUzhGhBaN\nIrq6pjJsogWetEJSfFo/4xsAIzItrckDyfKN0QhHAoGBAN8pejg4WzSJjwrfTOgA\nVnARRsrH8VVQ8FSpfWTsYnJe/z0K3hxF4OiWM0oIkZsXhj62yjiZDizWApjwlhcW\nO02v3bvgkF+W/VSs/W1Rf0iMdp22KVEhL97fNWcfi/19QH+FRPeRzZpe2ujNcJyb\n1GHhDwH33nMtylvbUkBN8pBU\n
-----END PRIVATE KEY-----"""
client_email = "financas-wilson@financaspro-wilson.iam.gserviceaccount.com"
token_uri = "https://oauth2.googleapis.com/token"
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
