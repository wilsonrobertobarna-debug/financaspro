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
    .card { flex: 1; padding: 15px; border-radius: 10px; color: white; text-align: center; font-weight: bold; font-size: 0.85rem; }
    .receita { background-color: #28a745; }
    .despesa { background-color: #dc3545; }
    .rendimento { background-color: #17a2b8; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO E UTILITÁRIOS
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

def garantir_aba(planilha, nome_aba, colunas):
    try:
        return planilha.worksheet(nome_aba)
    except:
        nova = planilha.add_worksheet(title=nome_aba, rows="1000", cols="10")
        nova.append_row(colunas)
        return nova

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# INICIALIZA AS ABAS
ws_finance = sh.get_worksheet(0)
ws_pets = garantir_aba(sh, "Controle_Pets", ["Data", "Pet", "Tipo", "Detalhe", "Valor"])
ws_veiculo = garantir_aba(sh, "Controle_Veiculo", ["Data", "Serviço", "KM", "Valor"])

# 3. MENU LATERAL
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
            ws_finance.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, f_tipo, f_banco, f_status])
            st.cache_data.clear(); st.rerun()

    dados = ws_finance.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"])
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data_Obj'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df_v = df.dropna(subset=['Data_Obj']).sort_values(by='Data_Obj', ascending=False)
        
        v_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
        v_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
        v_rend = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
        saldo = (v_rec + v_rend) - v_des

        st.title("🛡️ FinançasPro - Central Wilson")
        st.markdown(f'<div class="saldo-container"><small>SALDO ATUAL</small><h1 style="margin:0;">R$ {saldo:,.2f}</h1></div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="card-container"><div class="card receita">Receitas<br>R$ {v_rec:,.2f}</div><div class="card despesa">Despesas<br>R$ {v_des:,.2f}</div><div class="card rendimento">Rendimentos<br>R$ {v_rend:,.2f}</div></div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            df_v['Mês/Ano'] = df_v['Data_Obj'].dt.strftime('%m/%Y')
            res_m = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Receita'], name='Rec', marker_color='#28a745'))
            if 'Despesa' in res_m: fig1.add_trace(go.Bar(x=res_m['Mês/Ano'], y=res_m['Despesa'], name='Des', marker_color='#dc3545'))
            st.plotly_chart(fig1, use_container_width=True)
        with c2:
            res_cat = df_v[df_v['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().sort_values(ascending=False).reset_index()
            if not res_cat.empty:
                st.plotly_chart(go.Figure(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff')), use_container_width=True)

        df_v['Data'] = df_v['Data_Obj'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_v[["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"]].head(15), use_container_width=True)

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Cuidados: Milo & Bolt")
    with st.sidebar.form("form_p", clear_on_submit=True):
        p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
        p_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_tipo = st.selectbox("O quê?", ["Ração", "Vacina", "Vermífugo", "Banho", "Saúde"])
        p_valor = st.number_input("Valor (R$)", min_value=0.0)
        p_det = st.text_input("Detalhes")
        if st.form_submit_button("🦴 SALVAR"):
            dt_br = p_data.strftime("%d/%m/%Y")
            ws_pets.append_row([dt_br, p_pet, p_tipo, p_det, p_valor])
            ws_finance.append_row([dt_br, p_valor, f"Pet: {p_tipo} ({p_pet})", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()

    dados_p = ws_pets.get_all_values()
    if len(dados_p) > 1:
        df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0])
        df_p['Data_Obj'] = pd.to_datetime(df_p['Data'], dayfirst=True, errors='coerce')
        df_p = df_p.dropna(subset=['Data_Obj']).sort_values(by='Data_Obj', ascending=False)
        df_p['Data'] = df_p['Data_Obj'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_p[["Data", "Pet", "Tipo", "Detalhe", "Valor"]].head(20), use_container_width=True)
    else:
        st.info("Nenhum registro encontrado para os meninos.")

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Controle do Veículo")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("⛽ Calculadora Flex")
        alc = st.number_input("Álcool", min_value=0.0)
        gas = st.number_input("Gasolina", min_value=0.0)
        if alc > 0 and gas > 0:
            res = alc/gas
            st.write(f"Proporção: {res:.2f}")
            st.success("VÁ DE ÁLCOOL" if res <= 0.7 else "VÁ DE GASOLINA")

    with c2:
        with st.sidebar.form("form_v", clear_on_submit=True):
            v_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            v_tipo = st.selectbox("Serviço", ["Abastecimento", "Troca de Óleo", "Manutenção", "Outros"])
            v_km = st.number_input("KM", min_value=0)
            v_valor = st.number_input("Valor", min_value=0.0)
            if st.form_submit_button("🚗 SALVAR"):
                dt_br = v_data.strftime("%d/%m/%Y")
                ws_veiculo.append_row([dt_br, v_tipo, v_km, v_valor])
                ws_finance.append_row([dt_br, v_valor, f"Carro: {v_tipo}", "Despesa", "Nubank", "Pago"])
                st.cache_data.clear(); st.rerun()

        dados_v = ws_veiculo.get_all_values()
        if len(dados_v) > 1:
            df_v = pd.DataFrame(dados_v[1:], columns=dados_v[0])
            df_v['Data_Obj'] = pd.to_datetime(df_v['Data'], dayfirst=True, errors='coerce')
            df_v = df_v.dropna(subset=['Data_Obj']).sort_values(by='Data_Obj', ascending=False)
            df_v['Data'] = df_v['Data_Obj'].dt.strftime('%d/%m/%Y')
            st.dataframe(df_v[["Data", "Serviço", "KM", "Valor"]].head(15), use_container_width=True)
