import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF

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
    # Mantém o ID original da linha para ordenação correta
    df['ID_Linha'] = range(2, len(df) + 2)
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    # Garante que a data seja lida corretamente no formato brasileiro 
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Status_Normalizado'] = df['Status'].str.strip().str.upper()
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento', 'Entrada'] else -r['V_Num'], axis=1)
    
    # Ordena por Data e depois por ID para garantir a sequência real
    return df.sort_values(['DT', 'ID_Linha'])

def m_fmt(n): 
    if n == "" or pd.isna(n) or n == 0: return ""
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 3. INTERFACE
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

if aba == "📊 Extrato Diário":
    st.title("📊 Extrato Diário Detalhado")
    
    c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1])
    d_ini = c1.date_input("Início", datetime.now().replace(day=1))
    d_fim = c2.date_input("Fim", datetime.now())
    b_sel = c3.selectbox("Banco:", sorted(df_base['Banco'].unique())) if not df_base.empty else st.selectbox("Banco:", ["Sem dados"])
    s_filter = c4.selectbox("Filtro Status:", ["Todos", "Pago", "Pendente"])
    
    df_b = df_base[df_base['Banco'] == b_sel].copy() if not df_base.empty else pd.DataFrame()
    
    if not df_b.empty:
        # Cálculo do Saldo (apenas confirmados)
        df_b['Saldo_Acum'] = df_b[df_b['Status_Normalizado'] == 'PAGO']['V_Real'].cumsum()
        df_b['Saldo_Acum'] = df_b['Saldo_Acum'].ffill().fillna(0)
        
        # Filtros de exibição
        df_f = df_b[(df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_fim)].copy()
        if s_filter == "Pago": df_f = df_f[df_f['Status_Normalizado'] == 'PAGO']
        elif s_filter == "Pendente": df_f = df_f[df_f['Status_Normalizado'] != 'PAGO']
        
        # Identifica a última linha do dia no conjunto filtrado para mostrar o saldo
        df_f['Ultima_Linha_Dia'] = False
        if not df_f.empty:
            idx_ultimas = df_f.groupby('Data')['ID_Linha'].idxmax()
            df_f.loc[idx_ultimas, 'Ultima_Linha_Dia'] = True
            
        df_f['Valor_Exibir'] = df_f.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['V_Real'] < 0 else m_fmt(r['V_Num']), axis=1)
        df_f['Saldo_Exibir'] = df_f.apply(lambda r: m_fmt(r['Saldo_Acum']) if r['Ultima_Linha_Dia'] else "", axis=1)

        # Exibição (Data normalizada e Saldo visível)
        st.dataframe(
            df_f.iloc[::-1], # Mostra do mais recente para o mais antigo
            column_order=("ID_Linha", "Data", "Descrição", "Tipo", "Status", "Valor_Exibir", "Saldo_Exibir"),
            column_config={
                "ID_Linha": st.column_config.TextColumn("ID"),
                "Data": st.column_config.TextColumn("Data"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Valor_Exibir": "Valor",
                "Saldo_Exibir": "Saldo do Dia"
            },
            use_container_width=True, hide_index=True
        )
