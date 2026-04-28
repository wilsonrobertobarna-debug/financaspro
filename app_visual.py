import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

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

# 2. FUNÇÕES DE SUPORTE
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Linha'] = range(2, len(df) + 2)
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    
    # CRÍTICO: DT_ORDEM força o Python a entender que o DIA vem antes do MÊS (formato BR)
    df['DT_ORDEM'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    
    return df.sort_values(['DT_ORDEM', 'ID_Linha'])

def m_fmt(n): 
    if n == "" or pd.isna(n) or n == 0: return "R$ 0,00"
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

df_base = carregar()

# 3. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

if aba == "📊 Extrato Diário":
    st.title("📊 Extrato Diário")
    
    if df_base.empty:
        st.warning("Sem dados na planilha.")
    else:
        # CORREÇÃO DA PESQUISA: format="DD/MM/YYYY" garante o visual brasileiro
        c1, c2, c3 = st.columns([1, 1, 2])
        d_ini = c1.date_input("Início", datetime.now().replace(day=1), format="DD/MM/YYYY")
        d_fim = c2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
        b_sel = c3.selectbox("Filtrar por Banco:", sorted(df_base['Banco'].unique()))
        
        # Aplicando os filtros
        df_f = df_base[
            (df_base['Banco'] == b_sel) & 
            (df_base['DT_ORDEM'].dt.date >= d_ini) & 
            (df_base['DT_ORDEM'].dt.date <= d_fim)
        ].copy()
        
        # Preparando valor para exibição
        df_f['Valor_Exibir'] = df_f.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] not in ['Receita', 'Rendimento', 'Entrada'] else m_fmt(r['V_Num']), axis=1)

        st.divider()

        # TABELA DE EXIBIÇÃO
        st.dataframe(
            df_f.iloc[::-1], # Mais recente no topo
            column_order=("ID_Linha", "Data", "Descrição", "Tipo", "Status", "Valor_Exibir"),
            column_config={
                "ID_Linha": st.column_config.TextColumn("ID", width="small"),
                "Data": st.column_config.TextColumn("Data", width="medium"), # Usa a data original da planilha
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Valor_Exibir": st.column_config.TextColumn("Valor", width="medium"),
            },
            use_container_width=True, 
            hide_index=True
        )

elif aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    st.info("Ajustando as datas primeiro. O saldo consolidado voltará em breve.")
