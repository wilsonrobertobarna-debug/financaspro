import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 8px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px; line-height: 1.1;
    }
    .saldo-container h2 { margin: 0; font-size: 1.8rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .economia-texto { color: #007bff; font-size: 1.1rem; font-weight: bold; text-align: center; margin-bottom: 25px; }
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

# 3. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🛡️ FinançasPro Wilson</h1><p style='text-align: center; font-size: 1.5rem; margin-top: -10px;'>🐾<br>🐾</p>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        mes_atual = datetime.now().strftime('%m/%y')
        
        c_tipo = 'Tipo' if 'Tipo' in df.columns else df.columns[3]
        c_cat = 'Categoria' if 'Categoria' in df.columns else df.columns[2]
        c_stat = 'Status' if 'Status' in df.columns else df.columns[5]
        c_bnc = 'Banco' if 'Banco' in df.columns else df.columns[4]

        # Cálculos Dashboard
        rec = df[df[c_tipo].str.contains('Receita', case=False, na=False)]['Valor_Num'].sum()
        desp = df[df[c_tipo].str.contains('Despesa', case=False, na=False)]['Valor_Num'].sum()
        rend = df[df[c_cat].str.contains('Rendimento', case=False, na=False)]['Valor_Num'].sum()
        pend = df[df[c_stat].str.contains('Pendente', case=False, na=False)]['Valor_Num'].sum()
        saldo = rec - desp
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        st.markdown(f'<div class="saldo-container"><small>Saldo Atual</small><h2>{f_brl(saldo)}</h2></div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns(4); t1.metric("🟢 Receitas", f_brl(rec)); t2.metric("🔴 Despesas", f_brl(desp)); t3.metric("📈 Rendimentos", f_brl(rend)); t4.metric("⏳ Pendências", f_brl(pend))

        st.subheader("📋 Histórico")
        df_visual = df.copy(); df_visual.index = df_visual.index + 2
        st.dataframe(df_visual.iloc[::-1], use_container_width=True)

        # Gráficos
        st.write("---")
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("🍕 Categoria (Mês)")
            df_m = df.copy(); df_m['Mes'] = df_m['Data_DT'].dt.strftime('%m/%y')
            st.bar_chart(df_m[(df_m['Mes'] == mes_atual) & (df_m[c_tipo] == 'Despesa')].groupby(c_cat)['Valor_Num'].sum(), color='#ffc107')
        with g2:
            st.subheader("📊 Receita x Despesa")
            comp = df_m.groupby(['Mes', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
            st.bar_chart(comp, color=['#dc3545', '#28a745'])

        st.write("---")
        st.subheader("🏦 Gasto por Banco")
        st.bar_chart(df[df[c_tipo].str.contains('Despesa', case=False, na=False)].groupby(c_bnc)['Valor_Num'].sum(), color='#007bff')

    # MENU LATERAL FINANÇAS
    acao = st.sidebar.selectbox("Gerenciar Finanças:", ["Novo Lançamento", "Editar/Excluir"])
    if acao == "Novo Lançamento":
        with st.sidebar.form("f_fin"):
            f_dat = st.date_input("Data", datetime.now()); f_val = st.number_input("Valor", min_value=0.0)
            f_tip = st.selectbox("Tipo", ["Despesa", "Receita"]); f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
            f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"]); f_stat = st.selectbox("Status", ["Pago", "Pendente"])
            if st.form_submit_button("🚀 SALVAR"):
                ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
                st.cache_data.clear(); st.rerun()
    else:
        sel = st.sidebar.selectbox("ID Linha:", list(df_visual.index))
        if sel:
            row = df.loc[sel-2]
            with st.sidebar.form("e_fin"):
                e_dat = st.text_input("Data", value=str(row['Data'])); e_val = st.text_input("Valor", value=str(row['Valor']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 ATUALIZAR"):
                    ws.update(f"A{sel}:F{sel}", [[e_dat, e_val, row[c_cat], row[c_tipo], row[c_bnc], row[c_stat]]])
                    st.cache_data.clear(); st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    ws.delete_rows(int(sel)); st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    dados_p = ws_p.get_all_values()
    df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0])
    df_p.index = df_p.index + 2

    st.sidebar.subheader("Ação Pets")
    acao_p = st.sidebar.selectbox("Escolha:", ["Novo Registro", "Editar/Excluir"])

    if acao_p == "Novo Registro":
        with st.sidebar.form("f_p"):
            p_dat = st.date_input("Data", datetime.now()); p_obs = st.text_input("Obs"); p_val = st.number_input("Custo", min_value=0.0)
            if st.form_submit_button("🚀 SALVAR"):
                ws_p.append_row([p_dat.strftime("%d/%m/%Y"), p_obs, str(p_val).replace('.', ',')])
                st.cache_data.clear(); st.rerun()
    else:
        sel_p = st.sidebar.selectbox("ID Linha:", list(df_p.index))
        if sel_p:
            row_p = df_p.loc[sel_p]
            with st.sidebar.form("e_p"):
                e_obs = st.text_input("Obs", value=str(row_p['O que aconteceu?']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 ATUALIZAR"):
                    ws_p.update(f"B{sel_p}", [[e_obs]]); st.cache_data.clear(); st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    ws_p.delete_rows(int(sel_p)); st.cache_data.clear(); st.rerun()
    st.dataframe(df_p.iloc[::-1], use_container_width=True)

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Controle: Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    dados_v = ws_v.get_all_values()
    df_v = pd.DataFrame(dados_v[1:], columns=dados_v[0])
    df_v.index = df_v.index + 2

    st.sidebar.subheader("Ação Veículo")
    acao_v = st.sidebar.selectbox("Escolha:", ["Novo Registro", "Editar/Excluir"])

    if acao_v == "Novo Registro":
        with st.sidebar.form("f_v"):
            v_dat = st.date_input("Data", datetime.now()); v_km = st.number_input("KM", min_value=0); v_obs = st.text_input("Obs")
            if st.form_submit_button("🚀 SALVAR"):
                ws_v.append_row([v_dat.strftime("%d/%m/%Y"), str(v_km), v_obs, "0"])
                st.cache_data.clear(); st.rerun()
    else:
        sel_v = st.sidebar.selectbox("ID Linha:", list(df_v.index))
        if sel_v:
            row_v = df_v.loc[sel_v]
            with st.sidebar.form("e_v"):
                e_obs_v = st.text_input("Obs", value=str(row_v['Obs']))
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 ATUALIZAR"):
                    ws_v.update(f"C{sel_v}", [[e_obs_v]]); st.cache_data.clear(); st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    ws_v.delete_rows(int(sel_v)); st.cache_data.clear(); st.rerun()
    st.dataframe(df_v.iloc[::-1], use_container_width=True)
