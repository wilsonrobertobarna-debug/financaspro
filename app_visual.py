import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime, timedelta

# 1. CONEXÃO (Reutilizando sua lógica atual)
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

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

# --- ABA: CONTROLE DOS MENINOS (MILO) ---
if aba == "🐾 Controle dos Meninos":
    st.title("🐾 Controle do Milo")
    
    # Conexão com a aba específica
    try:
        ws_milo = sh.worksheet("Controle_Milo")
    except:
        st.error("Aba 'Controle_Milo' não encontrada no Google Sheets. Crie-a para começar.")
        st.stop()

    # Formulário de Entrada
    st.sidebar.header("📋 Registrar Evento")
    with st.sidebar.form("form_milo", clear_on_submit=True):
        m_data = st.date_input("Data do Evento", datetime.now())
        m_tipo = st.selectbox("Tipo", ["Vacina", "Banho", "Ração/Petisco", "Veterinário", "Outros Gastos"])
        m_desc = st.text_input("Descrição (Ex: V10, Banho Semanal, Antipulgas)")
        m_valor = st.number_input("Custo (R$)", min_value=0.0, format="%.2f")
        
        # Lógica de sugestão de próxima data
        sugestao_prox = m_data + timedelta(days=7) if m_tipo == "Banho" else m_data + timedelta(days=30)
        m_prox = st.date_input("Agendar Próximo (Opcional)", sugestao_prox)
        
        if st.form_submit_button("🦴 REGISTRAR PARA O MILO"):
            ws_milo.append_row([
                m_data.strftime("%d/%m/%Y"), 
                m_tipo, 
                m_desc, 
                m_valor, 
                m_prox.strftime("%d/%m/%Y")
            ])
            st.cache_data.clear()
            st.success("Dados do Milo salvos!")
            st.rerun()

    # Exibição dos Dados
    try:
        dados_milo = ws_milo.get_all_values()
        if len(dados_milo) > 1:
            df_milo = pd.DataFrame(dados_milo[1:], columns=dados_raw[0] if 'dados_raw' in locals() else dados_milo[0])
            
            # Resumo rápido
            gastos_totais = pd.to_numeric(df_milo['Valor'].str.replace(',', '.'), errors='coerce').sum()
            
            col1, col2 = st.columns(2)
            col1.metric("Gasto Total com Milo", f"R$ {gastos_totais:,.2f}")
            
            # Próximos Compromissos (Vacinas/Banhos)
            st.subheader("🗓️ Próximos Eventos Agendados")
            df_milo['Próxima Data'] = pd.to_datetime(df_milo['Próxima Data'], dayfirst=True, errors='coerce')
            hoje = datetime.now()
            agenda = df_milo[df_milo['Próxima Data'] >= hoje].sort_values('Próxima Data')
            
            if not agenda.empty:
                st.table(agenda[['Tipo', 'Descrição', 'Próxima Data']].head(5))
            
            st.subheader("📜 Histórico Completo")
            st.dataframe(df_milo.iloc[::-1], use_container_width=True)
            
    except Exception as e:
        st.info("Ainda não há registros para o Milo. Use o formulário lateral!")

# (Manter aqui o código das outras abas...)
