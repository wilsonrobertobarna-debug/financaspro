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
    .economia { background-color: #6f42c1; font-size: 1.1rem !important; border: 2px solid #ffffff55; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
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

# --- NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])
banco_selecionado = st.sidebar.selectbox("Filtrar por Banco:", ["Todos", "Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor Total (R$)", min_value=0.0, format="%.2f")
        f_cat = st.text_input("Categoria")
        f_parc = st.number_input("Parcelas", min_value=1, max_value=48, value=1)
        f_tipo = st.selectbox("Tipo:", ["Receita", "Despesa", "Rendimento", "Pendência"])
        f_banco = st.selectbox("Banco:", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
        f_status = st.text_input("Status", value="Pago")
        if st.form_submit_button("🚀 SALVAR FINANÇAS"):
            dt_br = f_data.strftime("%d/%m/%Y")
            ws_finance.append_row([dt_br, f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    try:
        dados_list = ws_finance.get_all_values()
        if len(dados_list) > 1:
            df = pd.DataFrame(dados_list[1:], columns=dados_list[0]).iloc[:, :6]
            df.columns = [c.strip() for c in df.columns]
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df_v = df.dropna(subset=['Data']).copy()

            if banco_selecionado != "Todos":
                df_v = df_v[df_v['Banco'] == banco_selecionado]

            # CÁLCULOS GERAIS
            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            saldo_total = (v_rec + v_rend) - v_des

            # CÁLCULO DE ECONOMIA (Mês Atual ou Total se vazio)
            mes_ref = datetime.now().strftime('%m/%Y')
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            df_mes = df_v[df_v['Mês/Ano'] == mes_ref]
            
            # Se não tiver dados no mês, usa o total para o cálculo de economia
            calc_rec = df_mes[df_mes['Tipo'].isin(['Receita', 'Rendimento'])]['Valor'].sum() if not df_mes.empty else (v_rec + v_rend)
            calc_des = df_mes[df_mes['Tipo'] == 'Despesa']['Valor'].sum() if not df_mes.empty else v_des
            
            valor_economizado = calc_rec - calc_des
            porcentagem = (valor_economizado / calc_rec * 100) if calc_rec > 0 else 0

            # EXIBIÇÃO PRINCIPAL
            st.title(f"🛡️ FinançasPro Wilson")
            st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL EM CONTA</small><h1 style="margin:0;">R$ {saldo_total:,.2f}</h1></div>', unsafe_allow_html=True)
            
            # FILEIRA DE CARDS
            st.markdown(f"""
                <div class="card-container">
                    <div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div>
                    <div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div>
                    <div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div>
                    <div class="card economia"><b>Resumo Economia</b><br>{porcentagem:.1f}% (R$ {valor_economizado:,.2f})</div>
                </div>
                """, unsafe_allow_html=True)

            # GRÁFICOS
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("📊 Evolução Mensal")
                res_m = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
                fig1 = go.Figure()
                if 'Receita' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Receita'], name='Receitas', marker_color='#28a745'))
                if 'Despesa' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Despesa'], name='Despesas', marker_color='#dc3545'))
                st.plotly_chart(fig1, use_container_width=True)
            with col2:
                st.subheader("🎯 Gastos por Categoria")
                res_cat = df_v[df_v['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False).reset_index()
                if not res_cat.empty:
                    fig2 = go.Figure(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff'))
                    st.plotly_chart(fig2, use_container_width=True)

            st.subheader("📋 Últimos Lançamentos")
            df_table = df_v.tail(10).copy()
            df_table['Data'] = df_table['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_table.iloc[::-1], use_container_width=True)

    except Exception as e: st.error(f"Erro ao carregar dados: {e}")

# (As outras abas Pets e Veículo seguem integradas conforme conversamos)
