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
    # Conexão com a planilha principal (Nuvem)
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_lanc = sh.get_worksheet(0)
    df_nuvem = pd.DataFrame(ws_lanc.get_all_records())
    
    st.title("🛡️ FinançasPro Wilson")

    # --- IMPORTAÇÃO DO ARQUIVO LOCAL ---
    with st.sidebar:
        st.header("📁 Importar Movimentação")
        uploaded_file = st.file_uploader("Suba o arquivo 'financas_bruta'", type=['csv'])

    df_local = pd.DataFrame()
    if uploaded_file is not None:
        try:
            # AJUSTE: Lendo com separador ';' conforme identificado no seu Drive
            df_local = pd.read_csv(uploaded_file, sep=';', encoding='latin1')
            
            # Padroniza nomes para evitar o erro 'valor_num'
            df_local = df_local.rename(columns={
                'Data': 'data',
                'Valor': 'valor_num', # Aqui resolvemos o erro!
                'Tipo': 'tipo'
            })
            
            # Converte valor para número (garantindo que seja float)
            df_local['valor_num'] = pd.to_numeric(df_local['valor_num'], errors='coerce').fillna(0.0)
            
            # Converte data
            df_local['data_dt'] = pd.to_datetime(df_local['data'], dayfirst=True, errors='coerce')
            df_local = df_local.dropna(subset=['data_dt'])
            
            st.sidebar.success(f"✅ {len(df_local)} lançamentos de Março carregados!")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler CSV: {e}")

    # UNIÃO E FILTRO
    df_final = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_final.empty:
        # Garante que a coluna de data para o filtro existe
        if 'data_dt' not in df_final.columns:
             df_final['data_dt'] = pd.to_datetime(df_final['Data'], dayfirst=True, errors='coerce')
        
        df_final['data_so_dia'] = df_final['data_dt'].dt.date

        # Seletor de Período focado em Março/Abril
        periodo = st.date_input("📅 Período:", value=(date(2026, 3, 1), date(2026, 4, 30)), format="DD/MM/YYYY")

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df_final[(df_final['data_so_dia'] >= d_ini) & (df_final['data_so_dia'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # Dashboard com nomes de colunas corrigidos
                rec = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('Receita', case=False, na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('Despesa', case=False, na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Faturamento", f"R$ {rec:,.2f}")
                c2.metric("Gastos (ex: Ração/Vacina)", f"R$ {desp:,.2f}")
                c3.metric("Saldo", f"R$ {rec - desp:,.2f}")

                st.subheader("📋 Lançamentos Encontrados")
                st.dataframe(df_filtrado[['data', 'tipo', 'valor_num', 'Descrição' if 'Descrição' in df_filtrado.columns else 'data']], use_container_width=True)

except Exception as e:
    st.error(f"Erro no sistema: {e}")
