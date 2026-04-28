import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro de conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO DOS DADOS
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    
    # Criamos colunas técnicas escondidas para o sistema não travar
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df.sort_values('DT', ascending=False)

df_base = carregar()

# 4. NAVEGAÇÃO LATERAL (O esqueleto do programa)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# 5. CONTEÚDO DAS ABAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro - Resumo Geral")
    st.write("Aba de Finanças carregada com sucesso.")
    if not df_base.empty:
        # Exibição limpa: column_order esconde as colunas feias
        st.dataframe(df_base, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    st.write("Aba dos Pets pronta para receber os filtros.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    st.write("Aba do Veículo pronta para receber os filtros.")

elif aba == "📄 Relatórios":
    st.title("📄 Relatórios e Exportação")
    st.write("Aba de Relatórios pronta.")
