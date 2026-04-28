import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
            "private_key": pk, "project_id": creds_dict["project_id"],
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E TRATAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    # Valor real para cálculo de saldo (Despesa vira negativo)
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO E LANÇAMENTOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📊 Extrato Diário"])

# [O código dos formulários de Novo Lançamento e Transferência permanece igual ao anterior]
# (Omitido aqui para brevidade, mas deve ser mantido no seu arquivo)

# 5. NOVA TELA: EXTRATO DIÁRIO (O SEU PEDIDO)
if aba == "📊 Extrato Diário":
    st.title("📊 Extrato Detalhado com Saldo Diário")
    
    c1, c2, c3 = st.columns(3)
    b_sel = c1.selectbox("Escolha o Banco:", sorted(df_base['Banco'].unique()))
    d_ini = c2.date_input("Início", datetime.now() - relativedelta(months=1))
    d_fim = c3.date_input("Fim", datetime.now())
    
    # Filtro de Beneficiário
    busca_ben = st.text_input("Filtrar por Beneficiário/Descrição (Opcional):")

    # Lógica de cálculo de saldo acumulado
    df_banco = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_banco['Saldo_Acumulado'] = df_banco['V_Real'].cumsum()
    
    # Filtrar pelo período e beneficiário para exibição
    mask = (df_banco['DT'].dt.date >= d_ini) & (df_banco['DT'].dt.date <= d_fim)
    if busca_ben:
        mask &= df_banco['Descrição'].str.contains(busca_ben, case=False, na=False)
    
    df_relat = df_banco.loc[mask].copy()

    if not df_relat.empty:
        # Identificar o último lançamento de cada dia para mostrar o saldo
        df_relat['Saldo Diário'] = ""
        last_indices = df_relat.groupby('DT').tail(1).index
        df_relat.loc[last_indices, 'Saldo Diário'] = df_relat.loc[last_indices, 'Saldo_Acumulado'].apply(m_fmt)
        
        # Formatação para exibição
        df_show = df_relat[['Data', 'Descrição', 'Tipo', 'Valor', 'Saldo Diário']].iloc[::-1]
        st.table(df_show) # Usando table para um visual mais impresso
        
        if st.button("🖨️ Preparar para Impressão / PDF"):
            st.info("Use Ctrl+P no seu navegador para salvar este extrato como PDF.")
    else:
        st.warning("Nenhum lançamento encontrado para este banco no período selecionado.")

# 6. TELA DE RELATÓRIOS (WHATSAPP)
elif aba == "📄 Relatórios":
    st.title("📄 Relatório para WhatsApp")
    # [Mantém a lógica do relatório resumido que fizemos anteriormente]

# [As outras abas: Finanças, Milo e Veículo permanecem iguais]
