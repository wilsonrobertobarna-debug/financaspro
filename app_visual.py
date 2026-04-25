import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO (Interface Blindada)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff;
        color: white;
        padding: 8px 15px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 20px;
    }
    .tag-card {
        background-color: #ffffff;
        padding: 10px;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
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

# CONFIGURAÇÕES TÉCNICAS
META_GASTO_CATEGORIA = 500.00  # Meta sugerida por categoria
ESTOQUE_TOTAL_RACAO = 15.0     # Capacidade do saco de ração em KG

# --- BARRA LATERAL: MENU DE NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    categorias_dict = {
        "Receita": ["Salário", "Vendas", "Extras"],
        "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Ração/Pet", "Saúde"],
        "Rendimento": ["Dividendos", "Juros", "Aplicações"],
        "Pendência": ["Boleto a Pagar", "Empréstimo", "Dívida"]
    }
    tipo = st.sidebar.selectbox("Tipo:", list(categorias_dict.keys()))
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
        f_cat = st.selectbox("Categoria", categorias_dict[tipo])
        f_desc = st.text_input("Descrição")
        if st.form_submit_button("Salvar no FinançasPro"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo, f_desc])
            st.cache_data.clear(); st.rerun()

elif aba == "🐾 Controle dos Meninos":
    st.sidebar.header("🐾 Alimentar Meninos")
    with st.sidebar.form("form_p", clear_on_submit=True):
        p_data = st.date_input("Data", datetime.now())
        p_gramas = st.number_input("Quantidade (Gramas)", min_value=0, step=100)
        p_pet = st.selectbox("Quem comeu?", ["Milo", "Ambos"])
        if st.form_submit_button("Registrar Refeição"):
            ws.append_row([p_data.strftime("%d/%m/%Y"), 0, "Consumo Ração", "Pet", f"{p_pet}: {p_gramas}g"])
            st.cache_data.clear(); st.rerun()

else:
    st.sidebar.header("⛽ Abastecimento")
    with st.sidebar.form("form_v", clear_on_submit=True):
        v_data = st.date_input("Data", datetime.now())
        v_km = st.number_input("KM Atual", min_value=0)
        v_litros = st.number_input("Litros", min_value=0.0)
        v_preco = st.number_input("Total R$", min_value=0.0)
        if st.form_submit_button("Registrar Veículo"):
            ws.append_row([v_data.strftime("%d/%m/%Y"), v_preco, "Combustível", "Veículo", f"KM:{v_km}|L:{v_litros}"])
            st.cache_data.clear(); st.rerun()

# --- ÁREA PRINCIPAL ---
try:
    dados_raw = ws.get_all_values()
    if len(dados_raw) > 1:
        df = pd.DataFrame(dados_raw[1:], columns=dados_raw[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Tipo'] = df['Tipo'].astype(str).str.strip()
        df_v = df.dropna(subset=['Data']).copy()
        df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            
            # CÁLCULOS DAS TAGS
            rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            ren = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            pen = df_v[df_v['Tipo'].str.contains('Penden', case=False, na=False)]['Valor'].sum()
            saldo = (rec + ren) - des

            # 1. TARJA DE SALDO
            st.markdown(f'<div class="saldo-container"><span style="font-weight:bold">SALDO ATUAL</span><span style="font-weight:bold; font-size:1.5rem">R$ {saldo:,.2f}</span></div>', unsafe_allow_html=True)
            
            # 2. TAGS (Receita, Despesa, Rendimento, Pendência)
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {rec:,.2f}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {des:,.2f}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='tag-card' style='border-left-color:#17a2b8;'><b>Rendimentos</b><br>R$ {ren:,.2f}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='tag-card' style='border-left-color:#ffc107;'><b>Pendências</b><br>R$ {pen:,.2f}</div>", unsafe_allow_html=True)

            # 3. GRÁFICO MENSAL (RECEITA VS DESPESA)
            st.subheader("📊 Evolução Mensal (Entradas vs Saídas)")
            res_mensal = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_mensal.columns:
                fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in res_mensal.columns:
                fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Despesa'], name='Despesa', marker_color='#dc3545'))
            fig1.update_layout(barmode='group', height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig1, use_container_width=True)

            # 4. GRÁFICO DE METAS (POR CATEGORIA)
            st.subheader("🎯 Metas por Categoria (Mês Atual)")
            mes_atual = datetime.now().strftime('%m/%Y')
            df_mes = df_v[(df_v['Mês/Ano'] == mes_atual) & (df_v['Tipo'] == 'Despesa')]
            res_cat = df_mes.groupby('Categoria')['Valor'].sum().reset_index()
            
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], name='Gasto Real', marker_color='#007bff'))
            fig2.add_trace(go.Scatter(x=res_cat['Categoria'], y=[META_GASTO_CATEGORIA]*len(res_cat), name='Limite', line=dict(color='#ffc107', width=3, dash='dash')))
            fig2.update_layout(height=300, margin=dict(t=20, b=20))
            st.plotly_chart(fig2, use_container_width=True)

            st.dataframe(df.tail(10), use_container_width=True)

        elif aba == "🐾 Controle dos Meninos":
            st.title("🐾 Controle de Ração - Milo & Cia")
            df_pet = df_v[df_v['Categoria'] == 'Consumo Ração'].copy()
            df_pet['G'] = df_pet['Descrição'].str.extract('(\d+)').astype(float).fillna(0)
            estoque = max(0, ESTOQUE_TOTAL_RACAO - (df_pet['G'].sum() / 1000))
            
            fig_p = go.Figure(go.Indicator(mode="gauge+number", value=estoque, title={'text': "Estoque (KG)"},
                gauge={'axis': {'range': [0, 15]}, 'bar': {'color': "green" if estoque > 3 else "red"}}))
            st.plotly_chart(fig_p, use_container_width=True)
            st.table(df_pet[['Data', 'Descrição']].tail(5))

        else:
            st.title("🚗 Performance do Veículo")
            df_car = df_v[df_v['Categoria'] == 'Combustível'].copy()
            df_car['KM'] = df_car['Descrição'].str.extract('KM:(\d+)').astype(float)
            df_car['L'] = df_car['Descrição'].str.extract('L:([\d.]+)').astype(float)
            if len(df_car) > 1:
                df_car = df_car.sort_values('Data')
                df_car['Consumo'] = df_car['KM'].diff() / df_car['L']
                st.metric("Última Média", f"{df_car['Consumo'].iloc[-1]:.2f} km/l")
                fig_v = go.Figure(go.Scatter(x=df_car['Data'], y=df_car['Consumo'], mode='lines+markers', name='km/l'))
                st.plotly_chart(fig_v, use_container_width=True)

    else:
        st.info("Aguardando lançamentos...")
except Exception as e:
    st.error(f"Erro: {e}")
