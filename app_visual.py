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
        st.error("⚠️ Wilson, os SEGREDOS não foram encontrados!")
        st.stop()
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

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
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

# 4. SIDEBAR - MENU E NOVO LANÇAMENTO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
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

# 5. TELAS
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_pie = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_pie.empty:
                st.plotly_chart(px.pie(df_pie, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_fluxo = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_fluxo.empty:
                # Cores padronizadas: Verde para Receita/Rendimento, Vermelho para Despesa
                cores = {'Receita': '#2ecc71', 'Rendimento': '#27ae60', 'Despesa': '#e74c3c'}
                st.plotly_chart(px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', color_discrete_map=cores, title="Entradas vs Saídas"), use_container_width=True)

        st.divider()
        st.subheader("🔍 Histórico com Filtro por Banco")
        f1, f2 = st.columns(2)
        s_bnc = f1.multiselect("Filtrar por Banco:", sorted(df_base['Banco'].unique()))
        s_sta = f2.multiselect("Filtrar por Status:", ["Pago", "Pendente"])
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        st.dataframe(df_v[['ID', 'Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Detalhes Milo & Bolt")
    st.info("Em breve: Linha do tempo de vacinas e vermífugos aqui.")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Gasto Total com os Meninos", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    
    # --- NOVIDADE: CALCULADORA FLEX ---
    st.subheader("⛽ Calculadora Álcool vs Gasolina")
    col_calc1, col_calc2, col_res = st.columns([1, 1, 2])
    p_alc = col_calc1.number_input("Preço Álcool", min_value=0.0, step=0.01)
    p_gas = col_calc2.number_input("Preço Gasolina", min_value=0.0, step=0.01)
    
    if p_alc > 0 and p_gas > 0:
        relacao = p_alc / p_gas
        if relacao <= 0.7:
            col_res.success(f"Abasteça com ÁLCOOL! (Relação: {relacao:.2%})")
        else:
            col_res.warning(f"Abasteça com GASOLINA! (Relação: {relacao:.2%})")
    
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível|Manutenção', case=False, na=False)]
    st.metric("Total Acumulado com Veículo", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

# EDIÇÃO NO SIDEBAR SEMPRE DISPONÍVEL
st.sidebar.divider()
if not df_base.empty:
    lista_opcoes = {f"ID: {r['ID']} | {r['Data']} | R$ {r['Valor']}": r for _, r in df_base.tail(15).iterrows()}
    escolha = st.sidebar.selectbox("⚙️ Alterar Lançamento:", [""] + list(lista_opcoes.keys()))
    if escolha:
        item = lista_opcoes[escolha]
        e_desc = st.sidebar.text_input("Descrição:", value=item['Descrição'])
        e_val = st.sidebar.text_input("Valor:", value=item['Valor'])
        if st.sidebar.button("💾 ATUALIZAR"):
            ws_base.update_cell(int(item['ID']), 3, e_desc)
            ws_base.update_cell(int(item['ID']), 2, e_val)
            st.cache_data.clear(); st.rerun()
