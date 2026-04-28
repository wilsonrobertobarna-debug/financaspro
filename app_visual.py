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
            "private_key": pk, "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E FUNÇÕES
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
    df['Ano_Mes_Sort'] = df['DT'].dt.strftime('%Y-%m')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (ESTRUTURA PROTEGIDA)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

st.sidebar.divider()

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "XP", "Mercado Pago"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_dt = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
            ws_base.append_row([nova_dt, v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

with st.sidebar.form("f_transf", clear_on_submit=True):
    st.write("### 💸 Transferência")
    t_val = st.number_input("Valor", min_value=0.0)
    t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
    if st.form_submit_button("EXECUTAR"):
        d_s = datetime.now().strftime("%d/%m/%Y")
        v_s = f"{t_val:.2f}".replace('.', ',')
        ws_base.append_row([d_s, v_s, f"Transf: {t_orig} > {t_dest}", "Transferência", "Despesa", t_orig, "Pago"])
        ws_base.append_row([d_s, v_s, f"Transf: {t_orig} > {t_dest}", "Transferência", "Receita", t_dest, "Pago"])
        st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
    
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3, m4 = st.columns(4)
    gasto_total_mes = df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()
    m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
    m2.metric("📉 Gasto", m_fmt(gasto_total_mes))
    m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
    m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        df_evol = df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])]
        fig_evol = px.bar(df_evol, x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Receita x Despesa Mensal")
        st.plotly_chart(fig_evol, use_container_width=True)
    with c2:
        metas = {"Mercado": 1200.0, "Aluguel": 2500.0, "Luz/Água": 400.0, "Internet": 150.0, "Pet: Milo": 500.0, "Pet: Bolt": 500.0, "Veículo": 1000.0}
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        gastos_cat['Meta'] = gastos_cat['Categoria'].map(metas).fillna(500.0)
        fig_meta = go.Figure()
        fig_meta.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['V_Num'], name='Gasto Real', marker_color='#EF553B'))
        fig_meta.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['Meta'], name='Meta', marker_color='#3B82F6', opacity=0.4))
        fig_meta.update_layout(title="Gasto x Meta por Categoria", barmode='overlay')
        st.plotly_chart(fig_meta, use_container_width=True)

    st.divider()
    st.write("### 🔍 Pesquisar Lançamentos")
    psq1, psq2, psq3 = st.columns([1, 1, 2])
    b_psq = psq1.selectbox("Banco:", ["Todos"] + sorted(df_base['Banco'].unique().tolist()))
    t_psq = psq2.selectbox("Tipo:", ["Todos", "Receita", "Despesa", "Rendimento"])
    d_psq = psq3.text_input("Descrição:")
    
    df_f = df_base.copy()
    if b_psq != "Todos": df_f = df_f[df_f['Banco'] == b_psq]
    if t_psq != "Todos": df_f = df_f[df_f['Tipo'] == t_psq]
    if d_psq: df_f = df_f[df_f['Descrição'].str.contains(d_psq, case=False, na=False)]
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Categoria']].iloc[::-1], use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)].copy()
    st.metric("Total Gasto com Pets", m_fmt(df_pets['V_Num'].sum()))
    fig_p = px.bar(df_pets, x='Mes_Ano', y='V_Num', color='Categoria', title="Gastos Mensais por Pet")
    st.plotly_chart(fig_p, use_container_width=True)
    st.table(df_pets[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    st.write("### ⛽ Álcool x Gasolina")
    v1, v2 = st.columns(2)
    alc = v1.number_input("Álcool", min_value=0.0)
    gas = v2.number_input("Gasolina", min_value=0.0)
    if alc > 0 and gas > 0:
        if alc/gas <= 0.7: st.success("Vá de ÁLCOOL!")
        else: st.warning("Vá de GASOLINA!")
    st.divider()
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])].copy()
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Detalhado")
    b_sel = st.selectbox("Selecione o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    st.table(df_b[['Data', 'Descrição', 'Valor', 'Saldo']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Gerador de Relatórios")
    r1, r2 = st.columns(2)
    ini = r1.date_input("Início", datetime.now().replace(day=1))
    fim = r2.date_input("Fim", datetime.now())
    df_r = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    
    txt = f"*Relatório Wilson*\nREC: {m_fmt(df_r[df_r['Tipo']=='Receita']['V_Num'].sum())}\nDES: {m_fmt(-df_r[df_r['Tipo']=='Despesa']['V_Num'].sum())}"
    st.text_area("WhatsApp:", txt, height=200)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(txt)}" target="_blank">📲 ENVIAR</a>', unsafe_allow_html=True)
