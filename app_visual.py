import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import re

st.set_page_config(page_title="FinançasPro Wilson", layout="wide")
st.title("🛡️ FinançasPro Wilson: Reparador de Conexão")

# Área para colar a chave - Isso evita que o erro fique "preso" no código
entrada_chave = st.text_area("Cole aqui o conteúdo do seu arquivo JSON:", height=200, help="Pode colar tudo, o sistema vai filtrar o que importa.")

if entrada_chave:
    try:
        # --- FILTRO DE SEGURANÇA ---
        # 1. Busca apenas o que está entre os hífens (descarta underlines externos)
        match = re.search(r"-----BEGIN PRIVATE KEY-----[\s\S]+?-----END PRIVATE KEY-----", entrada_chave)
        
        if not match:
            st.error("🚨 Marcadores BEGIN/END não encontrados. Copie a chave completa do arquivo!")
        else:
            # 2. Limpa os \n e espaços extras
            chave_limpa = match.group(0).replace("\\n", "\n").strip()
            
            # 3. Tenta a conexão
            scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
            creds_info = {
                "type": "service_account",
                "project_id": "financaspro-wilson",
                "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
                "token_uri": "https://oauth2.googleapis.com/token",
                "private_key": chave_limpa
            }
            
            # Tenta autorizar
            client = gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))
            sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
            
            st.success("🔥 CONECTADO! Wilson, o motor do programa voltou a funcionar.")
            st.balloons()
            
            # Se conectou, mostra os dados para confirmar
            ws = sh.get_worksheet(0)
            st.write("Dados recuperados com sucesso:", ws.get_all_records()[-3:])

    except Exception as e:
        if "95" in str(e):
            st.error("❌ O caractere '_' (underline) ainda está infiltrado na chave.")
        else:
            st.error(f"Erro: {e}")
else:
    st.info("Aguardando você colar a chave para reativar o sistema...")
