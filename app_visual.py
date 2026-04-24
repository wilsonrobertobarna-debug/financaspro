import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE DE ACESSO (MANTENHA AS TRÊS ASPAS)
# Cole sua chave inteira aqui. Mesmo que venha com pontos ou espaços, o código limpa.
CHAVE_BRUTA = """
-----BEGIN PRIVATE KEY-----
MIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQDF9qafCHj4HPHP
... (COLE O RESTANTE DA SUA CHAVE AQUI) ...
-----END PRIVATE KEY-----
"""

@st.cache_resource
def conectar_google():
    try:
        # --- LIMPEZA DE SEGURANÇA (O segredo está aqui) ---
        # 1. Remove os cabeçalhos para limpar o "miolo" da chave
        miolo = CHAVE_BRUTA.replace("-----BEGIN PRIVATE KEY-----", "").replace("-----END PRIVATE KEY-----", "")
        
        # 2. Remove TUDO que não for letra, número, +, / ou = (remove pontos e espaços)
        miolo_limpo = re.sub(r'[^a-zA-Z0-9+/=]', '', miolo)
        
        # 3. Reconstrói a chave no formato que o Google exige (blocos de 64 caracteres)
        linhas = [miolo_limpo[i:i+64] for i in range(0, len(miolo_limpo), 64)]
        chave_final = "-----BEGIN PRIVATE KEY-----\n" + "\n".join(linhas) + "\n-----END PRIVATE KEY-----\n"

        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        creds_info = {
            "type": "service_account",
            "project_id": "financaspro-wilson",
            "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
            "private_key": chave_final
        }
        
        return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))
    except Exception as e:
        st.error(f"Erro Crítico na Chave: {e}")
        return None

# 3. EXECUÇÃO DO SISTEMA
client = conectar_google()

if client:
    try:
        # Tenta abrir a planilha
        sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
        ws = sh.get_worksheet(0)
        
        # Lê os dados
        df = pd.DataFrame(ws.get_all_records())
        
        st.title("🛡️ FinançasPro Wilson")
        st.success("Conexão estabelecida com sucesso!")

        if not df.empty:
            # Padronização de Colunas
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Conversão de Dados
            df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
            df['valor_num'] = pd.to_numeric(
                df['valor'].astype(str).str.replace('R$', '', regex=False).str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip(), 
                errors='coerce'
            ).fillna(0.0)
            
            df['data_so_dia'] = df['data_dt'].dt.date

            # Filtro de Data
            periodo = st.date_input("📅 Selecione o Período:", value=(date(2026, 3, 1), date(2026, 4, 30)), format="DD/MM/YYYY")

            if isinstance(periodo, tuple) and len(periodo) == 2:
                d_ini, d_fim = periodo
                df_filtrado = df[(df['data_so_dia'] >= d_ini) & (df['data_so_dia'] <= d_fim)].copy()

                if not df_filtrado.empty:
                    rec = df_filtrado[df_filtrado['tipo'].str.contains('receita', case=False, na=False)]['valor_num'].sum()
                    desp = df_filtrado[df_filtrado['tipo'].str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Faturamento", f"R$ {rec:,.2f}")
                    c2.metric("Despesas", f"R$ {desp:,.2f}")
                    c3.metric("Saldo", f"R$ {rec - desp:,.2f}")

                    st.subheader("📋 Lançamentos Encontrados")
                    st.dataframe(df_filtrado[['data', 'valor', 'tipo', 'descrição']], use_container_width=True)
                else:
                    st.warning("Nenhum dado para este período.")
        else:
            st.warning("A planilha do Google está vazia.")

    except Exception as e:
        st.error(f"Erro ao acessar os dados da planilha: {e}")
