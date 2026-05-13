import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

# 1. CONFIGURAÇÕES INICIAIS E FUSO
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()
mes_atual = agora_br.strftime('%m/%y')

st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# Estilo para os cards de saldo
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1.1rem !important; font-weight: bold !important; }
    [data-testid='stMetricValue'] { font-size: 1.2rem !important; color: #1f77b4 !important; }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Secrets não configurados!"); st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro na conexão: {e}"); st.stop()

client = conectar()
ID_PLANILHA = "147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4"
sh = client.open_by_key(ID_PLANILHA)
ws_base = sh.get_worksheet(0)
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# 3. CARREGAMENTO DE DADOS
def carregar_dados():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 1: return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

def m_fmt(n): 
    return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados()
    st.session_state['df_bancos'] = carregar_bancos()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos']

# 4. SIDEBAR (MENU LATERAL)
st.sidebar.title("🎮 Menu Finanças")
aba = st.sidebar.radio("Navegar para:", ["💰 Saldo & Histórico", "🚗 Veículo", "🐾 Pets", "📄 WhatsApp", "📋 PDF", "⏳ Pendências"])

st.sidebar.divider()

# FORMULÁRIOS DE LANÇAMENTO (Na Sidebar para ficar limpo)
with st.sidebar.expander("➕ Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Vencimento", hoje_br, format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Dinheiro"])
        f_sta = st.selectbox("Status", ["Pendente", "Pago"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, "Outros", "Despesa", f_bnc, f_sta])
            st.success("Salvo!"); st.rerun()

# 5. LÓGICA DAS ABAS (O CORAÇÃO DO APP)
if aba == "💰 Saldo & Histórico":
    st.title("🛡️ Resumo Financeiro")
    if not df_base.empty:
        # Filtros rápidos
        col_f1, col_f2 = st.columns(2)
        filtro_status = col_f1.multiselect("Status", ["Pago", "Pendente"], default=["Pago", "Pendente"])
        filtro_banco = col_f2.multiselect("Banco", sorted(df_base['Banco'].unique()))

        df_filtro = df_base.copy()
        if filtro_status: df_filtro = df_filtro[df_filtro['Status'].isin(filtro_status)]
        if filtro_banco: df_filtro = df_filtro[df_filtro['Banco'].isin(filtro_banco)]

        # Métricas
        pagos = df_filtro[df_filtro['Status'] == 'Pago']
        receita = pagos[pagos['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesa = pagos[pagos['Tipo'] == 'Despesa']['V_Num'].sum()

        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas (Pagas)", m_fmt(receita))
        c2.metric("Despesas (Pagas)", m_fmt(despesa))
        c3.metric("Saldo Real", m_fmt(receita - despesa))

        st.divider()
        st.subheader("📋 Últimas Movimentações")
        st.dataframe(df_filtro[['Vencimento', 'Descrição', 'Valor', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum dado encontrado na planilha.")

elif aba == "🚗 Veículo":
    st.title("🚗 Gestão do Veículo")
    c1, c2 = st.columns(2)
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: st.success("⛽ ABASTEÇA COM ÁLCOOL")
        else: st.warning("⛽ ABASTEÇA COM GASOLINA")
    
    st.divider()
    st.subheader("Histórico do Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_car[['Vencimento', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🐾 Pets":
    st.title("🐾 Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    if not df_pets.empty:
        st.metric("Total Gasto com Pets", m_fmt(df_pets['V_Num'].sum()))
        st.table(df_pets[['Vencimento', 'Descrição', 'Valor']].tail(10))
    else:
        st.write("Sem registros de pets.")

elif aba == "📄 WhatsApp":
    st.title("📄 Relatório para WhatsApp")
    # Gerar o texto para copiar
    texto_zap = f"RESUMO WILSON - {mes_atual}\n"
    if not df_base.empty:
        df_mes = df_base[df_base['Mes_Ano'] == mes_atual]
        pend = df_mes[df_mes['Status'] == 'Pendente']['V_Num'].sum()
        texto_zap += f"Total Pendente no Mês: {m_fmt(pend)}"
    
    st.text_area("Texto para copiar:", texto_zap, height=150)
    st.markdown(f"[📲 Enviar via WhatsApp](https://wa.me/?text={urllib.parse.quote(texto_zap)})")

elif aba == "📋 PDF":
    st.title("📋 Gerador de Relatório PDF")
    if st.button("Gerar PDF do Mês"):
        st.write("Gerando arquivo...")
        # Lógica simples de PDF aqui

elif aba == "⏳ Pendências":
    st.title("⏳ Contas a Pagar")
    df_pend = df_base[df_base['Status'] == 'Pendente']
    if not df_pend.empty:
        st.error(f"Atenção: Você tem {m_fmt(df_pend['V_Num'].sum())} em contas pendentes.")
        st.dataframe(df_pend[['Vencimento', 'Descrição', 'Valor', 'Banco']], use_container_width=True)
    else:
        st.success("Tudo em dia! Nenhuma pendência.")
