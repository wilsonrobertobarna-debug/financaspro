import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

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
        st.error(f"Erro conexão: {e}"); st.stop()

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
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# FORMULÁRIOS (MANTIDOS)
with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_data = f_dat + relativedelta(months=i)
            ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

with st.sidebar.form("f_transf", clear_on_submit=True):
    st.write("### 💸 Transferência")
    t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    t_val = st.number_input("Valor Transferido", min_value=0.0, step=0.01)
    t_orig = st.selectbox("De onde sai (Origem):", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    t_dest = st.selectbox("Para onde vai (Destino):", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
    t_desc = st.text_input("Descrição")
    if st.form_submit_button("TRANSFERIR"):
        if t_orig == t_dest: st.error("Bancos iguais!")
        else:
            v_str = f"{t_val:.2f}".replace('.', ',')
            d_str = t_dat.strftime("%d/%m/%Y")
            ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

# 5. TELAS E CÁLCULOS
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # CÁLCULO DE SALDO GERAL (HISTÓRICO TODO)
        receitas_total = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesas_total = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        saldo_geral = receitas_total - despesas_total

        # FILTRO PARA O MÊS ATUAL (GRÁFICOS)
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        # MÉTRICAS NO TOPO
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🏦 SALDO GERAL", m_fmt(saldo_geral))
        m2.metric("📉 Gastos Mês", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento Mês", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente Total", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()

        # GRÁFICOS
        g1, g2 = st.columns(2)
        with g1:
            # Pizza ignora Transferências para não mentir o gasto
            df_p = df_m[(df_m['Tipo'] == 'Despesa') & (df_m['Categoria'] != 'Transferência')].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty:
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos Reais por Categoria", hole=0.4), use_container_width=True)
        with g2:
            # Fluxo de Caixa (Receita vs Despesa)
            df_f = df_m[df_m['Categoria'] != 'Transferência'].groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty:
                st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="Fluxo de Caixa (S/ Transferências)"), use_container_width=True)

        st.divider()
        st.subheader("🔍 Pesquisa e Histórico")
        st.dataframe(df_base[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

# ... (Manter seções de Milo e Veículo como no código anterior)
