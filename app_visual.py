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
META_GASTO_CATEGORIA = 500.00
ESTOQUE_TOTAL_RACAO = 15.0 

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    categorias_dict = {
        "Receita": ["Salário", "Vendas", "Extras"],
        "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"],
        "Rendimento": ["Dividendos", "Juros"],
        "Pendência": ["Boleto", "Dívida"]
    }
    tipo = st.sidebar.selectbox("Tipo:", list(categorias_dict.keys()))
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0)
        f_cat = st.selectbox("Categoria", categorias_dict[tipo])
        f_desc = st.text_input("Descrição")
        if st.form_submit_button("Salvar Finanças"):
            ws.append_row([f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo, f_desc])
            st.cache_data.clear(); st.rerun()

elif aba == "🐾 Controle dos Meninos":
    st.sidebar.header("🐾 Alimentar Meninos")
    with st.sidebar.form("form_p", clear_on_submit=True):
        p_data = st.date_input("Data", datetime.now())
        p_gramas = st.number_input("Gramas", min_value=0, step=100)
        if st.form_submit_button("Registrar Ração"):
            ws.append_row([p_data.strftime("%d/%m/%Y"), 0, "Consumo Ração", "Pet", f"Comeram: {p_gramas}g"])
            st.cache_data.clear(); st.rerun()

else:
    st.sidebar.header("🚗 Configurações Veículo")
    proxima_troca = st.sidebar.number_input("KM Próxima Troca de Óleo", value=50000)
    with st.sidebar.form("form_v", clear_on_submit=True):
        v_data = st.date_input("Data", datetime.now())
        v_km = st.number_input("KM Atual", min_value=0)
        v_litros = st.number_input("Litros", min_value=0.0)
        v_preco = st.number_input("Total R$", min_value=0.0)
        if st.form_submit_button("Registrar Veículo"):
            ws.append_row([v_data.strftime("%d/%m/%Y"), v_preco, "Combustível", "Veículo", f"KM:{v_km}|L:{v_litros}"])
            st.cache_data.clear(); st.rerun()

# --- PROCESSAMENTO ---
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
            
            rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            ren = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
            pen = df_v[df_v['Tipo'].str.contains('Penden', case=False, na=False)]['Valor'].sum()
            saldo = (rec + ren) - des
            
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {saldo:,.2f}</span></div>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {rec:,.2f}</div>", unsafe_allow_html=True)
            c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {des:,.2f}</div>", unsafe_allow_html=True)
            c3.markdown(f"<div class='tag-card' style='border-left-color:#17a2b8;'><b>Rendimentos</b><br>R$ {ren:,.2f}</div>", unsafe_allow_html=True)
            c4.markdown(f"<div class='tag-card' style='border-left-color:#ffc107;'><b>Pendências</b><br>R$ {pen:,.2f}</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.subheader("📊 Comparativo Mensal")
            res_mensal = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Despesa'], name='Despesa', marker_color='#dc3545'))
            st.plotly_chart(fig1, use_container_width=True)

            st.subheader("🎯 Metas por Categoria")
            res_cat = df_v[df_v['Tipo'] == 'Despesa'].groupby('Categoria')['Valor'].sum().reset_index()
            fig2 = go.Figure()
            fig2.add_trace(go.Bar(x=res_cat['Categoria'], y=res_cat['Valor'], marker_color='#007bff'))
            fig2.add_trace(go.Scatter(x=res_cat['Categoria'], y=[META_GASTO_CATEGORIA]*len(res_cat), name='Limite', line=dict(color='#ffc107', dash='dash')))
            st.plotly_chart(fig2, use_container_width=True)

            # --- TABELA DE LANÇAMENTOS (AQUI ESTÁ A CORREÇÃO) ---
            st.markdown("---")
            st.subheader("📋 Últimos Lançamentos")
            # Mostra apenas as colunas principais e os 15 mais recentes
            st.dataframe(df[['Data', 'Valor', 'Categoria', 'Tipo', 'Descrição']].tail(15), use_container_width=True)

        elif aba == "🐾 Controle dos Meninos":
            st.title("🐾 Gestão de Ração - Milo & Cia")
            df_pet = df_v[df_v['Categoria'] == 'Consumo Ração'].copy()
            df_pet['G'] = df_pet['Descrição'].str.extract('(\d+)').astype(float).fillna(0)
            estoque = max(0, ESTOQUE_TOTAL_RACAO - (df_pet['G'].sum() / 1000))
            fig_p = go.Figure(go.Indicator(mode="gauge+number", value=estoque, title={'text': "Estoque (KG)"}, gauge={'axis': {'range': [0, 15]}, 'bar': {'color': "green"}}))
            st.plotly_chart(fig_p, use_container_width=True)
            st.table(df_pet[['Data', 'Descrição']].tail(10))

        else:
            st.title("🚗 Performance do Veículo")
            df_car = df_v[df_v['Categoria'] == 'Combustível'].copy()
            df_car['KM'] = df_car['Descrição'].str.extract('KM:(\d+)').astype(float)
            if not df_car.empty:
                km_atual = df_car['KM'].max()
                restante = proxima_troca - km_atual
                st.info(f"KM Atual: {km_atual} | Próxima Troca em: {restante:.0f} KM")
                st.dataframe(df_car[['Data', 'Valor', 'Descrição']].tail(10), use_container_width=True)

except Exception as e:
    st.error(f"Erro: {e}")
