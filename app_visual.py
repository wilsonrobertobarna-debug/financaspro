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
    .pendencia { background-color: #ffc107; color: #212529; }
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

# --- NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
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
            # Ajuste da data para formato brasileiro DD/MM/YYYY
            data_br = f_data.strftime("%d/%m/%Y")
            # Adicionamos a info de parcelas na descrição ou coluna extra
            desc_com_parc = f"{f_cat} ({f_parc}x)"
            ws.append_row([data_br, f_valor, desc_com_parc, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    try:
        dados_list = ws.get_all_values()
        if len(dados_list) > 1:
            df = pd.DataFrame(dados_list[1:], columns=dados_list[0]).iloc[:, :6]
            df.columns = [c.strip() for c in df.columns]
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            
            # Força a leitura da data no formato brasileiro
            df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df_v = df.dropna(subset=['Data']).copy()

            st.title("🛡️ FinançasPro Wilson")
            
            # CARDS
            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            v_pend = df_v[df_v['Tipo'] == 'Pendência']['Valor'].sum()
            
            st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL</small><h1 style="margin:0;">R$ {(v_rec + v_rend) - v_des:,.2f}</h1></div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-container"><div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div><div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div><div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div><div class="card pendencia">Pendentes<br>R$ {v_pend:,.2f}</div></div>', unsafe_allow_html=True)

            st.subheader("📋 Últimos Lançamentos")
            df_table = df_v.tail(10).copy()
            df_table['Data'] = df_table['Data'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_table.iloc[::-1], use_container_width=True)

            # GRÁFICOS
            st.markdown("---")
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Evolução Mensal")
                df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
                res_m = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
                fig1 = go.Figure()
                if 'Receita' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Receita'], name='Receitas', marker_color='#28a745'))
                if 'Despesa' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Despesa'], name='Despesas', marker_color='#dc3545'))
                st.plotly_chart(fig1, use_container_width=True)

            with col2:
                st.subheader("🎯 Gastos por Categoria")
                mes_atual = datetime.now().strftime('%m/%Y')
                df_mes = df_v[(df_v['Mês/Ano'] == mes_atual) & (df_v['Tipo'] == 'Despesa')]
                res_cat = df_mes.groupby('Categoria')['Valor'].sum().sort_values(ascending=False).reset_index()
                if not res_cat.empty:
                    fig2 = go.Figure(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff'))
                    st.plotly_chart(fig2, use_container_width=True)

    except Exception as e: st.error(f"Erro: {e}")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    try:
        ws_p = sh.worksheet("Controle_Pets")
        st.sidebar.header("📋 Registrar p/ os Meninos")
        with st.sidebar.form("form_p", clear_on_submit=True):
            p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
            p_data = st.date_input("Data", datetime.now())
            p_tipo = st.selectbox("O quê?", ["Vacina", "Banho", "Ração/Petiscos", "Saúde", "Brinquedos"])
            p_desc = st.text_input("Descrição")
            p_valor = st.number_input("Valor (R$)", min_value=0.0)
            p_prox = st.date_input("Agendar Próximo?", p_data + timedelta(days=7))
            if st.form_submit_button("🦴 SALVAR REGISTRO PET"):
                ws_p.append_row([p_data.strftime("%d/%m/%Y"), p_pet, p_tipo, p_desc, p_valor, p_prox.strftime("%d/%m/%Y")])
                st.cache_data.clear(); st.rerun()

        dados_p = ws_p.get_all_values()
        if len(dados_p) > 1:
            dp = pd.DataFrame(dados_p[1:], columns=dados_p[0]).iloc[:, :6]
            # Formatação de moeda para visualização
            val_pet = pd.to_numeric(dp['Valor'].str.replace(',','.'), errors='coerce').sum()
            st.metric("Total Gasto c/ Meninos", f"R$ {val_pet:,.2f}")
            st.dataframe(dp.iloc[::-1], use_container_width=True)
    except: st.info("Certifique-se de que a aba 'Controle_Pets' existe no Sheets.")

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    try:
        ws_v = sh.worksheet("Controle_Veiculo")
        st.sidebar.header("⛽ Registrar Gasto")
        with st.sidebar.form("form_v", clear_on_submit=True):
            v_data = st.date_input("Data", datetime.now())
            v_tipo = st.selectbox("Tipo", ["Combustível", "Manutenção", "Óleo", "Seguro"])
            v_km = st.number_input("KM Atual", min_value=0)
            v_valor = st.number_input("Valor (R$)", min_value=0.0)
            v_desc = st.text_input("Detalhes")
            if st.form_submit_button("🏎️ SALVAR VEÍCULO"):
                ws_v.append_row([v_data.strftime("%d/%m/%Y"), v_tipo, v_desc, v_km, v_valor])
                st.cache_data.clear(); st.rerun()

        dados_v = ws_v.get_all_values()
        if len(dados_v) > 1:
            dv = pd.DataFrame(dados_v[1:], columns=dados_v[0]).iloc[:, :5]
            val_veic = pd.to_numeric(dv['Valor'].str.replace(',','.'), errors='coerce').sum()
            st.metric("Gasto Total Veículo", f"R$ {val_veic:,.2f}")
            st.dataframe(dv.iloc[::-1], use_container_width=True)
    except: st.info("Certifique-se de que a aba 'Controle_Veiculo' existe no Sheets.")
