import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
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

# 3. INTERFACE DE NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# --- FUNÇÃO DE TABELA INTELIGENTE ---
def exibir_tabela_dinamica(aba_sheet, titulo):
    dados = aba_sheet.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        try:
            col_data = dados[0][0]
            df['Data_Sort'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            df = df.sort_values(by='Data_Sort', ascending=False).drop(columns=['Data_Sort'])
        except: pass
        st.subheader(f"📋 {titulo}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"Aba {titulo} vazia.")

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.title("🛡️ FinançasPro - Central Wilson")
    
    with st.sidebar.form("f_fin", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor (R$)", min_value=0.0)
        f_cat = st.selectbox("Categoria", ["Mercado", "Shopee", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Outros"])
        if st.form_submit_button("🚀 SALVAR FINANCEIRO"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
            
    exibir_tabela_dinamica(ws, "Histórico Financeiro Geral")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    ws = sh.worksheet("Controle_Pets")
    st.title("🐾 Cuidados: Milo & Bolt")
    
    with st.sidebar.form("f_pet", clear_on_submit=True):
        p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_tip = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Saúde"])
        p_val = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("🦴 SALVAR NO PET"):
            dt_s = p_dat.strftime("%d/%m/%Y")
            ws.append_row([dt_s, p_pet, p_tip, "Lançamento App", str(p_val).replace('.', ',')])
            sh.get_worksheet(0).append_row([dt_s, str(p_val).replace('.', ','), f"Pet: {p_tip}", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
            
    exibir_tabela_dinamica(ws, "Histórico dos Meninos")

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    ws = sh.worksheet("Controle_Veiculo")
    st.title("🚗 Controle do Veículo")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("⛽ Calculadora Flex")
        alc = st.number_input("Preço Álcool", min_value=0.0)
        gas = st.number_input("Preço Gasolina", min_value=0.0)
        if alc > 0 and gas > 0:
            res = alc / gas
            st.metric("Proporção", f"{res:.2f}")
            if res <= 0.7: st.success("VÁ DE ÁLCOOL! ✅")
            else: st.warning("VÁ DE GASOLINA! ⛽")

    with c2:
        with st.sidebar.form("f_vei", clear_on_submit=True):
            v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            v_tip = st.selectbox("Serviço", ["Abastecimento", "Troca de Óleo", "Manutenção", "Lavagem"])
            v_det = st.text_input("Descrição (Ex: Posto, Marca do Óleo)")
            v_km = st.number_input("KM Atual", min_value=0)
            v_val = st.number_input("Valor Pago (R$)", min_value=0.0)
            
            if st.form_submit_button("🚗 SALVAR NO VEÍCULO"):
                dt_s = v_dat.strftime("%d/%m/%Y")
                # ORDEM: Data | Serviço | Descrição | KM | Valor
                ws.append_row([dt_s, v_tip, v_det, str(v_km), str(v_val).replace('.', ',')])
                # LANÇA NO FINANCEIRO GERAL
                sh.get_worksheet(0).append_row([dt_s, str(v_val).replace('.', ','), f"Veículo: {v_tip}", "Despesa", "Nubank", "Pago"])
                st.cache_data.clear(); st.rerun()
                
    exibir_tabela_dinamica(ws, "Histórico do Veículo")
