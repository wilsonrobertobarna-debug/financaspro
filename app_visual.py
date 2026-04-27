import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONEXÃO E CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

@st.cache_resource
def conectar_google():
    creds_info = st.secrets["connections"]["gsheets"]
    private_key = creds_info["private_key"].replace("\\n", "\n").strip()
    final_creds = {
        "type": creds_info["type"], "project_id": creds_info["project_id"],
        "private_key_id": creds_info["private_key_id"], "private_key": private_key,
        "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
    }
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 2. CARREGAMENTO (Com TTL baixo para evitar o erro de 'não apagar')
@st.cache_data(ttl=2)
def carregar_dados():
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        return df
    return pd.DataFrame()

df_base = carregar_dados()

# 3. INTERFACE SIMPLIFICADA PARA TESTE DE EXCLUSÃO
st.sidebar.title("🎮 Painel Wilson")
st.title("🛡️ FinançasPro - Gerenciador")

if not df_base.empty:
    st.subheader("📋 Últimos Lançamentos")
    st.dataframe(df_base.tail(10), use_container_width=True)

    # --- ÁREA DE EXCLUSÃO ---
    st.sidebar.write("---")
    st.sidebar.write("### ⚙️ Apagar Lançamento")
    
    # Criamos um ID que mistura a linha com a descrição para você ter certeza do que está apagando
    df_base['Linha'] = df_base.index + 2
    opcoes = {}
    for _, r in df_base.iloc[::-1].head(15).iterrows():
        label = f"Linha {r['Linha']} | {r['Data']} | {r['Descrição']} (R$ {r['Valor']})"
        opcoes[label] = r['Linha']
    
    item_selecionado = st.sidebar.selectbox("Selecione o item para remover:", [""] + list(opcoes.keys()))
    
    if item_selecionado:
        linha_para_deletar = opcoes[item_selecionado]
        st.sidebar.warning(f"Cuidado: Você vai apagar definitivamente a {item_selecionado}")
        
        if st.sidebar.button("🗑️ CONFIRMAR EXCLUSÃO"):
            # AÇÃO REAL NO GOOGLE SHEETS
            sh.get_worksheet(0).delete_rows(int(linha_para_deletar))
            
            # LIMPEZA TOTAL DE CACHE PARA O APP NÃO SE CONFUNDIR
            st.cache_data.clear()
            
            st.sidebar.success("✅ Item removido com sucesso!")
            st.rerun() # Força a atualização da tela
else:
    st.info("Nenhum dado encontrado na planilha.")
