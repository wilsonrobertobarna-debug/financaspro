import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

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

# 3. INTERFACE
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# --- FUNÇÃO AUXILIAR PARA EXIBIR TABELAS SEM CONFLITO ---
def exibir_tabela_segura(aba_sheet, titulo):
    dados = aba_sheet.get_all_values()
    if len(dados) > 1:
        # Usa a primeira linha da planilha como cabeçalho, seja qual for
        df = pd.DataFrame(dados[1:], columns=dados[0])
        
        # Tenta converter a data apenas para organizar a ordem (mais recentes primeiro)
        try:
            col_data = dados[0][0] # Assume que a primeira coluna é a data
            df['temp_data'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            df = df.sort_values(by='temp_data', ascending=False).drop(columns=['temp_data'])
        except:
            pass
            
        st.subheader(f"📋 {titulo}")
        st.dataframe(df, use_container_width=True)
    else:
        st.info(f"Aba '{aba_sheet.title}' pronta. Aguardando lançamentos.")

# ==========================================
# LÓGICA DAS ABAS
# ==========================================

if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.title("🛡️ FinançasPro - Central Wilson")
    
    with st.sidebar.form("f_fin"):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_cat = st.selectbox("Categoria", ["Mercado", "Shopee", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Outros"])
        if st.form_submit_button("🚀 SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val), f_cat, "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
    
    exibir_tabela_segura(ws, "Histórico Financeiro")

elif aba == "🐾 Milo & Bolt":
    ws = sh.worksheet("Controle_Pets")
    st.title("🐾 Cuidados: Milo & Bolt")
    
    with st.sidebar.form("f_pet"):
        p_pet = st.selectbox("Pet", ["Milo", "Bolt", "Os Dois"])
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_tip = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Saúde"])
        p_val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("🦴 SALVAR"):
            dt_s = p_dat.strftime("%d/%m/%Y")
            ws.append_row([dt_s, p_pet, p_tip, "Lançamento App", str(p_val)])
            sh.get_worksheet(0).append_row([dt_s, str(p_val), "Milo/Bolt", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
            
    exibir_tabela_segura(ws, "Histórico dos Meninos")

else:
    ws = sh.worksheet("Controle_Veiculo")
    st.title("🚗 Controle do Veículo")
    
    with st.sidebar.form("f_vei"):
        v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        v_tip = st.selectbox("Serviço", ["Abastecimento", "Manutenção", "Óleo"])
        v_km = st.number_input("KM", min_value=0)
        v_val = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("🚗 SALVAR"):
            dt_s = v_dat.strftime("%d/%m/%Y")
            ws.append_row([dt_s, v_tip, str(v_km), str(v_val)])
            sh.get_worksheet(0).append_row([dt_s, str(v_val), "Combustível", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
            
    exibir_tabela_segura(ws, "Histórico do Veículo")
