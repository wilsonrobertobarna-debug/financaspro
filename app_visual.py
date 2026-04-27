import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# Estilos Visuais
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 10px; border: 1px solid #0056b3; }
    .saldo-container h2 { margin: 0; font-size: 2.5rem; font-weight: bold; }
    .tag-container { display: flex; justify-content: space-around; margin-bottom: 25px; gap: 10px; }
    .tag-card { flex: 1; padding: 12px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .tag-receita { background-color: #28a745; }
    .tag-despesa { background-color: #dc3545; }
    .tag-rendimento { background-color: #17a2b8; }
    .tag-pendente { background-color: #ffc107; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO ROBUSTA (Tratamento de Chave)
@st.cache_resource
def conectar_google():
    try:
        # Pega as infos do Secrets
        creds_dict = st.secrets["connections"]["gsheets"]
        
        # O SEGREDO ESTÁ AQUI: Limpa a chave privada de espaços ou quebras de linha erradas
        private_key = creds_dict["private_key"].replace("\\n", "\n").strip()
        
        info = {
            "type": creds_dict["type"],
            "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict["private_key_id"],
            "private_key": private_key,
            "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(info, scopes=scopes)
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro na Chave de Acesso: {e}")
        st.stop()

client = conectar_google()
# Substitua pela sua ID se for diferente
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO E LIMPEZA
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        ws_l = sh.get_worksheet(0) # Aba LANCAMENTOS
        ws_b = sh.worksheet("Bancos")
        ws_c = sh.worksheet("Categoria")
        
        df = pd.DataFrame(ws_l.get_all_records())
        df_b = pd.DataFrame(ws_b.get_all_records())
        df_c = pd.DataFrame(ws_c.get_all_records())
        return df_b, df_c, df
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    if pd.isna(v) or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')

# 4. INTERFACE PRINCIPAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # OS TRÊS FILTROS DE VOLTA
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            lista_bancos = ["Todos"] + sorted(df_base['Banco'].unique().tolist())
            banco_sel = st.selectbox("🔍 Banco:", lista_bancos)
        with col_f2:
            tipo_sel = st.selectbox("📂 Tipo:", ["Todos", "Despesa", "Receita", "Rendimento"])
        with col_f3:
            status_sel = st.multiselect("📌 Status:", ["Pago", "Pendente"], default=["Pago", "Pendente"])

        # Filtragem
        df_f = df_base.copy()
        if banco_sel != "Todos": df_f = df_f[df_f['Banco'] == banco_sel]
        if tipo_sel != "Todos": df_f = df_f[df_f['Tipo'] == tipo_sel]
        df_f = df_f[df_f['Status'].isin(status_sel)]

        # Tags de Resumo (Baseado no Banco)
        receitas = df_f[(df_f['Tipo'] == 'Receita') & (df_f['Status'] == 'Pago')]['V_Num'].sum()
        despesas = df_f[(df_f['Tipo'] == 'Despesa') & (df_f['Status'] == 'Pago')]['V_Num'].sum()
        rendimentos = df_f[(df_f['Tipo'] == 'Rendimento') & (df_f['Status'] == 'Pago')]['V_Num'].sum()
        pendentes = df_f[df_f['Status'] == 'Pendente']['V_Num'].sum()

        st.markdown(f'''
            <div class="tag-container">
                <div class="tag-card tag-receita">Receitas<br>R$ {receitas:,.2f}</div>
                <div class="tag-card tag-despesa">Despesas<br>R$ {despesas:,.2f}</div>
                <div class="tag-card tag-rendimento">Rendimentos<br>R$ {rendimentos:,.2f}</div>
                <div class="tag-card tag-pendente">Pendências<br>R$ {pendentes:,.2f}</div>
            </div>
        '''.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        st.dataframe(df_f.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 5. GERENCIADOR DE EXCLUSÃO (LIMPO)
st.sidebar.write("---")
if not df_base.empty:
    st.sidebar.write("### 🗑️ Apagar Registro")
    df_base['Linha'] = df_base.index + 2
    opcoes = {f"L{r['Linha']} | {r['Descrição']}": r['Linha'] for _, r in df_base.iloc[::-1].head(10).iterrows()}
    item_del = st.sidebar.selectbox("Escolha para apagar:", [""] + list(opcoes.keys()))
    
    if item_del:
        if st.sidebar.button("CONFIRMAR EXCLUSÃO"):
            sh.get_worksheet(0).delete_rows(int(opcoes[item_del]))
            st.cache_data.clear()
            st.rerun()
