import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 10px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
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

# 3. FUNÇÃO DE CARREGAMENTO
@st.cache_data(ttl=60)
def carregar_aba(nome_aba):
    try:
        ws = sh.worksheet(nome_aba)
        dados = ws.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

# 4. CARREGAMENTO INICIAL DE DADOS
df_bancos_cad = carregar_aba("Bancos")
df_cats_cad = carregar_aba("Categoria")
# Ajuste de Metas
if not df_cats_cad.empty and 'Meta' in df_cats_cad.columns:
    df_cats_cad['Meta'] = df_cats_cad['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
    df_cats_cad['Meta'] = pd.to_numeric(df_cats_cad['Meta'], errors='coerce').fillna(0.0)

# 5. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 💰 FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws_fin = sh.get_worksheet(0)
    dados_fin = ws_fin.get_all_values()
    df_base = pd.DataFrame(dados_fin[1:], columns=dados_fin[0]) if len(dados_fin) > 1 else pd.DataFrame()
    
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        def limpar(v):
            v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return pd.to_numeric(v, errors='coerce') or 0.0

        df_base['V_Num'] = df_base[c_val].apply(limpar)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        banco_sel = st.selectbox("🔍 Pesquisar por Banco:", ["Todos"] + sorted(df_base[c_bnc].unique().tolist()))
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculos (Regra: Pendente não entra no Saldo Geral)
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar).sum() if not df_bancos_cad.empty else 0
        df_realizado = df_base[df_base[c_sta] != 'Pendente']
        t_rec = df_realizado[(df_realizado[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
        t_des = df_realizado[df_realizado[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_geral = s_ini + t_rec - t_des

        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        m_rec = df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum()
        m_des = df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum()
        m_ren = df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum()
        m_pen = df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum()

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {m_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.write("---")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.subheader("🏦 Saldo por Banco")
            s_bancos = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar).sum()
                re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                s_bancos.append({'Banco': b, 'Saldo': si + re - de})
            df_sb = pd.DataFrame(s_bancos)
            df_sb = df_sb[df_sb['Saldo'] != 0]
            if not df_sb.empty:
                fig_p = px.pie(df_sb, values='Saldo', names='Banco', hole=.4, height=300)
                st.plotly_chart(fig_p, use_container_width=True)

        with col_g2:
            st.subheader(f"📊 Metas ({mes_atual})")
            g_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
            df_m = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': g_cat}).fillna(0.0)
            df_m = df_m[(df_m['Meta'] > 0) | (df_m['Real'] > 0)]
            if not df_m.empty:
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(y=df_m.index, x=df_m['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig_m.add_trace(go.Bar(y=df_m.index, x=df_m['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig_m.update_layout(barmode='group', height=300, margin=dict(l=0, r=0, t=20, b=0), legend=dict(orientation="h", y=1.2))
                st.plotly_chart(fig_m, use_container_width=True)

        st.subheader("📋 Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

    # FORMULÁRIOS LATERAIS
    with st.sidebar.form("f_novo"):
        st.write("### 🚀 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        f_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            for i in range(f_parc):
                dt_p = f_dat + relativedelta(months=i)
                desc = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                ws_fin.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

    st.sidebar.write("---")
    st.sidebar.write("### ⚙️ Gerenciar")
    if not df_base.empty:
        lista_edit = df_base.iloc[::-1].head(15)
        opcoes = [f"{idx+2} | {row[c_dat]} | {row[c_cat]} | {row[c_val]}" for idx, row in lista_edit.iterrows()]
        item_sel = st.sidebar.selectbox("Selecionar:", [""] + opcoes)
        if item_sel:
            l_idx = int(item_sel.split(" | ")[0])
            if st.sidebar.button("✅ Quitar"):
                ws_fin.update_cell(l_idx, 6, "Pago")
                st.cache_data.clear(); st.rerun()
            conf = st.sidebar.checkbox("Confirmar exclusão?")
            if conf and st.sidebar.button("🗑️ EXCLUIR"):
                ws_fin.delete_rows(l_idx)
                st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 🐾 MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Controle: Milo & Bolt</h1>", unsafe_allow_html=True)
    df_p = carregar_aba("Controle_Pets")
    if not df_p.empty:
        st.dataframe(df_p.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_pet"):
        st.write("### 🐾 Novo Gasto/Cuidado")
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_pet = st.selectbox("Pet", ["Milo", "Bolt", "Ambos"])
        p_tipo = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Veterinário", "Remédio", "Outros"])
        p_val = st.number_input("Valor (R$)", min_value=0.0)
        p_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        p_obs = st.text_input("Obs")
        p_parc = st.number_input("Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            ws_p = sh.worksheet("Controle_Pets")
            for i in range(p_parc):
                dt_p = p_dat + relativedelta(months=i)
                obs_f = f"{p_obs} ({i+1}/{p_parc})" if p_parc > 1 else p_obs
                ws_p.append_row([dt_p.strftime("%d/%m/%Y"), p_pet, p_tipo, str(p_val).replace('.', ','), p_bnc, obs_f])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 🚗 MEU VEÍCULO
# ==========================================
else:
    st.markdown("<h1 style='text-align: center;'>🚗 Controle Veículo</h1>", unsafe_allow_html=True)
    df_v = carregar_aba("Controle_Veiculo")
    if not df_v.empty:
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_veic"):
        st.write("### 🚗 Registro Veículo")
        v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        v_tipo = st.selectbox("Tipo", ["Combustível", "Troca de Óleo", "Pneus", "Revisão", "Seguro", "Outros"])
        v_km = st.text_input("KM Atual")
        v_val = st.number_input("Valor", min_value=0.0)
        v_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        v_parc = st.number_input("Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            ws_v = sh.worksheet("Controle_Veiculo")
            for i in range(v_parc):
                dt_p = v_dat + relativedelta(months=i)
                tipo_f = f"{v_tipo} ({i+1}/{v_parc})" if v_parc > 1 else v_tipo
                ws_v.append_row([dt_p.strftime("%d/%m/%Y"), tipo_f, v_km, str(v_val).replace('.', ','), v_bnc])
            st.cache_data.clear(); st.rerun()
