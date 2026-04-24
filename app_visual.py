import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# 2. CHAVE DE ACESSO (Mantenha sua chave completa aqui)
PK_LIST = ["--- SUA CHAVE AQUI ---"] 

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

    # --- ÁREA DE UPLOAD ---
    st.sidebar.header("📁 Importar CSV (11 Colunas)")
    uploaded_file = st.sidebar.file_uploader("Selecione o arquivo financas_bruta", type=['csv'])

    df_local = pd.DataFrame()

    if uploaded_file is not None:
        try:
            # Lendo o arquivo com detecção de separador e limpeza inicial
            df_local = pd.read_csv(uploaded_file, sep=None, engine='python', encoding='latin1')
            
            # PADRONIZAÇÃO DAS 11 COLUNAS: Tira espaços e acentos internos para o Python entender
            df_local.columns = [str(c).strip().lower().replace('ç', 'c').replace('ã', 'a') for c in df_local.columns]
            
            # LIMPEZA DA DATA
            if 'data' in df_local.columns:
                df_local['data_dt'] = pd.to_datetime(df_local['data'], dayfirst=True, errors='coerce')
                df_local = df_local.dropna(subset=['data_dt']) # Remove linhas sem data
                df_local['data'] = df_local['data_dt'].dt.strftime('%d/%m/%Y')
            
            # LIMPEZA DO VALOR
            if 'valor' in df_local.columns:
                df_local['valor'] = df_local['valor'].astype(str).str.replace('R$', '', regex=False)
                df_local['valor'] = df_local['valor'].str.replace('.', '', regex=False).str.replace(',', '.', regex=False).str.strip()
                df_local['valor_num'] = pd.to_numeric(df_local['valor'], errors='coerce').fillna(0)
                
            st.sidebar.success(f"✅ {len(df_local)} linhas prontas para processar!")
        except Exception as e:
            st.sidebar.error(f"Erro ao ler arquivo: {e}")

    # UNIÃO DOS DADOS
    df_all = pd.concat([df_nuvem, df_local], ignore_index=True)

    if not df_all.empty:
        # Garante as colunas de data e valor para o filtro final
        df_all['data_dt'] = pd.to_datetime(df_all['data'], dayfirst=True, errors='coerce').dt.date
        if 'valor_num' not in df_all.columns:
            df_all['valor_num'] = pd.to_numeric(df_all['valor'], errors='coerce').fillna(0)

        st.title("🛡️ FinançasPro Wilson")

        # FILTRO DE CALENDÁRIO
        periodo = st.date_input(
            "📅 Selecione o Período de Março/Abril:",
            value=(date(2026, 3, 1), date(2026, 4, 30)),
            format="DD/MM/YYYY"
        )

        if isinstance(periodo, tuple) and len(periodo) == 2:
            d_ini, d_fim = periodo
            df_filtrado = df_all[(df_all['data_dt'] >= d_ini) & (df_all['data_dt'] <= d_fim)].copy()

            if not df_filtrado.empty:
                # CÁLCULOS (Baseados na sua coluna 'tipo')
                # Procura por 'receita' ou 'despesa' de forma flexível
                rec = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('receita', case=False, na=False)]['valor_num'].sum()
                desp = df_filtrado[df_filtrado['tipo'].astype(str).str.contains('despesa', case=False, na=False)]['valor_num'].sum()
                
                c1, c2, c3 = st.columns(3)
                c1.metric("Faturamento (Receitas)", f"R$ {rec:,.2f}")
                c2.metric("Saídas (Despesas)", f"R$ {desp:,.2f}")
                c3.metric("Resultado Líquido", f"R$ {rec - desp:,.2f}")

                st.subheader("📋 Lista de Movimentações")
                st.dataframe(df_filtrado, use_container_width=True)
            else:
                st.warning(f"Nenhum dado encontrado no período {d_ini} a {d_fim}.")
                
                # RAIO-X: Se não aparecer nada, isso aqui vai dizer o porquê
                with st.expander("🔍 Raio-X do Arquivo (Diagnóstico)"):
                    st.write("Últimas datas lidas do seu arquivo:")
                    st.write(df_all['data'].tail(10).tolist())
                    st.write("Anos encontrados no arquivo:", df_all['data_dt'].apply(lambda x: x.year if x else None).unique())

except Exception as e:
    st.error(f"Erro no sistema: {e}")
