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
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - FORMULÁRIOS COMPLETOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

# NOVO LANÇAMENTO
with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# TRANSFERÊNCIA (RESTAURADA)
with st.sidebar.form("f_transf", clear_on_submit=True):
    st.write("### 💸 Transferência")
    t_dat = st.date_input("Data", datetime.now())
    t_val = st.number_input("Valor Transf.", min_value=0.0, step=0.01)
    t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
    t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
    if st.form_submit_button("EXECUTAR TRANSFERÊNCIA"):
        if t_orig != t_dest:
            v_s = f"{t_val:.2f}".replace('.', ',')
            d_s = t_dat.strftime("%d/%m/%Y")
            ws_base.append_row([d_s, v_s, "Transferência Saída", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([d_s, v_s, "Transferência Entrada", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Patrimônio Total (Soma de tudo)
        patrimonio = df_base['V_Real'].sum()
        st.info(f"### 🏦 PATRIMÔNIO TOTAL CONSOLIDADO: {m_fmt(patrimonio)}")

        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        # Gráfico de Barras Receita x Despesa (RESTAURADO)
        df_fluxo = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', title="Resumo Mensal: Receita vs Despesa"), use_container_width=True)

        st.divider()
        st.subheader("🔍 Pesquisa de Lançamentos")
        c1, c2, c3 = st.columns(3)
        p_bnc = c1.multiselect("Filtrar Banco:", sorted(df_base['Banco'].unique()))
        p_tip = c2.multiselect("Filtrar Tipo:", ["Receita", "Despesa", "Rendimento"])
        p_des = c3.text_input("Buscar Beneficiário/Descrição:")
        
        df_v = df_base.copy()
        if p_bnc: df_v = df_v[df_v['Banco'].isin(p_bnc)]
        if p_tip: df_v = df_v[df_v['Tipo'].isin(p_tip)]
        if p_des: df_v = df_v[df_v['Descrição'].str.contains(p_des, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato por Banco com Saldo Progressivo")
    c1, c2, c3 = st.columns(3)
    b_sel = c1.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    d_ini = c2.date_input("De:", datetime.now() - relativedelta(months=1))
    d_fim = c3.date_input("Até:", datetime.now())
    
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    
    mask = (df_b['DT'].dt.date >= d_ini) & (df_b['DT'].dt.date <= d_fim)
    df_res = df_b.loc[mask].copy()

    if not df_res.empty:
        df_res['Saldo Diário'] = ""
        last_idx = df_res.groupby('DT').tail(1).index
        df_res.loc[last_idx, 'Saldo Diário'] = df_res.loc[last_idx, 'Saldo_Acum'].apply(m_fmt)
        st.table(df_res[['Data', 'Descrição', 'Tipo', 'Valor', 'Saldo Diário']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    # Cálculo Álcool x Gasolina (RESTAURADO)
    st.subheader("⛽ Calculadora de Combustível")
    col1, col2 = st.columns(2)
    p_alc = col1.number_input("Preço Álcool", min_value=0.0, step=0.01)
    p_gas = col2.number_input("Preço Gasolina", min_value=0.0, step=0.01)
    if p_alc > 0 and p_gas > 0:
        ratio = p_alc / p_gas
        if ratio <= 0.7: st.success(f"Razão: {ratio:.2f}. **ABASTEÇA COM ÁLCOOL!**")
        else: st.warning(f"Razão: {ratio:.2f}. **ABASTEÇA COM GASOLINA!**")
    
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.dataframe(df_pet[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    # Relatório por Banco (RESTAURADO)
    bancos = sorted(df_base['Banco'].unique())
    saldos_txt = ""
    for b in bancos:
        s = df_base[df_base['Banco'] == b]['V_Real'].sum()
        saldos_txt += f"- {b}: {m_fmt(s)}\n"
    st.text_area("Saldos Atuais por Banco", saldos_txt, height=200)
