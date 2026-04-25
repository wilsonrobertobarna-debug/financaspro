import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 12px; text-align: center; margin-bottom: 25px; }
    .card-container { display: flex; justify-content: space-between; gap: 10px; margin-bottom: 25px; }
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 0.9rem; }
    .receita { background-color: #28a745; }
    .despesa { background-color: #dc3545; }
    .rendimento { background-color: #17a2b8; }
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

# 3. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY") 
        f_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_cat = st.selectbox("Categoria", ["Mercado", "Shopee", "Mercado Livre", "AserNet", "Skyfit", "Farmácia", "Combustível", "Milo/Bolt", "Lazer", "Outros"])
        f_tipo = st.selectbox("Tipo", ["Receita", "Despesa", "Rendimento", "Pendência"])
        f_banco = st.selectbox("Banco", ["Nubank", "Itaú", "Bradesco", "Dinheiro", "Outros"])
        f_status = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("🚀 SALVAR"):
            dt_br = f_data.strftime("%d/%m/%Y")
            ws_finance.append_row([dt_br, f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    try:
        dados = ws_finance.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"])
            df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            df['Data_Obj'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
            df_v = df.dropna(subset=['Data_Obj']).sort_values(by='Data_Obj', ascending=False)
            df_v['Data'] = df_v['Data_Obj'].dt.strftime('%d/%m/%Y')

            v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            saldo = (v_rec + v_rend) - v_des

            st.title("🛡️ FinançasPro - Central Wilson")
            st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL</small><h1 style="margin:0;">R$ {saldo:,.2f}</h1></div>', unsafe_allow_html=True)
            st.markdown(f"""<div class="card-container"><div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div><div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div><div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div></div>""", unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📊 Evolução Mensal")
                df_v['Mês/Ano'] = df_v['Data_Obj'].dt.strftime('%m/%Y')
                res_m = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
                fig1 = go.Figure()
                if 'Receita' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Receita'], name='Rec', marker_color='#28a745'))
                if 'Despesa' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Despesa'], name='Des', marker_color='#dc3545'))
                st.plotly_chart(fig1, use_container_width=True)
            with c2:
                st.subheader("🎯 Por Categoria")
                res_cat = df_v[df_v['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False).reset_index()
                if not res_cat.empty:
                    fig2 = go.Figure(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff'))
                    st.plotly_chart(fig2, use_container_width=True)
            st.dataframe(df_v[["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"]].head(15), use_container_width=True)
    except Exception as e: st.error(f"Erro: {e}")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Cuidados: Milo & Bolt")
    try:
        ws_p = sh.worksheet("Controle_Pets")
        st.sidebar.header("📝 Registro Pet")
        with st.sidebar.form("form_p", clear_on_submit=True):
            p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
            p_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            p_tipo = st.selectbox("O quê?", ["Ração", "Vacina", "Vermífugo", "Banho", "Saúde"])
            p_valor = st.number_input("Valor (R$)", min_value=0.0)
            if st.form_submit_button("🦴 SALVAR"):
                dt_br = p_data.strftime("%d/%m/%Y")
                ws_p.append_row([dt_br, p_pet, p_tipo, "Cuidado Pet", p_valor])
                ws_finance.append_row([dt_br, p_valor, f"Pet: {p_tipo}", "Despesa", "Nubank", "Pago"])
                st.cache_data.clear(); st.rerun()

        dp_list = ws_p.get_all_values()
        if len(dp_list) > 1:
            dp = pd.DataFrame(dp_list[1:], columns=["Data", "Pet", "Tipo", "Detalhe", "Valor"])
            dp['Data_Obj'] = pd.to_datetime(dp['Data'], dayfirst=True, errors='coerce')
            dp = dp.sort_values(by='Data_Obj', ascending=False)
            dp['Data'] = dp['Data_Obj'].dt.strftime('%d/%m/%Y')
            st.dataframe(dp[["Data", "Pet", "Tipo", "Detalhe", "Valor"]].head(20), use_container_width=True)
    except: st.error("Crie a aba 'Controle_Pets' na planilha.")

# ==========================================
# ABA 3: MEU VEÍCULO (LIBERADA!)
# ==========================================
else:
    st.title("🚗 Controle do Veículo")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("⛽ Calculadora Flex")
        alc = st.number_input("Preço Álcool (R$)", min_value=0.0, format="%.2f")
        gas = st.number_input("Preço Gasolina (R$)", min_value=0.0, format="%.2f")
        if alc > 0 and gas > 0:
            proporcao = alc / gas
            if proporcao <= 0.7:
                st.success(f"Proporção: {proporcao:.2f} - VÁ DE ÁLCOOL! ✅")
            else:
                st.warning(f"Proporção: {proporcao:.2f} - VÁ DE GASOLINA! ⛽")

    with col_b:
        try:
            ws_v = sh.worksheet("Controle_Veiculo")
            st.sidebar.header("📝 Novo Registro Veicular")
            with st.sidebar.form("form_v", clear_on_submit=True):
                v_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
                v_tipo = st.selectbox("Tipo", ["Abastecimento", "Troca de Óleo", "Manutenção", "Lavagem", "Outros"])
                v_km = st.number_input("KM Atual", min_value=0)
                v_valor = st.number_input("Valor (R$)", min_value=0.0)
                if st.form_submit_button("🚗 SALVAR"):
                    dt_br = v_data.strftime("%d/%m/%Y")
                    ws_v.append_row([dt_br, v_tipo, v_km, v_valor])
                    ws_finance.append_row([dt_br, v_valor, "Combustível" if v_tipo=="Abastecimento" else "Outros", "Despesa", "Nubank", "Pago"])
                    st.cache_data.clear(); st.rerun()

            dv_list = ws_v.get_all_values()
            if len(dv_list) > 1:
                dv = pd.DataFrame(dv_list[1:], columns=["Data", "Serviço", "KM", "Valor"])
                dv['Data_Obj'] = pd.to_datetime(dv['Data'], dayfirst=True, errors='coerce')
                dv = dv.sort_values(by='Data_Obj', ascending=False)
                dv['Data'] = dv['Data_Obj'].dt.strftime('%d/%m/%Y')
                st.subheader("📋 Histórico do Veículo")
                st.dataframe(dv[["Data", "Serviço", "KM", "Valor"]].head(15), use_container_width=True)
        except:
            st.error("Por favor, crie a aba 'Controle_Veiculo' na sua planilha.")
