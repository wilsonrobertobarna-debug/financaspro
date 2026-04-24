import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# CHAVE DE ACESSO (Mantenha sua chave original aqui)
PK_LIST = ["..."] 

@st.cache_resource
def conectar_google():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds_info = {
        "type": "service_account", "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token", "private_key": "\n".join(PK_LIST)
    }
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    df_nuvem = pd.DataFrame(ws_lanc.get_all_records())
    
    st.title("🛡️ FinançasPro Wilson")

    # --- IMPORTAÇÃO ---
    with st.sidebar:
        st.header("📁 Importar Movimentação")
        uploaded_file = st.file_uploader("Suba o arquivo CSV", type=['csv'])

    df_local = pd.DataFrame()
    if uploaded_file is not None:
        try:
            # Lendo com detecção automática de separador
            df_local = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
            
            # NORMALIZAÇÃO: Transforma todos os nomes de colunas em minúsculo e sem espaços
            df_local.columns = [str(c).strip().lower() for c in df_local.columns]
            
            # MAPEAMENTO DE SEGURANÇA: Se não achar 'tipo', tenta 'tipo de lançamento' ou similares
            if 'tipo' not in df_local.columns:
                # Se houver pelo menos 11 colunas, sabemos que a 11ª (índice 10) é o tipo
                if len(df_local.columns) >= 11:
                    df_local = df_local.rename(columns={df_local.columns[10]: 'tipo'})
            
            # Limpeza de Valor e Data (repetindo a lógica de sucesso anterior)
            df_local['valor_num'] = pd.to_numeric(
                df_local.iloc[:, 1].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip(), 
                errors='coerce'
            ).fillna(0.0)
            
            df_local['data_dt'] = pd.to_datetime(df_local.iloc[:, 0], dayfirst=True, errors='coerce')
            st.sidebar.success(f"✅ {len(df_local)} linhas carregadas!")
        except Exception as e:
            st.sidebar.error(f"Erro no CSV: {e}")

    # UNIÃO DOS DADOS
    df_final = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_final.empty:
        # Padroniza TUDO para minúsculo antes de filtrar
        df_final.columns = [str(c).strip().lower() for c in df_final.columns]
        
        # Garante que as colunas essenciais existem para o código não quebrar
        for col in ['tipo', 'valor_num', 'data']:
            if col not in df_final.columns:
                df_final[col] = "" if col != 'valor_num' else 0.0

        df_final['data_dt'] = pd.to_datetime(df_final['data'], dayfirst=True, errors='coerce')
        df_final['data_so_dia'] = df_final['data_dt'].dt.date

        # FILTRO
        periodo = st.date_input("📅 Período:", value=(date(2026, 3, 1), date(2026, 4, 30)), format="DD/MM/YYYY")

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df_final[(df_final['data_so_dia'] >= d_ini) & (df_final['data_so_dia'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # Agora o 'tipo' (minúsculo) vai funcionar!
                rec = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('receita', case=False, na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Faturamento", f"R$ {rec:,.2f}")
                c2.metric("Despesas", f"R$ {desp:,.2f}")
                c3.metric("Saldo", f"R$ {rec - desp:,.2f}")

                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.warning("Nenhum dado encontrado no período.")
                with st.expander("🔍 Diagnóstico de Colunas"):
                    st.write("Colunas detectadas:", list(df_final.columns))

except Exception as e:
    st.error(f"Erro Geral: {e}")
