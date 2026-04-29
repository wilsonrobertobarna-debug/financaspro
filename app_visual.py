import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

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
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# BUSCA DE BANCOS (Tenta na aba BANCOS, se não der, usa os lançamentos)
try:
    ws_bancos = sh.worksheet("BANCOS")
    dados_b = ws_bancos.get_all_values()
    bancos_oficiais = [linha[0] for linha in dados_b[1:] if linha[0]]
except:
    bancos_oficiais = []

# 3. CARREGAMENTO DOS DADOS
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# LISTA DINÂMICA
if bancos_oficiais:
    lista_bancos_dinamica = sorted(list(set(bancos_oficiais)))
elif not df_base.empty:
    lista_bancos_dinamica = sorted(df_base['Banco'].unique().tolist())
else:
    lista_bancos_dinamica = ["Dinheiro", "Pix"]

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO E BARRINHAS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📋 Relatório PDF"])
st.sidebar.divider()

# --- BARRINHAS DE AÇÃO ---
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco/Cartão", lista_bancos_dinamica)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("💸 Transferência"):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now())
        t_val = st.number_input("Valor", min_value=0.0)
        t_orig = st.selectbox("Sai de:", lista_bancos_dinamica)
        t_dest = st.selectbox("Entra em:", lista_bancos_dinamica)
        if st.form_submit_button("TRANSFERIR"):
            v_str = f"{t_val:.2f}".replace('.', ',')
            d_str = t_dat.strftime("%d/%m/%Y")
            ws_base.append_row([d_str, v_str, "Transferência Saída", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([d_str, v_str, "Transferência Entrada", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("⚙️ Ajustar Lançamento"):
    if not df_base.empty:
        opcoes = {f"{r['Data']} - {r['Descrição']} (R$ {r['Valor']})": r for _, r in df_base.tail(20).iterrows()}
        edit = st.selectbox("Selecione:", [""] + list(opcoes.keys()))
        if edit:
            item = opcoes[edit]
            ed_sta = st.selectbox("Mudar Status:", ["Pago", "Pendente"], index=0 if item['Status']=="Pago" else 1)
            if st.button("ATUALIZAR STATUS"):
                ws_base.update_cell(int(item['ID']), 7, ed_sta)
                st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo = df_base[df_base['Tipo'].isin(['Receita','Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo']=='Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(saldo)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        c1, c2, c3 = st.columns(3)
        c1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo']=='Receita']['V_Num'].sum()))
        c2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo']=='Despesa']['V_Num'].sum()))
        c3.metric("⏳ Pendentes", m_fmt(df_m[df_m['Status']=='Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo']=='Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria"), use_container_width=True)
        with g2:
            df_f = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo do Mês"), use_container_width=True)
        
        st.subheader("🔍 Últimos Lançamentos")
        st.dataframe(df_base[['Data','Descrição','Categoria','Valor','Banco','Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.dataframe(df_pet.iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car.iloc[::-1], use_container_width=True)

elif "📄" in aba:
    st.title("📄 Relatório Wilson")
    # Lógica de relatório corrigida para WhatsApp
    r_v = df_base[df_base['Tipo'] == 'Receita']['V_Num'].sum()
    d_v = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
    relat = f"RELATÓRIO WILSON\nRESUMO GERAL\nREC: {m_fmt(r_v)}\nDES: {m_fmt(d_v)}\nSOBRA: {m_fmt(r_v-d_v)}"
    st.text_area("Texto para copiar:", relat, height=200)
    zap_link = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f'[📲 Enviar WhatsApp]({zap_link})')
