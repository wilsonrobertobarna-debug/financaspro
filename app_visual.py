import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets!"); st.stop()
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
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO
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
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values(['DT', 'ID_Linha'])

def m_fmt(n): 
    if n == "" or pd.isna(n): return ""
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

df_base = carregar()

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

# 5. TELAS
if aba == "📊 Extrato Diário":
    st.title("📊 Extrato com Fechamento Diário")
    
    c1, c2, c3 = st.columns([1,1,2])
    d_ini = c1.date_input("Início", datetime.now().replace(day=1))
    d_fim = c2.date_input("Fim", datetime.now())
    txt_psq = c3.text_input("🔍 Buscar na Descrição:")
    
    b_sel = st.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    
    df_b = df_base[df_base['Banco'] == b_sel].copy()
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    
    # Identificar última linha do dia para o fechamento
    df_b['is_last_of_day'] = ~df_b.duplicated(subset=['Data'], keep='last')
    
    # Filtros
    df_f = df_b[(df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_fim)].copy()
    if txt_psq:
        df_f = df_f[df_f['Descrição'].str.contains(txt_psq, case=False, na=False)]
    
    # Formatação de colunas para exibição
    df_f['Valor_Exibir'] = df_f.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] == 'Despesa' else m_fmt(r['V_Num']), axis=1)
    df_f['Saldo_Exibir'] = df_f.apply(lambda r: m_fmt(r['Saldo_Acum']) if r['is_last_of_day'] else "", axis=1)

    # Função de Cores Corrigida
    def colorir_estilo(row):
        estilos = [''] * len(row)
        # Cor do Valor
        if '-' in str(row['Valor_Exibir']): estilos[row.index.get_loc('Valor_Exibir')] = 'color: red'
        else: estilos[row.index.get_loc('Valor_Exibir')] = 'color: green'
        
        # Cor do Saldo (Vermelho se o acumulado for negativo)
        if row['is_last_of_day']:
            if row['Saldo_Acum'] < 0:
                estilos[row.index.get_loc('Saldo_Exibir')] = 'color: red; font-weight: bold'
            else:
                estilos[row.index.get_loc('Saldo_Exibir')] = 'color: blue; font-weight: bold'
        return estilos

    st.divider()
    # Preparar DF de exibição
    df_res = df_f[['Data', 'Descrição', 'Valor_Exibir', 'Saldo_Exibir', 'Saldo_Acum', 'is_last_of_day']].iloc[::-1]
    
    # Renomear colunas para o usuário
    df_final = df_res.rename(columns={'Valor_Exibir': 'Valor', 'Saldo_Exibir': 'Saldo'})
    
    # Aplicar estilo e esconder colunas de suporte
    st.dataframe(
        df_final.style.apply(colorir_estilo, axis=1),
        column_order=("Data", "Descrição", "Valor", "Saldo"),
        use_container_width=True,
        hide_index=True
    )

elif aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    # ... (Restante do código de Finanças, Milo & Bolt e Relatórios mantidos)
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(df_base['V_Real'].sum())}")
