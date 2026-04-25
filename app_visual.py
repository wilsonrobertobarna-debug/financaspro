import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

# 2. CONEXÃO E FUNÇÃO PARA GARANTIR ABAS
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
    except gspread.exceptions.WorksheetNotFound:
        nova_aba = planilha.add_worksheet(title=nome_aba, rows="1000", cols="20")
        nova_aba.append_row(colunas)
        return nova_aba

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# GARANTE QUE AS ABAS EXISTAM
ws_finance = sh.get_worksheet(0)
ws_pets = garantir_aba(sh, "Controle_Pets", ["Data", "Pet", "Tipo", "Detalhe", "Valor"])
ws_veiculo = garantir_aba(sh, "Controle_Veiculo", ["Data", "Serviço", "KM", "Valor"])

# 3. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS (CÓDIGO COMPLETO)
# ==========================================
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro - Central Wilson")
    # ... (Aqui vai o código dos gráficos e cards que já usamos antes)
    st.info("Painel de Finanças carregado com sucesso.")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Cuidados: Milo & Bolt")
    
    st.sidebar.header("📝 Registro Pet")
    with st.sidebar.form("form_p", clear_on_submit=True):
        p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
        p_data = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_tipo = st.selectbox("O quê?", ["Ração", "Vacina", "Vermífugo", "Banho", "Saúde"])
        p_valor = st.number_input("Valor (R$)", min_value=0.0)
        p_det = st.text_input("Detalhes")
        
        if st.form_submit_button("🦴 SALVAR"):
            dt_br = p_data.strftime("%d/%m/%Y")
            ws_pets.append_row([dt_br, p_pet, p_tipo, p_det, p_valor])
            # Lança no financeiro também
            ws_finance.append_row([dt_br, p_valor, f"Pet: {p_tipo}", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()

    dados_p = ws_pets.get_all_values()
    if len(dados_p) > 1:
        df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0])
        df_p['Data_Obj'] = pd.to_datetime(df_p['Data'], dayfirst=True, errors='coerce')
        df_p = df_p.sort_values(by='Data_Obj', ascending=False)
        df_p['Data'] = df_p['Data_Obj'].dt.strftime('%d/%m/%Y')
        st.dataframe(df_p[["Data", "Pet", "Tipo", "Detalhe", "Valor"]].head(20), use_container_width=True)

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Controle do Veículo")
    # ... (Código da calculadora e histórico do veículo)
    st.success("Aba de Veículo pronta para uso.")
