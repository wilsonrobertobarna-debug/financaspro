import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets!"); st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Real'] = range(2, len(df) + 2) # ID interno para edição
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df.sort_values('DT', ascending=False)

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): 
    return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO E LANÇAMENTOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

st.sidebar.divider()
st.sidebar.link_button("💬 Abrir WhatsApp Web", "https://web.whatsapp.com")

# FORMULÁRIO DE LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    
    # Métricas de Topo
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3 = st.columns(3)
    m1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()))
    m2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
    m3.metric("⏳ Pendentes", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

    st.divider()
    
    # Tabela com visual limpo
    st.subheader("🔍 Últimos Lançamentos")
    c1, c2 = st.columns(2)
    b_bnc = c1.multiselect("Banco:", sorted(df_base['Banco'].unique()))
    b_desc = c2.text_input("Buscar por descrição:")
    
    df_v = df_base.copy()
    if b_bnc: df_v = df_v[df_v['Banco'].isin(b_bnc)]
    if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
    
    st.dataframe(
        df_v, 
        column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"),
        use_container_width=True, 
        hide_index=True
    )

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Total Gasto (Milo & Bolt)", m_fmt(df_pet['V_Num'].sum()))
        st.dataframe(df_pet, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro para os pets.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.metric("Total Gasto (Veículo)", m_fmt(df_car['V_Num'].sum()))
        st.dataframe(df_car, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro para o veículo.")

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = c2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
    
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    if not df_per.empty:
        sobra = df_per[df_per['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        st.success(f"### Sobra no Período: {m_fmt(sobra)}")
        
        relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\nSOBRA: {m_fmt(sobra)}"
        zap_link = f"https://wa.me/?text={urllib.parse.quote(relat)}"
        st.link_button("📲 Enviar para WhatsApp", zap_link)

# 6. EDIÇÃO NA SIDEBAR
st.sidebar.divider()
if not df_base.empty:
    with st.sidebar.expander("⚙️ Editar/Excluir"):
        escolha = st.selectbox("Selecione o item:", [""] + [f"{r['Data']} - {r['Descrição']}" for _, r in df_base.head(20).iterrows()])
        if escolha:
            st.warning("Função de edição pronta para ser configurada.")
