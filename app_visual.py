import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .resumo-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-top: 10px; }
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

# 3. CARREGAMENTO
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        # Carrega categorias para as Metas
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
            
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
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
    for col in ['Data', 'Valor', 'Categoria', 'Tipo', 'Banco', 'Status']:
        if col not in df_base.columns: df_base[col] = ""
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    if aba == "🐾 Milo & Bolt":
        lista_cats = ["Pet: Milo - Ração", "Pet: Milo - Vet", "Pet: Bolt - Ração", "Pet: Bolt - Vet", "Gasto Geral Pet"]
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f"{f_cat} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 6. CONTEÚDO
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        df_real = df_base[df_base['Status'].str.strip() != 'Pendente']
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0
        t_in = df_real[df_real['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        t_out = df_real[df_real['Tipo'] == 'Despesa']['V_Num'].sum()
        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {s_ini + t_in - t_out:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        df_mes = df_base[df_base['Mes_Ano'] == mes_atual]
        m_rec = df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()
        m_des = df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()
        m_ren = df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum()
        m_pen = df_mes[df_mes['Status'].str.strip() == 'Pendente']['V_Num'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {m_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- RESUMO ECONOMIA ---
        st.write("---")
        c_ec1, c_ec2 = st.columns([1, 2])
        with c_ec1:
            total_entrada = m_rec + m_ren
            sobra = total_entrada - m_des
            perc = (sobra / total_entrada * 100) if total_entrada > 0 else 0
            st.markdown(f'<div class="resumo-box"><h4>💰 Economia do Mês</h4><p>Sobrou: <b>R$ {sobra:,.2f}</b></p><p style="color:#28a745;"><b>{perc:.1f}%</b> do total que entrou.</p></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)
        with c_ec2:
            df_res_cat = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index().sort_values(by='V_Num', ascending=False)
            if not df_res_cat.empty:
                df_res_cat.columns = ['Categoria', 'Valor']
                df_res_cat['%'] = (df_res_cat['Valor'] / m_des * 100).apply(lambda x: f"{x:.1f}%")
                df_res_cat['Valor'] = df_res_cat['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                st.dataframe(df_res_cat, use_container_width=True, hide_index=True)

        # --- GRÁFICOS ---
        st.write("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("📈 Evolução Mensal")
            df_evol = df_base.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().unstack().fillna(0).reset_index()
            fig = go.Figure()
            for t, c in zip(['Receita', 'Despesa', 'Rendimento'], ['#28a745', '#dc3545', '#007bff']):
                if t in df_evol.columns: fig.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol[t], name=t, marker_color=c))
            fig.update_layout(barmode='group', height=300, margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig, use_container_width=True)

        with col_g2:
            st.subheader("📊 Metas vs Gasto Real")
            gasto_cat = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum()
            df_metas = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': gasto_cat}).fillna(0.0)
            df_metas = df_metas[(df_metas['Meta'] > 0) | (df_metas['Real'] > 0)]
            if not df_metas.empty:
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(y=df_metas.index, x=df_metas['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig_m.add_trace(go.Bar(y=df_metas.index, x=df_metas['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig_m.update_layout(barmode='group', height=300, margin=dict(l=10,r=10,t=10,b=10))
                st.plotly_chart(fig_m, use_container_width=True)

        st.write("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_base.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1].head(15), use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        df_pets = df_base[df_base['Categoria'].str.contains('Milo|Bolt|Pet|Ração', case=False, na=False)]
        st.info(f"Investimento Total nos Pets: **R$ {df_pets['V_Num'].sum():,.2f}**".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_pets.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# GERENCIADOR
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar")
if not df_base.empty:
    lista_edit = df_base.iloc[::-1].head(10)
    opcoes = [f"{idx+2} | {row['Data']} | {row['Categoria']} | {row['Valor']}" for idx, row in lista_edit.iterrows()]
    sel = st.sidebar.selectbox("Editar/Excluir:", [""] + opcoes)
    if sel:
        linha = int(sel.split(" | ")[0])
        if st.sidebar.button("🗑️ Excluir"):
            sh.get_worksheet(0).delete_rows(linha)
            st.cache_data.clear(); st.rerun()
        if st.sidebar.button("✅ Quitar"):
            sh.get_worksheet(0).update_cell(linha, 6, "Pago")
            st.cache_data.clear(); st.rerun()
