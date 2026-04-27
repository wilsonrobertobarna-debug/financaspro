import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.08); border: 1px solid #eee; }
    [data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO (LIMPEZA PEM)
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        pk = creds_info["private_key"].replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": pk,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO (SOMA BLINDADA)
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        df = df[df['Data'] != ""].copy() 
        return df_b, df_c, df
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_ben = st.text_input("Beneficiário")
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    if aba == "🐾 Milo & Bolt":
        lista_cats = ["Pet: Milo", "Pet: Bolt", "Geral Pet"]
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        desc_final = f"{f_des} [{f_ben}]"
        ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_final, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. ABA FINANÇAS
if aba == "💰 Finanças":
    st.markdown("<h2 style='text-align: center;'>🛡️ FinançasPro Wilson</h2>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_mes = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        # --- TAGS NO TOPO ---
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("📈 Receitas", f"R$ {df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ','))
        t2.metric("📉 Despesas", f"R$ {df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ','))
        t3.metric("💰 Rendimentos", f"R$ {df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ','))
        t4.metric("⏳ Pendência", f"R$ {df_mes[df_mes['Status'].str.strip() == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ','))

        st.write("---")

        # --- GRÁFICOS NO MEIO ---
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            df_g = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_g.empty:
                st.plotly_chart(px.pie(df_g, values='V_Num', names='Categoria', hole=0.4, title="Gastos por Categoria"), use_container_width=True)
        with col_g2:
            df_f = df_mes.groupby('Tipo')['V_Num'].sum().reset_index()
            st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo de Caixa"), use_container_width=True)

        st.write("---")

        # --- PESQUISA E TABELA NO FINAL ---
        st.subheader("📋 Pesquisa de Lançamentos")
        c1, c2, c3 = st.columns(3)
        p_banco = c1.multiselect("Filtrar por Banco:", sorted(df_base['Banco'].unique()))
        p_status = c2.multiselect("Filtrar por Status:", ["Pago", "Pendente"])
        p_tipo = c3.multiselect("Filtrar por Tipo:", ["Despesa", "Receita", "Rendimento"])

        df_f = df_base.copy()
        if p_banco: df_f = df_f[df_f['Banco'].isin(p_banco)]
        if p_status: df_f = df_f[df_f['Status'].isin(p_status)]
        if p_tipo: df_f = df_f[df_f['Tipo'].isin(p_tipo)]
        
        st.dataframe(df_f.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

# 6. ABA MILO & BOLT (MENINOS)
elif aba == "🐾 Milo & Bolt":
    st.markdown("<h2 style='text-align: center;'>🐾 Lançamentos dos Meninos</h2>", unsafe_allow_html=True)
    df_milos = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Total Investido neles", f"R$ {df_milos['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ','))
    st.dataframe(df_milos.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. ABA MEU VEÍCULO
elif aba == "🚗 Meu Veículo":
    st.markdown("<h2 style='text-align: center;'>🚗 Gastos com Veículo</h2>", unsafe_allow_html=True)
    df_carro = df_base[df_base['Categoria'].str.contains('Veículo|Carro', case=False, na=False)]
    st.dataframe(df_carro.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

# 8. GERENCIADOR (EXCLUIR)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar Registro")
if not df_base.empty:
    df_aux = df_base.copy()
    df_aux['ID'] = df_aux.index + 2
    opcoes = {f"L{r['ID']} | {r['Descrição']} | R$ {r['Valor']}": r['ID'] for _, r in df_aux.tail(15).iloc[::-1].iterrows()}
    sel = st.sidebar.selectbox("Ação na linha:", [""] + list(opcoes.keys()))
    if sel and st.sidebar.button("🚨 APAGAR"):
        sh.get_worksheet(0).delete_rows(int(opcoes[sel]))
        st.cache_data.clear(); st.rerun()
