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
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
# Verifique se este ID continua o mesmo na sua planilha
ID_PLANILHA = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
sh = client.open_by_key(ID_PLANILHA)
ws = sh.get_worksheet(0)

# --- BARRA LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegar para:", ["💰 Finanças", "🐾 Controle dos Meninos", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.sidebar.header("📝 Novo Lançamento")
    tipo_selecionado = st.sidebar.selectbox("Tipo (Classificação):", ["Receita", "Despesa", "Rendimento", "Pendência"])
    categorias_dict = {
        "Receita": ["Salário", "Vendas", "Extras"],
        "Despesa": ["Alimentação", "Moradia", "Transporte", "Lazer", "Saúde"],
        "Rendimento": ["Dividendos", "Juros"],
        "Pendência": ["Boleto", "Dívida"]
    }
    
    with st.sidebar.form("form_f", clear_on_submit=True):
        f_data = st.date_input("Data", datetime.now())
        f_valor = st.number_input("Valor (R$)", min_value=0.0, format="%.2f")
        f_cat = st.selectbox("Categoria", categorias_dict.get(tipo_selecionado, ["Geral"]))
        f_status = st.text_input("Status (Pago ou Pendente)", value="Pago") 
        
        if st.form_submit_button("🚀 SALVAR AGORA"):
            try:
                # Tentativa de escrita direta no Google Sheets
                nova_linha = [f_data.strftime("%d/%m/%Y"), f_valor, f_cat, tipo_selecionado, f_status]
                ws.append_row(nova_linha)
                st.sidebar.success("✅ Registrado com sucesso!")
                # Limpa o cache para forçar a leitura dos novos dados
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.sidebar.error(f"❌ Erro ao salvar: {e}")

# --- PROCESSAMENTO E EXIBIÇÃO ---
try:
    # Busca dados atualizados
    dados_raw = ws.get_all_values()
    if len(dados_raw) > 1:
        df = pd.DataFrame(dados_raw[1:], columns=dados_raw[0])
        df.columns = [c.strip() for c in df.columns]
        df['Valor'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df_v = df.dropna(subset=['Data']).copy()

        if aba == "💰 Finanças":
            st.title("🛡️ FinançasPro Wilson")
            
            # Cálculos Rápidos
            rec = df_v[df_v['Tipo'].isin(['Receita', 'Rendimento'])]['Valor'].sum()
            des = df_v[df_v['Tipo'] == 'Despesa']['Valor'].sum()
            st.markdown(f'<div class="saldo-container"><span>SALDO ATUAL</span><span>R$ {rec - des:,.2f}</span></div>', unsafe_allow_html=True)

            # TABELA DE HISTÓRICO
            st.subheader("📋 Últimos Lançamentos (Atualizado)")
            df_display = df_v.copy()
            df_display['Data'] = df_display['Data'].dt.strftime('%d/%m/%Y')
            
            # Mostramos as últimas 20 linhas para garantir que você veja o que acabou de entrar
            df_final = df_display[['Data', 'Valor', 'Categoria', 'Tipo', 'Descrição']].tail(20)
            df_final.columns = ['Data', 'Valor', 'Categoria', 'Tipo', 'Status']
            st.dataframe(df_final.iloc[::-1], use_container_width=True) # O mais novo em cima

            # GRÁFICO MENSAL
            st.markdown("---")
            st.subheader("📊 Comparativo Mensal")
            df_v['Mês/Ano'] = df_v['Data'].dt.strftime('%m/%Y')
            res_mensal = df_v.groupby(['Mês/Ano', 'Tipo'])['Valor'].sum().unstack(fill_value=0).reset_index()
            fig1 = go.Figure()
            if 'Receita' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in res_mensal.columns: fig1.add_trace(go.Bar(x=res_mensal['Mês/Ano'], y=res_mensal['Despesa'], name='Despesa', marker_color='#dc3545'))
            st.plotly_chart(fig1, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados da planilha: {e}")
