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
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; }
    .tag-card { background-color: #ffffff; padding: 12px; border-radius: 8px; border-left: 5px solid #ccc; box-shadow: 0 2px 4px rgba(0,0,0,0.05); margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
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
        st.error(f"Erro de conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

# --- CONFIGURAÇÕES ---
META_GASTO_MENSAL = 3000.00
ESTOQUE_TOTAL_RACAO = 15.0  # Em kg (ex: um saco de 15kg)

# --- BARRA LATERAL ---
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    categorias_dict = {
        "Receita": ["Salário", "Vendas", "Extras"],
        "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Ração/Pet", "Saúde"],
        "Rendimento": ["Dividendos", "Juros"],
        "Pendência": ["Boleto", "Dívida"]
    }
    tipo = st.sidebar.selectbox("Tipo:", list(categorias_dict.keys()))
    with st.sidebar.form("form_financas", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        f_cat = st.selectbox("Categoria", categorias_dict[tipo])
        if st.form_submit_button("Salvar"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo, ""])
            st.cache_data.clear(); st.rerun()

else:
    st.sidebar.header("🐾 Alimentar Meninos")
    with st.sidebar.form("form_pet", clear_on_submit=True):
        p_data = st.date_input("Data", datetime.now())
        p_quantidade = st.number_input("Quantidade de Ração (Gramas)", min_value=0, step=50)
        p_pet = st.selectbox("Quem Comeu?", ["Milo", "Ambos"])
        if st.form_submit_button("Registrar Refeição"):
            # Salvamos como "Despesa" na categoria "Ração" com valor 0 para não afetar o financeiro se for só consumo
            ws.append_row([p_data.strftime("%d/%m/%Y"), 0, "Consumo Ração", "Pet", f"{p_pet}: {p_quantidade}g"])
            st.cache_data.clear(); st.rerun()

# --- ÁREA PRINCIPAL ---
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
            # (Lógica de Saldo e Gráficos Financeiros que já funcionava)
            val_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            val_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            saldo = val_rec - val_des
            
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {saldo:,.2f}</span></div>', unsafe_allow_html=True)
            
            # Gráfico de Metas
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            res = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            
            st.subheader("🎯 Meta de Gastos")
            fig = go.Figure()
            if 'Despesa' in res.columns:
                fig.add_trace(go.Bar(x=res['Mês/Ano'], y=res['Despesa'], name='Gasto Real', marker_color='#007bff'))
                fig.add_trace(go.Scatter(x=res['Mês/Ano'], y=[META_GASTO_MENSAL]*len(res), name='Meta', line=dict(color='#ffc107', width=3, dash='dash')))
            st.plotly_chart(fig, use_container_width=True)

        else:
            st.title("🐾 Controle de Ração - Milo & Cia")
            
            # Cálculo de Consumo (Filtramos pela categoria "Consumo Ração")
            df_pet = df_v[df_v['Categoria'] == 'Consumo Ração'].copy()
            df_pet['Gramas'] = df_pet['Descrição'].str.extract('(\d+)').astype(float).fillna(0)
            total_consumido_kg = df_pet['Gramas'].sum() / 1000
            estoque_atual = max(0, ESTOQUE_TOTAL_RACAO - total_consumido_kg)
            
            # Gráfico de Medidor (Gauge) para o Estoque
            fig_estoque = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = estoque_atual,
                title = {'text': "Estoque de Ração (KG)"},
                gauge = {
                    'axis': {'range': [0, ESTOQUE_TOTAL_RACAO]},
                    'bar': {'color': "#28a745" if estoque_atual > 3 else "#dc3545"},
                    'steps': [{'range': [0, 3], 'color': "red"}]
                }
            ))
            st.plotly_chart(fig_estoque, use_container_width=True)
            
            if estoque_atual <= 3:
                st.error(f"⚠️ Wilson, o estoque está baixo! Restam apenas {estoque_atual:.2f} kg.")

            st.subheader("📋 Últimas Refeições")
            st.table(df_pet[['Data', 'Descrição']].tail(5))

except Exception as e:
    st.error(f"Erro: {e}")
