import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); border: 1px solid #eee; }
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

# 3. CARREGAMENTO E LIMPEZA (Soma exata)
@st.cache_data(ttl=2)
def carregar_dados():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        # Limpeza para evitar duplicação de dados fantasmas
        df = df.dropna(how='all')
        return df_b, df_c, df
    except: return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    if not v: return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (LANÇAMENTOS)
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
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        desc_final = f"{f_des} [{f_ben}]"
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_final, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. CONTEÚDO PRINCIPAL (ORDEM QUE VOCÊ PEDIU)
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # --- 1º TAGS (TOP) ---
        df_mes = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        t1, t2, t3, t4 = st.columns(4)
        with t1:
            val = df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()
            st.metric("📈 Receitas", f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        with t2:
            val = df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()
            st.metric("📉 Despesas", f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        with t3:
            val = df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum()
            st.metric("💰 Rendimentos", f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        with t4:
            val = df_mes[df_mes['Status'].str.strip() == 'Pendente']['V_Num'].sum()
            st.metric("⏳ Pendência", f"R$ {val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.write("---")

        # --- 2º GRÁFICOS (MEIO) ---
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📊 Gastos por Categoria")
            df_g = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_g.empty:
                st.plotly_chart(px.pie(df_g, values='V_Num', names='Categoria', hole=0.4, height=350), use_container_width=True)
            else: st.info("Sem gastos este mês.")

        with col_g2:
            st.subheader("⚖️ Receitas vs Despesas")
            df_f = df_mes.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty:
                st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', height=350, color_discrete_map={'Receita':'#28a745','Despesa':'#dc3545','Rendimento':'#007bff'}), use_container_width=True)

        st.write("---")

        # --- 3º LANÇAMENTOS (BASE) ---
        st.subheader("📋 Lançamentos e Pesquisa")
        # Filtro por banco
        bancos = ["Todos"] + sorted(df_base['Banco'].unique().tolist())
        sel_banco = st.selectbox("Pesquisar por Banco:", bancos)
        
        df_mostrar = df_base.copy()
        if sel_banco != "Todos":
            df_mostrar = df_mostrar[df_mostrar['Banco'] == sel_banco]
            
        st.dataframe(df_mostrar.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

# 8. GERENCIADOR
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar Registro")
if not df_base.empty:
    df_aux = df_base.copy()
    df_aux['ID'] = df_aux.index + 2
    opcoes = {f"L{r['ID']} | {r['Descrição']} | R$ {r['Valor']}": r['ID'] for _, r in df_aux.tail(15).iloc[::-1].iterrows()}
    sel = st.sidebar.selectbox("Ação na linha:", [""] + list(opcoes.keys()))
    if sel:
        linha = opcoes[sel]
        c1, c2 = st.sidebar.columns(2)
        if c1.button("🚨 Apagar"):
            sh.get_worksheet(0).delete_rows(int(linha))
            st.cache_data.clear(); st.rerun()
        if c2.button("✅ Quitar"):
            sh.get_worksheet(0).update_cell(int(linha), 7, "Pago")
            st.cache_data.clear(); st.rerun()
