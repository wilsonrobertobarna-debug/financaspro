import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. SUA CHAVE DE ACESSO (Cole aqui sua lista de strings original)
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    "SUA_CHAVE_AQUI...",
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar_google():
    try:
        # TRATAMENTO DA CHAVE: Remove espaços e garante quebras de linha corretas
        # Isso resolve o erro de 'load_pem_private_key'
        private_key = "\n".join([line.strip() for line in PK_LIST if line.strip()])
        
        scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        
        creds_info = {
            "type": "service_account",
            "project_id": "financaspro-wilson",
            "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
            "token_uri": "https://oauth2.googleapis.com/token",
            "private_key": private_key
        }
        
        return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))
    except Exception as e:
        st.error(f"Erro na autenticação da chave: {e}")
        return None

# 3. LÓGICA DO SISTEMA
client = conectar_google()

if client:
    try:
        # Conexão com a planilha
        sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
        ws = sh.get_worksheet(0)
        
        # Carregando dados da Nuvem
        df = pd.DataFrame(ws.get_all_records())
        
        st.title("🛡️ FinançasPro Wilson")
        st.info("Sistema conectado à base de dados oficial.")

        if not df.empty:
            # Normalização (Tudo minúsculo para evitar erros de 'tipo' ou 'valor')
            df.columns = [str(c).strip().lower() for c in df.columns]
            
            # Conversão de Dados
            df['data_dt'] = pd.to_datetime(df['data'], dayfirst=True, errors='coerce')
            df['valor_num'] = pd.to_numeric(df['valor'].astype(str).replace(',', '.'), errors='coerce').fillna(0.0)
            df['data_so_dia'] = df['data_dt'].dt.date

            # Filtro de Período (Focado em Março/Abril)
            periodo = st.date_input("📅 Selecione o Período:", 
                                   value=(date(2026, 3, 1), date(2026, 4, 30)), 
                                   format="DD/MM/YYYY")

            if isinstance(periodo, tuple) and len(periodo) == 2:
                d_ini, d_fim = periodo
                df_filtrado = df[(df['data_so_dia'] >= d_ini) & (df['data_so_dia'] <= d_fim)].copy()

                if not df_filtrado.empty:
                    # Cálculos do Dashboard
                    rec = df_filtrado[df_filtrado['tipo'].str.contains('receita', case=False, na=False)]['valor_num'].sum()
                    desp = df_filtrado[df_filtrado['tipo'].str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                    
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Faturamento", f"R$ {rec:,.2f}")
                    c2.metric("Gastos", f"R$ {desp:,.2f}")
                    c3.metric("Saldo Líquido", f"R$ {rec - desp:,.2f}")

                    st.subheader("📋 Lançamentos Detalhados")
                    st.dataframe(df_filtrado[['data', 'valor', 'tipo', 'descrição']], use_container_width=True)
                else:
                    st.warning("Nenhum dado encontrado para o período selecionado.")
        else:
            st.warning("A planilha está vazia.")

    except Exception as e:
        st.error(f"Erro ao acessar a planilha: {e}")
