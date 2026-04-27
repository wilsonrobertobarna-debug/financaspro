import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df.columns = [c.strip() for c in df.columns]
            return df_b, df_c, df
        return df_b, df_c, pd.DataFrame()
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

# 4. PROCESSAMENTO
if not df_base.empty:
    for col in ['Data', 'Valor', 'Descrição', 'Categoria', 'Tipo', 'Banco', 'Status']:
        if col not in df_base.columns: df_base[col] = ""
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR - FORMULÁRIO COM ORDEM DE COLUNAS CORRIGIDA
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt"])

with st.sidebar.form("f_novo"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_des = st.text_input("Descrição (Ex: Ração Milo)")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Alimentação", "Saúde", "Outros"]
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_p = f"{f_des} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_des
            # A ORDEM ABAIXO PRECISA SER IDÊNTICA ÀS COLUNAS DA PLANILHA (A até G)
            ws.append_row([
                dt_p.strftime("%d/%m/%Y"), # Coluna A
                str(f_val).replace('.', ','), # Coluna B
                desc_p,                      # Coluna C
                f_cat,                       # Coluna D
                f_tip,                       # Coluna E
                f_bnc,                       # Coluna F
                f_sta                        # Coluna G
            ])
        st.cache_data.clear()
        st.rerun()

# 6. EXIBIÇÃO POR ABA
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        # Filtros e Métricas omitidos para brevidade, mas mantidos no seu código real
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_base.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1].head(15), use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        # Filtro inteligente para capturar gastos com os cães
        pets = 'Milo|Bolt|Pet|Ração|Vacina|Vet'
        df_pets = df_base[df_base['Categoria'].str.contains(pets, case=False, na=False) | 
                          df_base['Descrição'].str.contains(pets, case=False, na=False)]
        st.info(f"Investimento Total nos Pets: **R$ {df_pets['V_Num'].sum():,.2f}**")
        st.dataframe(df_pets.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. GERENCIADOR (EXCLUIR / QUITAR)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar")
if not df_base.empty:
    df_manag = df_base.copy()
    df_manag['Linha'] = df_manag.index + 2
    opcoes = {f"Linha {r['Linha']} | {r['Descrição']}": r['Linha'] for _, r in df_manag.iloc[::-1].head(10).iterrows()}
    sel = st.sidebar.selectbox("Ação rápida:", [""] + list(opcoes.keys()))
    
    if sel:
        linha = opcoes[sel]
        c1, c2 = st.sidebar.columns(2)
        if c1.button("🗑️ APAGAR"):
            sh.get_worksheet(0).delete_rows(int(linha))
            st.cache_data.clear()
            st.rerun()
        if c2.button("✅ PAGO"):
            sh.get_worksheet(0).update_cell(int(linha), 7, "Pago") # Coluna 7 = Status
            st.cache_data.clear()
            st.rerun()
