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
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .tag-card { background-color: #ffffff; padding: 12px; border-radius: 8px; border-left: 5px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .alerta-oleo { padding: 15px; border-radius: 8px; margin-bottom: 20px; font-weight: bold; text-align: center; border: 2px solid; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
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
        st.error(f"Erro: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# CONFIGURAÇÕES TÉCNICAS
ESTOQUE_TOTAL_RACAO = 15.0 

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.selectbox("Módulo:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "🚗 Meu Veículo":
    st.sidebar.header("⚙️ Configurar Alertas")
    # Este valor poderia ser salvo na planilha, aqui ele inicia com um padrão
    proxima_troca = st.sidebar.number_input("KM da Próxima Troca de Óleo", value=50000, step=1000)
    
    st.sidebar.header("⛽ Novo Abastecimento")
    with st.sidebar.form("form_v", clear_on_submit=True):
        v_data = st.date_input("Data", datetime.now())
        v_km = st.number_input("Quilometragem Atual (KM)", min_value=0)
        v_litros = st.number_input("Litros", min_value=0.0)
        v_preco = st.number_input("Total R$", min_value=0.0)
        if st.form_submit_button("Registrar no Sistema"):
            ws.append_row([v_data.strftime("%d/%m/%Y"), v_preco, "Combustível", "Veículo", f"KM:{v_km}|L:{v_litros}"])
            st.cache_data.clear(); st.rerun()
# ... (Outros formulários de sidebar simplificados para foco no veículo)

# --- PROCESSAMENTO ---
try:
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        if aba == "🚗 Meu Veículo":
            st.title("🚗 Gestão do Veículo")
            
            df_car = df_v[df_v['Categoria'] == 'Combustível'].copy()
            df_car['KM'] = df_car['Descrição'].str.extract('KM:(\d+)').astype(float)
            
            if not df_car.empty:
                km_atual = df_car['KM'].max()
                restante = proxima_troca - km_atual
                
                # 📢 LÓGICA DO ALERTA VISUAL
                if restante <= 0:
                    st.markdown(f'<div class="alerta-oleo" style="background-color: #ff4b4b; color: white; border-color: #8b0000;">⚠️ URGENTE: Troca de óleo vencida há {abs(restante):.0f} KM!</div>', unsafe_allow_html=True)
                elif restante <= 500:
                    st.markdown(f'<div class="alerta-oleo" style="background-color: #ffeb3b; color: #856404; border-color: #fbc02d;">🔔 ATENÇÃO: Trocar óleo em {restante:.0f} KM.</div>', unsafe_allow_html=True)
                else:
                    st.success(f"✅ Tudo em ordem! Faltam {restante:.0f} KM para a próxima troca de óleo.")

                # Gráfico de Consumo (se houver mais de 1 registro)
                df_car['L'] = df_car['Descrição'].str.extract('L:([\d.]+)').astype(float)
                if len(df_car) > 1:
                    df_car = df_car.sort_values('Data')
                    df_car['Consumo'] = df_car['KM'].diff() / df_car['L']
                    fig_v = go.Figure(go.Scatter(x=df_car['Data'], y=df_car['Consumo'], mode='lines+markers', name='km/l', line=dict(color='#007bff')))
                    fig_v.update_layout(title="Histórico de Consumo (km/l)")
                    st.plotly_chart(fig_v, use_container_width=True)
            else:
                st.info("Faça seu primeiro registro de KM para ativar os alertas.")

        # ... (Logica de Finanças e Pets mantida conforme o código anterior)
except Exception as e:
    st.error(f"Erro: {e}")
