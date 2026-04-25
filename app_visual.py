import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")
st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
    .tag-card { background-color: #ffffff; padding: 12px; border-radius: 8px; border-left: 5px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
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

# CONFIGURAÇÕES
META_GASTO_MENSAL = 3000.00
ESTOQUE_TOTAL_RACAO = 15.0 

# --- BARRA LATERAL: MENU DE NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel de Controle")
aba = st.sidebar.selectbox("Escolha o Módulo:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    categorias_dict = {"Receita": ["Salário", "Vendas", "Extras"], "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"], "Rendimento": ["Investimentos"], "Pendência": ["Boleto"]}
    tipo = st.sidebar.selectbox("Tipo:", list(categorias_dict.keys()))
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0)
        f_cat = st.selectbox("Categoria", categorias_dict[tipo])
        if st.form_submit_button("Salvar"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo, ""])
            st.cache_data.clear(); st.rerun()

elif aba == "🐾 Controle dos Meninos":
    st.sidebar.header("🐾 Alimentar Meninos")
    with st.sidebar.form("form_p", clear_on_submit=True):
        p_data = st.date_input("Data", datetime.now())
        p_gramas = st.number_input("Gramas de Ração", min_value=0, step=100)
        if st.form_submit_button("Registrar Ração"):
            ws.append_row([p_data.strftime("%d/%m/%Y"), 0, "Consumo Ração", "Pet", f"Comeram: {p_gramas}g"])
            st.cache_data.clear(); st.rerun()

else:
    st.sidebar.header("⛽ Abastecimento / Manutenção")
    with st.sidebar.form("form_v", clear_on_submit=True):
        v_data = st.date_input("Data", datetime.now())
        v_km = st.number_input("Quilometragem Atual (KM)", min_value=0)
        v_litros = st.number_input("Litros abastecidos", min_value=0.0)
        v_preco = st.number_input("Valor Total (R$)", min_value=0.0)
        if st.form_submit_button("Registrar Posto"):
            ws.append_row([v_data.strftime("%d/%m/%Y"), v_preco, "Combustível", "Veículo", f"KM:{v_km} | L:{v_litros}"])
            st.cache_data.clear(); st.rerun()

# --- PROCESSAMENTO ---
try:
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            saldo = rec - des
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {saldo:,.2f}</span></div>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {rec:,.2f}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {des:,.2f}</div>", unsafe_allow_html=True)
            
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            res = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            
            st.subheader("📊 Gráficos Financeiros")
            fig = go.Figure()
            if 'Despesa' in res.columns:
                fig.add_trace(go.Bar(x=res['Mês/Ano'], y=res['Despesa'], name='Gasto', marker_color='#007bff'))
                fig.add_trace(go.Scatter(x=res['Mês/Ano'], y=[META_GASTO_MENSAL]*len(res), name='Meta', line=dict(color='#ffc107', dash='dash')))
            st.plotly_chart(fig, use_container_width=True)

        elif aba == "🐾 Controle dos Meninos":
            st.title("🐾 Gestão de Ração")
            df_pet = df_v[df_v['Categoria'] == 'Consumo Ração'].copy()
            df_pet['G'] = df_pet['Descrição'].str.extract('(\d+)').astype(float).fillna(0)
            estoque = max(0, ESTOQUE_TOTAL_RACAO - (df_pet['G'].sum() / 1000))
            st.plotly_chart(go.Figure(go.Indicator(mode="gauge+number", value=estoque, title={'text': "Estoque (KG)"}, gauge={'axis': {'range': [0, 15]}, 'bar':{'color': "green"}})), use_container_width=True)

        else:
            st.title("🚗 Performance do Veículo")
            df_car = df_v[df_v['Categoria'] == 'Combustível'].copy()
            # Extrair KM e Litros da descrição
            df_car['KM'] = df_car['Descrição'].str.extract('KM:(\d+)').astype(float)
            df_car['L'] = df_car['Descrição'].str.extract('L:([\d.]+)').astype(float)
            
            if len(df_car) > 1:
                df_car = df_car.sort_values('Data')
                df_car['KM_Percorrido'] = df_car['KM'].diff()
                df_car['Consumo'] = df_car['KM_Percorrido'] / df_car['L']
                
                ultima_media = df_car['Consumo'].iloc[-1]
                st.metric("Média Último Abastecimento", f"{ultima_media:.2f} km/l")
                
                fig_v = go.Figure(go.Scatter(x=df_car['Data'], y=df_car['Consumo'], mode='lines+markers', name='Consumo (km/l)'))
                fig_v.update_layout(title="Histórico de Eficiência (km/l)", yaxis_title="km/l")
                st.plotly_chart(fig_v, use_container_width=True)
            else:
                st.info("Abasteça pelo menos 2 vezes para calcular a média de consumo!")

except Exception as e:
    st.error(f"Erro: {e}")
