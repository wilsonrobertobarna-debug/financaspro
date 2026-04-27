import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO (SEGURA E LIMPA)
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, os SEGREDOS (Secrets) não foram encontrados!")
        st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"],
            "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"),
            "private_key": pk,
            "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro na chave: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    ws = sh.get_worksheet(0)
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df = df[df['Data'].str.strip() != ""].copy()
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (ÍCONES RESTAURADOS)
st.sidebar.title("🎮 Painel Wilson")
# Aqui voltamos com os ícones exatamente como você queria:
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    
    # Categorias mudam conforme a aba para facilitar sua vida
    lista_cats = ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros"]
    if "🐾" in aba:
        lista_cats = ["Pet: Milo", "Pet: Bolt", "Geral Pet"]
    elif "🚗" in aba:
        lista_cats = ["Combustível", "Manutenção", "IPVA/Seguro"]
        
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        sh.get_worksheet(0).append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. ABAS
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        c2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        c3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        c4.metric("⏳ Pendente", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty:
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos do Mês", hole=0.4), use_container_width=True)
        with g2:
            df_b = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            st.plotly_chart(px.bar(df_b, x='Tipo', y='V_Num', color='Tipo', title="Fluxo de Caixa"), use_container_width=True)
        
        st.divider()
        st.subheader("🔍 Filtros de Lançamentos")
        f1, f2 = st.columns(2)
        s_bnc = f1.multiselect("Banco:", sorted(df_base['Banco'].unique()))
        s_sta = f2.multiselect("Status:", ["Pago", "Pendente"])
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Lançamentos dos Meninos")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Total Investido neles", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Gastos com Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível|Manutenção', case=False, na=False)]
    st.metric("Total no Veículo", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

# 6. GERENCIADOR (SIDEBAR)
st.sidebar.divider()
if not df_base.empty:
    opcoes = {f"L{i+2} | {r['Descrição']}": i+2 for i, r in df_base.tail(15).iterrows()}
    sel = st.sidebar.selectbox("Ação na linha:", [""] + list(opcoes.keys()))
    if sel and st.sidebar.button("🚨 APAGAR"):
        sh.get_worksheet(0).delete_rows(int(opcoes[sel]))
        st.cache_data.clear(); st.rerun()
