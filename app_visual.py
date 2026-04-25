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
        f_desc = st.text_input("Descrição")
        if st.form_submit_button("Salvar"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo, f_desc])
            st.cache_data.clear(); st.rerun()
else:
    st.sidebar.header("🐾 Alimentar Meninos")
    with st.sidebar.form("form_pet", clear_on_submit=True):
        p_data = st.date_input("Data", datetime.now())
        p_quantidade = st.number_input("Quantidade (Gramas)", min_value=0, step=50)
        p_pet = st.selectbox("Quem?", ["Milo", "Ambos"])
        if st.form_submit_button("Registrar Refeição"):
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
        df['Tipo'] = df['Tipo'].astype(str).str.strip()
        df_v = df.dropna(subset=['Data']).copy()
        df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            
            # CÁLCULOS
            rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            ren = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            pen = df_v[df_v['Tipo'].str.contains('Penden', case=False, na=False)]['Valor'].sum()
            saldo = (rec + ren) - des

            # 1. TARJA DE SALDO
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {saldo:,.2f}</span></div>', unsafe_allow_html=True)
            
            # 2. TAGS COLORIDAS
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {rec:,.2f}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {des:,.2f}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='tag-card' style='border-left-color:#17a2b8;'><b>Rendimentos</b><br>R$ {ren:,.2f}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='tag-card' style='border-left-color:#ffc107;'><b>Pendências</b><br>R$ {pen:,.2f}</div>", unsafe_allow_html=True)

            st.markdown("---")
            resumo = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()

            # 3. GRÁFICO COMPARATIVO
            st.subheader("📊 Comparativo Mensal")
            fig1 = go.Figure()
            for t, cor in zip(["Receita", "Despesa", "Rendimento"], ["#28a745", "#dc3545", "#17a2b8"]):
                if t in resumo.columns:
                    fig1.add_trace(go.Bar(x=resumo['Mês/Ano'], y=resumo[t], name=t, marker_color=cor))
            fig1.update_layout(barmode='group', height=300)
            st.plotly_chart(fig1, use_container_width=True)

            # 4. GRÁFICO DE METAS
            st.subheader("🎯 Meta de Gastos")
            fig2 = go.Figure()
            if 'Despesa' in resumo.columns:
                fig2.add_trace(go.Bar(x=resumo['Mês/Ano'], y=resumo['Despesa'], name='Gasto Real', marker_color='#007bff'))
                fig2.add_trace(go.Scatter(x=resumo['Mês/Ano'], y=[META_GASTO_MENSAL]*len(resumo), name='Meta', line=dict(color='#ffc107', width=3, dash='dash')))
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

            st.markdown("---")
            st.subheader("📋 Últimos Lançamentos")
            st.dataframe(df.tail(10), use_container_width=True)

        else:
            # TELA DOS MENINOS (Módulo Pet)
            st.title("🐾 Controle de Ração")
            df_pet = df_v[df_v['Categoria'] == 'Consumo Ração'].copy()
            df_pet['Gramas'] = df_pet['Descrição'].str.extract('(\d+)').astype(float).fillna(0)
            consumo_kg = df_pet['Gramas'].sum() / 1000
            estoque = max(0, ESTOQUE_TOTAL_RACAO - consumo_kg)
            
            fig_p = go.Figure(go.Indicator(mode="gauge+number", value=estoque, title={'text': "Estoque (KG)"},
                gauge={'axis': {'range': [0, ESTOQUE_TOTAL_RACAO]}, 'bar': {'color': "green" if estoque > 3 else "red"}}))
            st.plotly_chart(fig_p, use_container_width=True)
            
            st.subheader("📋 Histórico de Refeições")
            st.table(df_pet[['Data', 'Descrição']].tail(5))

except Exception as e:
    st.error(f"Erro ao carregar: {e}")
