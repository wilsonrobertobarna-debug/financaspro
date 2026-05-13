import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import urllib.parse

# --- CONFIGURAÇÃO DE TEMPO E FUSO ---
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()
mes_atual = hoje_br.strftime('%m/%y')

# --- CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# CSS para Visual Limpo
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1rem !important; font-weight: bold !important; color: #666; }
    [data-testid='stMetricValue'] { font-size: 1.3rem !important; font-weight: bold !important; color: #1E88E5; }
    .stButton>button { width: 100%; border-radius: 5px; }
    </style>
""", unsafe_allow_html=True)

# --- CONEXÃO E CACHE ---
@st.cache_resource
def conectar():
    creds_dict = st.secrets["connections"]["gsheets"]
    pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
    if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
    final_creds = {
        "type": creds_dict["type"], "project_id": creds_dict["project_id"],
        "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
        "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
    }
    return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)
ws_bancos = sh.worksheet("Bancos")

# --- FUNÇÕES DE DADOS ---
def carregar_dados():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['V_Num'] = df['Valor'].apply(lambda x: float(str(x).replace('R$', '').replace('.', '').replace(',', '.').strip()) if x else 0.0)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_info():
    dados = ws_bancos.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    return pd.DataFrame(dados[1:], columns=dados[0])

# Inicialização da Sessão
if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados()
if 'df_bancos_info' not in st.session_state:
    st.session_state['df_bancos_info'] = carregar_bancos_info()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']
bancos_disponiveis = sorted(df_bancos_info.iloc[:, 0].unique()) if not df_bancos_info.empty else []

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- SIDEBAR NAVEGAÇÃO ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Dashboard", "📅 Pendências", "🐾 Pets", "🚗 Veículo", "📄 WhatsApp"])

# --- FORMULÁRIO (MANTIDO CONFORME SEU PEDIDO) ---
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Vencimento", hoje_br)
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Outros"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pendente", "Pago"])
        if st.form_submit_button("SALVAR"):
            for i in range(f_par):
                nova_dt = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_dt.strftime("%d/%m/%Y"), f"{f_val:.2f}".replace('.', ','), f_des, f_cat, f_tip, f_bnc, f_sta, ""])
            st.session_state['df_base'] = carregar_dados()
            st.rerun()

# --- LÓGICA DAS ABAS ---

if aba == "💰 Dashboard":
    st.title("🛡️ Dashboard Financeiro")
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    
    c1, c2, c3, c4 = st.columns(4)
    receitas = df_m[(df_m['Tipo'].isin(['Receita', 'Rendimento'])) & (df_m['Status'] == 'Pago')]['V_Num'].sum()
    despesas = df_m[(df_m['Tipo'] == 'Despesa') & (df_m['Status'] == 'Pago')]['V_Num'].sum()
    c1.metric("Receitas (Mês)", m_fmt(receitas))
    c2.metric("Despesas (Mês)", m_fmt(despesas))
    c3.metric("Sobra", m_fmt(receitas - despesas))
    c4.metric("A Pagar", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()), delta_color="inverse")

    st.markdown("---")
    col_dir, col_esq = st.columns(2)
    
    with col_dir:
        fig_cat = px.pie(df_m[df_m['Tipo']=='Despesa'], values='V_Num', names='Categoria', title="Gastos por Categoria", hole=.4)
        st.plotly_chart(fig_cat, use_container_width=True)
    
    with col_esq:
        # Tabela de bancos simplificada
        st.subheader("Saldos por Instituição")
        for b in bancos_disponiveis:
            movs = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pago')]
            v_ini = float(str(df_bancos_info[df_bancos_info.iloc[:,0]==b].iloc[0,1]).replace('R$','').replace('.','').replace(',','.').strip())
            total = v_ini + movs[movs['Tipo']!='Despesa']['V_Num'].sum() - movs[movs['Tipo']=='Despesa']['V_Num'].sum()
            st.write(f"**{b}:** {m_fmt(total)}")

elif aba == "📅 Pendências":
    st.title("📅 Contas Pendentes")
    df_pend = df_base[df_base['Status'] == 'Pendente'].sort_values('DT')
    if not df_pend.empty:
        st.dataframe(df_pend[['Vencimento', 'Descrição', 'Valor', 'Banco', 'Categoria']], use_container_width=True)
    else:
        st.success("Tudo em dia!")

elif aba == "🐾 Pets":
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', na=False)]
    st.metric("Gasto Acumulado Pets", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet.sort_values('DT', ascending=False), use_container_width=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Meu Veículo")
    df_car = df_base[df_base['Categoria'] == 'Veículo']
    st.metric("Manutenção e Custos", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car.sort_values('DT', ascending=False), use_container_width=True)

elif aba == "📄 WhatsApp":
    st.title("📄 Relatório WhatsApp")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", hoje_br - timedelta(days=30))
    d_fim = c2.date_input("Fim", hoje_br)
    
    saldos_txt = ""
    total_pat = 0.0
    
    for b in sorted(bancos_disponiveis):
        row_b = df_bancos_info[df_bancos_info.iloc[:,0] == b]
        v_base = float(str(row_b.iloc[0,1]).replace('R$','').replace('.','').replace(',','.').strip())
        tipo = str(row_b.iloc[0,2]).upper()
        
        if "CART" in tipo:
            usado = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pendente') & (df_base['DT'].dt.date <= d_fim)]['V_Num'].sum()
            saldos_txt += f"💳 *{b}*: Disp: {m_fmt(v_base - usado)} (Usado: {m_fmt(usado)})\n"
        else:
            movs = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pago')]
            saldo = v_base + movs[movs['Tipo']!='Despesa']['V_Num'].sum() - movs[movs['Tipo']=='Despesa']['V_Num'].sum()
            saldos_txt += f"🏦 *{b}*: {m_fmt(saldo)}\n"
            total_pat += saldo

    # Lógica de Sobra Período
    df_p = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim) & (df_base['Status'] == 'Pago')]
    sobra = df_p[df_p['Tipo']!='Despesa']['V_Num'].sum() - df_p[df_p['Tipo']=='Despesa']['V_Num'].sum()

    relat = f"*FINANÇAS WILSON*\n📅 {d_ini.strftime('%d/%m')} a {d_fim.strftime('%d/%m')}\n\n{saldos_txt}\n💰 *Patrimônio:* {m_fmt(total_pat)}\n⚖️ *Sobra no Período:* {m_fmt(sobra)}"
    
    st.text_area("Copiável:", relat, height=300)
    st.markdown(f"[📲 Enviar para WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})")
