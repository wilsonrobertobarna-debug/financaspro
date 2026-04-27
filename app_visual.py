import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; }
    .metric-card { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border-left: 5px solid #007bff; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
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
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

# 4. PROCESSAMENTO
if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR (LANÇAMENTOS)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_f = f"{f_des} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_des
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_f, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 6. ABA FINANÇAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    
    if not df_base.empty:
        # Filtros
        c1, c2 = st.columns(2)
        bancos = ["Todos"] + sorted(df_base['Banco'].unique().tolist())
        banco_sel = c1.selectbox("Filtrar Banco:", bancos)
        
        df_f = df_base if banco_sel == "Todos" else df_base[df_base['Banco'] == banco_sel]
        
        # Cálculos de Saldo
        receitas = df_f[(df_f['Tipo'].isin(['Receita', 'Rendimento'])) & (df_f['Status'] == 'Pago')]['V_Num'].sum()
        despesas = df_f[(df_f['Tipo'] == 'Despesa') & (df_f['Status'] == 'Pago')]['V_Num'].sum()
        
        if banco_sel == "Todos":
            s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0
        else:
            s_ini = df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0

        saldo_total = s_ini + receitas - despesas

        st.markdown(f'''<div class="saldo-container"><small>Saldo Real ({banco_sel})</small><h2>R$ {saldo_total:,.2f}</h2></div>'''.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("📈 Evolução")
            df_evol = df_f.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().unstack().fillna(0).reset_index()
            fig = go.Figure()
            for t, cor in zip(['Receita', 'Despesa'], ['#28a745', '#dc3545']):
                if t in df_evol.columns: fig.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol[t], name=t, marker_color=cor))
            st.plotly_chart(fig, use_container_width=True)
        
        with g2:
            st.subheader("📊 Gastos do Mês")
            df_m = df_f[df_f['Mes_Ano'] == mes_atual]
            gastos = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum()
            if not gastos.empty:
                st.plotly_chart(go.Figure(data=[go.Pie(labels=gastos.index, values=gastos.values, hole=.4)]), use_container_width=True)

        st.dataframe(df_f.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. ABA PETS
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Total Gasto", f"R$ {df_p['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.dataframe(df_p.iloc[::-1], use_container_width=True)

# 8. GERENCIADOR DE EXCLUSÃO (CORRIGIDO)
st.sidebar.write("---")
if not df_base.empty:
    st.sidebar.write("### 🗑️ Gerenciar Registros")
    df_excluir = df_base.copy()
    df_excluir['LinhaPlanilha'] = df_excluir.index + 2
    
    # Prepara a lista para o selectbox (Últimos 15 registros)
    opcoes_dict = {}
    for _, r in df_excluir.tail(15).iloc[::-1].iterrows():
        texto = f"L{r['LinhaPlanilha']} | {r['Data']} | {r['Descrição']} | R$ {r['Valor']}"
        opcoes_dict[texto] = r['LinhaPlanilha']
    
    selecionado = st.sidebar.selectbox("Escolha para apagar:", [""] + list(opcoes_dict.keys()))
    
    if selecionado:
        linha_alvo = opcoes_dict[selecionado]
        if st.sidebar.button("CONFIRMAR EXCLUSÃO"):
            sh.get_worksheet(0).delete_rows(int(linha_alvo))
            st.sidebar.success(f"Linha {linha_alvo} apagada!")
            st.cache_data.clear()
            st.rerun()
