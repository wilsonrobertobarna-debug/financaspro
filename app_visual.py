import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 0.9rem; }
    .receita { background-color: #28a745; }
    .despesa { background-color: #dc3545; }
    .rendimento { background-color: #17a2b8; }
    .economia { background-color: #6f42c1; }
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
ws_finance = sh.get_worksheet(0)

# LISTAS DE SELEÇÃO (Para evitar erros de digitação)
LISTA_CATEGORIAS = ["Mercado", "Shopee", "Mercado Livre", "AserNet", "Skyfit", "Farmácia", "Combustível", "Milo/Bolt", "Lazer", "Outros"]
LISTA_TIPOS = ["Receita", "Despesa", "Rendimento", "Pendência"]
LISTA_STATUS = ["Pago", "Pendente"]
LISTA_BANCOS = ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"]

# --- NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])
banco_selecionado = st.sidebar.selectbox("Filtrar por Banco:", ["Todos"] + LISTA_BANCOS)

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        f_cat = st.selectbox("Categoria", LISTA_CATEGORIAS)
        f_tipo = st.selectbox("Tipo", LISTA_TIPOS)
        f_banco = st.selectbox("Banco", LISTA_BANCOS)
        f_status = st.selectbox("Status", LISTA_STATUS)
        
        if st.form_submit_button("🚀 SALVAR NAS FINANÇAS"):
            dt_br = f_data.strftime("%d/%m/%Y")
            ws_finance.append_row([dt_br, f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    try:
        dados_list = ws_finance.get_all_values()
        if len(dados_list) > 1:
            df = pd.DataFrame(dados_list[1:], columns=dados_list[0]).iloc[:, :6]
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df_v = df.dropna(subset=['Data']).sort_values(by='Data', ascending=False) # ORDEM RECENTE NO TOPO

            if banco_selecionado != "Todos":
                df_v = df_v[df_v['Banco'] == banco_selecionado]

            # CÁLCULOS
            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            saldo_total = (v_rec + v_rend) - v_des
            perc_eco = ((v_rec + v_rend - v_des) / (v_rec + v_rend) * 100) if (v_rec+v_rend) > 0 else 0

            st.title(f"🛡️ FinançasPro Wilson")
            st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL</small><h1 style="margin:0;">R$ {saldo_total:,.2f}</h1></div>', unsafe_allow_html=True)
            
            st.markdown(f"""
                <div class="card-container">
                    <div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div>
                    <div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div>
                    <div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div>
                    <div class="card economia">Economia<br>{perc_eco:.1f}%</div>
                </div>
                """, unsafe_allow_html=True)

            st.subheader("📋 Últimos Lançamentos (Mais recentes primeiro)")
            # Formata data para exibição BR na tabela
            df_display = df_v.copy()
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_display.head(20), use_container_width=True)

    except Exception as e: st.error(f"Erro: {e}")

# (As abas Pets e Veículo seguem o mesmo padrão de listas)
