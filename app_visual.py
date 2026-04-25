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
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        c_tipo = 'Tipo' if 'Tipo' in df_base.columns else df_base.columns[3]
        c_cat = 'Categoria' if 'Categoria' in df_base.columns else df_base.columns[2]
        c_stat = 'Status' if 'Status' in df_base.columns else df_base.columns[5]
        c_bnc = 'Banco' if 'Banco' in df_base.columns else df_base.columns[4]

        bancos_lista = ["Todos"] + sorted(list(df_base[c_bnc].unique()))
        banco_filtro = st.selectbox("🔍 Filtrar Visão por Banco:", bancos_lista)

        df = df_base[df_base[c_bnc] == banco_filtro].copy() if banco_filtro != "Todos" else df_base.copy()

        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        mes_atual = datetime.now().strftime('%m/%y')
        
        rec = df[df[c_tipo].str.contains('Receita', case=False, na=False)]['Valor_Num'].sum()
        desp = df[df[c_tipo].str.contains('Despesa', case=False, na=False)]['Valor_Num'].sum()
        saldo = rec - desp
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        st.markdown(f'<div class="saldo-container"><small>Saldo em: {banco_filtro}</small><h2>{f_brl(saldo)}</h2></div>', unsafe_allow_html=True)
        t1, t2 = st.columns(2)
        t1.metric("🟢 Receitas", f_brl(rec)); t2.metric("🔴 Despesas", f_brl(desp))

        st.subheader("📋 Histórico")
        df_visual = df.copy(); df_visual.index = df.index + 2
        st.dataframe(df_visual.iloc[::-1], use_container_width=True)

    # MENU LATERAL COM PARCELAMENTO
    acao_fin = st.sidebar.selectbox("Ação Financeira:", ["Novo Lançamento", "Editar/Excluir"])
    
    if acao_fin == "Novo Lançamento":
        with st.sidebar.form("f_fin"):
            f_dat = st.date_input("Início", datetime.now())
            f_val = st.number_input("Valor (da parcela)", min_value=0.0)
            f_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
            f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
            f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Parcelamento", "Outros"])
            f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"])
            f_stat = st.selectbox("Status", ["Pago", "Pendente"])
            
            if st.form_submit_button("🚀 SALVAR"):
                novas_linhas = []
                for i in range(f_parc):
                    data_parc = f_dat + relativedelta(months=i)
                    desc_parc = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                    novas_linhas.append([
                        data_parc.strftime("%d/%m/%Y"), 
                        str(f_val).replace('.', ','), 
                        desc_parc, f_tip, f_bnc, f_stat
                    ])
                ws.append_rows(novas_linhas)
                st.cache_data.clear(); st.rerun()
    else:
        sel_f = st.sidebar.selectbox("ID Linha para Editar:", list(df_visual.index))
        if sel_f:
            row_f = df_base.loc[sel_f-2]
            with st.sidebar.form("e_fin"):
                e_val = st.text_input("Valor", value=str(row_f['Valor']))
                e_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"], index=0)
                if st.form_submit_button("💾 ATUALIZAR"):
                    ws.update(f"B{sel_f}", [[e_val]])
                    ws.update(f"E{sel_f}", [[e_bnc]])
                    st.cache_data.clear(); st.rerun()
                if st.form_submit_button("🗑️ EXCLUIR"):
                    ws.delete_rows(int(sel_f))
                    st.cache_data.clear(); st.rerun()

# Manter Milo & Bolt e Veículo como antes
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    # ... (código anterior do pet)
else:
    st.title("🚗 Controle: Veículo")
    # ... (código anterior do veículo)
