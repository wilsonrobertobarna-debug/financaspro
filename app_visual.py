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

if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🛡️ FinançasPro Wilson</h1><p style='text-align: center; font-size: 1.5rem; margin-top: -10px;'>🐾<br>🐾</p>", unsafe_allow_html=True)
    
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Colunas e Cálculos
        c_tipo = 'Tipo'; c_cat = 'Categoria'; c_stat = 'Status'; c_bnc = 'Banco'
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum()
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum()
        rend = df[df[c_cat].str.contains('Rendimento', case=False)]['Valor_Num'].sum()
        pend = df[df[c_stat].str.contains('Pendente', case=False)]['Valor_Num'].sum()
        saldo = rec - desp
        eco_perc = (saldo / rec * 100) if rec > 0 else 0
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # Dashboard
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual</small><h2>{f_brl(saldo)}</h2></div>', unsafe_allow_html=True)
        t1, t2, t3, t4 = st.columns(4)
        t1.metric("🟢 Receitas", f_brl(rec)); t2.metric("🔴 Despesas", f_brl(desp))
        t3.metric("📈 Rendimentos", f_brl(rend)); t4.metric("⏳ Pendências", f_brl(pend))
        st.markdown(f'<div class="economia-texto">🔹 Economia Real: {f_brl(saldo)} ({eco_perc:.1f}%)</div>', unsafe_allow_html=True)

        st.subheader("📋 Histórico")
        st.dataframe(df.iloc[::-1], use_container_width=True)

    # --- NOVO: FORMULÁRIOS NO MENU LATERAL ---
    menu_acao = st.sidebar.selectbox("Ação:", ["Novo Lançamento", "Editar/Excluir"])

    if menu_acao == "Novo Lançamento":
        with st.sidebar.form("f_novo"):
            st.subheader("📝 Novo")
            f_dat = st.date_input("Data", datetime.now())
            f_val = st.number_input("Valor", min_value=0.0)
            f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
            f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
            f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro"])
            f_stat = st.selectbox("Status", ["Pago", "Pendente"])
            if st.form_submit_button("🚀 SALVAR"):
                ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
                st.cache_data.clear(); st.rerun()

    elif menu_acao == "Editar/Excluir":
        st.sidebar.subheader("⚙️ Gerenciar")
        # Wilson, aqui você escolhe a linha pelo número (2 é a primeira depois do cabeçalho)
        linhas = [i + 2 for i in range(len(df))]
        escolha = st.sidebar.selectbox("Selecione a linha da tabela:", linhas, format_func=lambda x: f"Linha {x}")
        
        # Carrega dados atuais da linha escolhida
        row_idx = escolha - 2
        dados_atuais = df.iloc[row_idx]

        with st.sidebar.form("f_edita"):
            e_dat = st.text_input("Data", value=dados_atuais['Data'])
            e_val = st.text_input("Valor", value=dados_atuais['Valor'])
            e_tip = st.selectbox("Tipo", ["Despesa", "Receita"], index=0 if dados_atuais[c_tipo]=="Despesa" else 1)
            e_cat = st.text_input("Categoria", value=dados_atuais[c_cat])
            e_bnc = st.text_input("Banco", value=dados_atuais[c_bnc])
            e_stat = st.selectbox("Status", ["Pago", "Pendente"], index=0 if dados_atuais[c_stat]=="Pago" else 1)
            
            col_ed1, col_ed2 = st.columns(2)
            btn_up = col_ed1.form_submit_button("💾 ATUALIZAR")
            btn_del = col_ed2.form_submit_button("🗑️ EXCLUIR")

            if btn_up:
                ws.update(f"A{escolha}:F{escolha}", [[e_dat, e_val, e_cat, e_tip, e_bnc, e_stat]])
                st.cache_data.clear(); st.rerun()
            
            if btn_del:
                ws.delete_rows(escolha)
                st.cache_data.clear(); st.rerun()

# (Abas de Pets e Veículo continuam abaixo conforme código anterior)
