import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DO SISTEMA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
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

# 3. CARREGAMENTO E LIMPEZA
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

# 5. SIDEBAR (FORMULÁRIO)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_p = f"{f_des} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_des
            # ORDEM A-G: Data, Valor, Descrição, Categoria, Tipo, Banco, Status
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_p, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 6. CONTEÚDO PRINCIPAL
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Filtro por Banco
        bancos_list = ["Todos"] + sorted(df_base['Banco'].unique().tolist())
        banco_sel = st.selectbox("🔍 Pesquisar por Banco:", bancos_list)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base['Banco'] == banco_sel]

        # Saldo Real
        df_pago = df_filtrado[df_filtrado['Status'].str.strip() == 'Pago']
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_valor).sum()
        entradas = df_pago[df_pago['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        saidas = df_pago[df_pago['Tipo'] == 'Despesa']['V_Num'].sum()
        
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual ({banco_sel})</small><h2>R$ {s_ini + entradas - saidas:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # Gráficos
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("📈 Evolução Mensal")
            df_evol = df_filtrado.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().unstack().fillna(0).reset_index()
            fig = go.Figure()
            for t, cor in zip(['Receita', 'Despesa', 'Rendimento'], ['#28a745', '#dc3545', '#007bff']):
                if t in df_evol.columns: fig.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol[t], name=t, marker_color=cor))
            fig.update_layout(barmode='group', height=300, margin=dict(l=0,r=0,t=30,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            st.subheader("📊 Metas por Categoria")
            df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
            real_cat = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum()
            if 'Meta' in df_cats_cad.columns:
                df_cats_cad['Meta_Num'] = df_cats_cad['Meta'].astype(str).apply(limpar_valor)
                df_meta_plot = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta_Num'], 'Real': real_cat}).fillna(0).query("Meta > 0 or Real > 0")
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(y=df_meta_plot.index, x=df_meta_plot['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig_m.add_trace(go.Bar(y=df_meta_plot.index, x=df_meta_plot['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig_m.update_layout(barmode='group', height=300, margin=dict(l=0,r=0,t=30,b=0))
                st.plotly_chart(fig_m, use_container_width=True)

        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_filtrado.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1].head(20), use_container_width=True)

# 7. GERENCIADOR (BARRA LATERAL)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gestão de Linhas")
if not df_base.empty:
    df_base['Linha'] = df_base.index + 2
    opcoes = {f"Linha {r['Linha']} | {r['Descrição']}": r['Linha'] for _, r in df_base.iloc[::-1].head(10).iterrows()}
    sel = st.sidebar.selectbox("Selecionar para ação:", [""] + list(opcoes.keys()))
    if sel:
        l_alvo = opcoes[sel]
        col_b1, col_b2 = st.sidebar.columns(2)
        if col_b1.button("🗑️ APAGAR"):
            sh.get_worksheet(0).delete_rows(int(l_alvo))
            st.cache_data.clear(); st.rerun()
        if col_b2.button("✅ PAGO"):
            sh.get_worksheet(0).update_cell(int(l_alvo), 7, "Pago") # Coluna 7 é a 'G'
            st.cache_data.clear(); st.rerun()
