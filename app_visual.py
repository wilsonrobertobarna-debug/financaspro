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

# 3. CARREGAMENTO DE CADASTROS (ABAS NOVAS)
@st.cache_data(ttl=60)
def carregar_cadastros():
    # Bancos
    ws_b = sh.worksheet("Bancos")
    df_b = pd.DataFrame(ws_b.get_all_records())
    # Categorias
    ws_c = sh.worksheet("Categoria")
    df_c = pd.DataFrame(ws_c.get_all_records())
    # Cartões
    ws_ct = sh.worksheet("Cartoes")
    df_ct = pd.DataFrame(ws_ct.get_all_records())
    return df_b, df_c, df_ct

df_bancos_cad, df_cats_cad, df_cartoes_cad = carregar_cadastros()

# 4. NAVEGAÇÃO
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
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        c_tipo = 'Tipo' if 'Tipo' in df_base.columns else df_base.columns[3]
        c_cat = 'Categoria' if 'Categoria' in df_base.columns else df_base.columns[2]
        c_stat = 'Status' if 'Status' in df_base.columns else df_base.columns[5]
        c_bnc = 'Banco' if 'Banco' in df_base.columns else df_base.columns[4]

        # Filtro de Banco baseado no cadastro real
        lista_bancos_filtro = ["Todos"] + sorted(df_bancos_cad['Nome do Banco'].tolist())
        banco_filtro = st.selectbox("🔍 Filtrar Visão por Banco:", lista_bancos_filtro)
        
        df = df_base[df_base[c_bnc] == banco_filtro].copy() if banco_filtro != "Todos" else df_base.copy()

        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_Calc'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        mes_atual = datetime.now().strftime('%m/%y')
        
        # Lógica de Saldo Inicial
        if banco_filtro == "Todos":
            saldo_inicial = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()
        else:
            row_b = df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_filtro]
            saldo_inicial = pd.to_numeric(row_b['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum()

        rec = df[df[c_tipo].str.contains('Receita', case=False, na=False)]['Valor_Num'].sum()
        desp = df[df[c_tipo].str.contains('Despesa', case=False, na=False)]['Valor_Num'].sum()
        rend = df[df[c_cat].str.contains('Rendimento', case=False, na=False)]['Valor_Num'].sum()
        pend = df[df[c_stat].str.contains('Pendente', case=False, na=False)]['Valor_Num'].sum()
        
        saldo_total = saldo_inicial + rec - desp
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        st.markdown(f'<div class="saldo-container"><small>Saldo Atual em {banco_filtro} (Inc. Saldo Inicial)</small><h2>{f_brl(saldo_total)}</h2></div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("🟢 Receitas", f_brl(rec))
        t2.metric("🔴 Despesas", f_brl(desp))
        t3.metric("📈 Rendimentos", f_brl(rend))
        t4.metric("⏳ Pendências", f_brl(pend))

        st.subheader("📋 Histórico")
        df_visual = df.drop(columns=['Data_Calc'], errors='ignore').copy()
        df_visual.index = df.index + 2
        st.dataframe(df_visual.iloc[::-1], use_container_width=True)

    # FORMULÁRIO DINÂMICO
    acao_fin = st.sidebar.selectbox("Ação Financeira:", ["Novo Lançamento", "Editar/Excluir"])
    if acao_fin == "Novo Lançamento":
        with st.sidebar.form("f_fin"):
            f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            f_val = st.number_input("Valor", min_value=0.0)
            f_parc = st.number_input("Qtd Parcelas", min_value=1, value=1)
            f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
            # Puxando categorias da aba Categoria
            f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()))
            # Puxando bancos da aba Bancos + Cartões
            opcoes_pagamento = sorted(df_bancos_cad['Nome do Banco'].tolist() + df_cartoes_cad['Nome do Cartão'].tolist())
            f_bnc = st.selectbox("Destino/Banco", opcoes_pagamento)
            f_stat = st.selectbox("Status", ["Pago", "Pendente"])
            
            if st.form_submit_button("🚀 SALVAR"):
                linhas = []
                for i in range(f_parc):
                    dt = f_dat + relativedelta(months=i)
                    cat_nome = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                    linhas.append([dt.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), cat_nome, f_tip, f_bnc, f_stat])
                ws.append_rows(linhas)
                st.cache_data.clear(); st.rerun()

# ABA MILO E VEÍCULO (MANTIDAS IGUAIS)
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    df_p = pd.DataFrame(ws_p.get_all_values()[1:], columns=ws_p.get_all_values()[0])
    df_p.index = df_p.index + 2
    with st.sidebar.form("f_p"):
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY"); p_obs = st.text_input("Obs"); p_val = st.number_input("Custo", min_value=0.0)
        if st.form_submit_button("🚀 SALVAR PET"):
            ws_p.append_row([p_dat.strftime("%d/%m/%Y"), p_obs, str(p_val).replace('.', ',')])
            st.cache_data.clear(); st.rerun()
    st.dataframe(df_p.iloc[::-1], use_container_width=True)

else:
    st.title("🚗 Controle: Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    df_v = pd.DataFrame(ws_v.get_all_values()[1:], columns=ws_v.get_all_values()[0])
    df_v.index = df_v.index + 2
    with st.sidebar.form("f_v"):
        v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY"); v_km = st.number_input("KM", min_value=0); v_obs = st.text_input("Obs")
        if st.form_submit_button("🚀 SALVAR VEÍCULO"):
            ws_v.append_row([v_dat.strftime("%d/%m/%Y"), str(v_km), v_obs, "0"])
            st.cache_data.clear(); st.rerun()
    st.dataframe(df_v.iloc[::-1], use_container_width=True)
