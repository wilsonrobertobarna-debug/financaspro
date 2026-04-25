import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO (Interface Limpa e Profissional)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    /* Tarja de Saldo Estreita */
    .saldo-container {
        background-color: #007bff;
        color: white;
        padding: 10px 20px;
        border-radius: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 25px;
    }
    /* Cartões de Tags */
    .tag-card {
        background-color: #ffffff;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #ccc;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"],
            "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"],
            "private_key": private_key,
            "client_email": creds_info["client_email"],
            "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de conexão: {e}")
        st.stop()

client = conectar_google()
PLANILHA_ID = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
sh = client.open_by_key(PLANILHA_ID)
ws = sh.get_worksheet(0)

# 3. CONFIGURAÇÕES GERAIS
META_GASTO_MENSAL = 3000.00
categorias_dict = {
    "Receita": ["Salário", "Vendas", "Investimentos", "Extras"],
    "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde", "Educação"],
    "Rendimento": ["Dividendos", "Juros", "Aplicações"],
    "Pendência": ["Boleto a Pagar", "Empréstimo", "Dívida", "Outros"]
}

# --- BARRA LATERAL: FORMULÁRIO ---
st.sidebar.header("📝 Novo Lançamento")
tipo_selecionado = st.sidebar.selectbox("Tipo de Movimentação:", list(categorias_dict.keys()))

with st.sidebar.form("form_lancamento", clear_on_submit=True):
    data_f = st.date_input("Data", datetime.now())
    valor_f = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
    cat_f = st.selectbox("Categoria", categorias_dict[tipo_selecionado])
    desc_f = st.text_input("Descrição / Detalhes")
    
    if st.form_submit_button("Salvar no FinançasPro"):
        if valor_f > 0:
            ws.append_row([data_f.strftime("%d/%m/%Y"), valor_f, cat_f, tipo_selecionado, desc_f])
            st.cache_data.clear()
            st.rerun()

# --- ÁREA PRINCIPAL ---
st.title("🛡️ FinançasPro Wilson")

try:
    dados_raw = ws.get_all_values()
    if len(dados_raw) > 1:
        df = pd.DataFrame(dados_raw[1:], columns=dados_raw[0])
        df.columns = [c.strip() for c in df.columns]

        # Conversão de Dados Blindada
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], format='%d/%m/%Y', errors='coerce')
        df['Tipo'] = df['Tipo'].astype(str).str.strip() # Remove espaços acidentais
        
        df_v = df.dropna(subset=['Data']).copy()
        df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')

        # CÁLCULOS DAS TAGS
        val_rec = df_v[df_v['Tipo'] == 'Receita']['Valor'].sum()
        val_des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
        val_ren = df_v[df_v['Tipo'] == 'Rendimento']['Valor'].sum()
        # Busca flexível para Pendência (com ou sem acento)
        val_pen = df_v[df_v['Tipo'].str.contains('Penden', case=False, na=False)]['Valor'].sum()
        
        saldo_total = (val_rec + val_ren) - val_des

        # EXIBIÇÃO 1: TARJA AZUL COMPACTA
        st.markdown(f"""
            <div class="saldo-container">
                <span style='font-weight: bold; font-size: 1rem;'>SALDO ATUAL (Disponível)</span>
                <span style='font-weight: bold; font-size: 1.6rem;'>R$ {saldo_total:,.2f}</span>
            </div>
        """, unsafe_allow_html=True)

        # EXIBIÇÃO 2: TAGS COLORIDAS
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"<div class='tag-card' style='border-left-color:#28a745;'><b>Receitas</b><br>R$ {val_rec:,.2f}</div>", unsafe_allow_html=True)
        c2.markdown(f"<div class='tag-card' style='border-left-color:#dc3545;'><b>Despesas</b><br>R$ {val_des:,.2f}</div>", unsafe_allow_html=True)
        c3.markdown(f"<div class='tag-card' style='border-left-color:#17a2b8;'><b>Rendimentos</b><br>R$ {val_ren:,.2f}</div>", unsafe_allow_html=True)
        c4.markdown(f"<div class='tag-card' style='border-left-color:#ffc107;'><b>Pendências</b><br>R$ {val_pen:,.2f}</div>", unsafe_allow_html=True)

        st.markdown("---")

        # PROCESSAMENTO DOS GRÁFICOS
        resumo_mensal = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()

        # 📊 GRÁFICO 1: COMPARATIVO MENSAL
        st.subheader("📊 Evolução Mensal: Entradas vs Saídas")
        fig1 = go.Figure()
        if 'Receita' in resumo_mensal.columns:
            fig1.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Receita'], name='Receitas', marker_color='#28a745'))
        if 'Despesa' in resumo_mensal.columns:
            fig1.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Despesa'], name='Despesas', marker_color='#dc3545'))
        if 'Rendimento' in resumo_mensal.columns:
            fig1.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Rendimento'], name='Rendimentos', marker_color='#17a2b8'))
        
        fig1.update_layout(barmode='group', height=350, margin=dict(t=20, b=20), legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig1, use_container_width=True)

        st.markdown("---")

        # 🎯 GRÁFICO 2: METAS DE GASTOS
        st.subheader("🎯 Acompanhamento de Metas (Teto de Despesas)")
        fig2 = go.Figure()
        if 'Despesa' in resumo_mensal.columns:
            fig2.add_trace(go.Bar(x=resumo_mensal['Mês/Ano'], y=resumo_mensal['Despesa'], name='Gasto Realizado', marker_color='#007bff'))
            # Linha de Meta
            fig2.add_trace(go.Scatter(
                x=resumo_mensal['Mês/Ano'], 
                y=[META_GASTO_MENSAL] * len(resumo_mensal),
                name='Sua Meta', line=dict(color='#ffc107', width=4, dash='dash')
            ))
        
        fig2.update_layout(height=350, margin=dict(t=20, b=20))
        st.plotly_chart(fig2, use_container_width=True)

        # TABELA DE HISTÓRICO
        st.markdown("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df.tail(15), use_container_width=True)
        
    else:
        st.info("👋 Wilson, seu FinançasPro está pronto! Faça o primeiro lançamento na barra lateral.")

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
