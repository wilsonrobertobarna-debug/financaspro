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

# 3. CARREGAMENTO COM ID
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

# 4. SIDEBAR - LANÇAMENTO E EDIÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_data = f_dat + relativedelta(months=i)
            ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# EDIÇÃO NO SIDEBAR
st.sidebar.divider()
if not df_base.empty:
    lista_opcoes = {f"ID: {r['ID']} | {r['Data']} | {r['Descrição']} | R$ {r['Valor']}": r for _, r in df_base.tail(15).iterrows()}
    escolha = st.sidebar.selectbox("Alterar Lançamento:", [""] + list(lista_opcoes.keys()))
    if escolha:
        item = lista_opcoes[escolha]
        e_desc = st.sidebar.text_input("Nova Descrição:", value=item['Descrição'])
        e_valor = st.sidebar.text_input("Novo Valor:", value=item['Valor'])
        e_status = st.sidebar.selectbox("Novo Status:", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
        c1, c2 = st.sidebar.columns(2)
        if c1.button("💾 SALVAR"):
            ws_base.update_cell(int(item['ID']), 3, e_desc)
            ws_base.update_cell(int(item['ID']), 2, e_valor)
            ws_base.update_cell(int(item['ID']), 7, e_status)
            st.cache_data.clear(); st.rerun()
        if c2.button("🚨 APAGAR"):
            ws_base.delete_rows(int(item['ID']))
            st.cache_data.clear(); st.rerun()

# 5. TELAS E GRÁFICOS
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        # MÉTRICAS
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Despesas", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()

        # --- SEÇÃO DE GRÁFICOS ---
        g1, g2 = st.columns(2)
        with g1:
            # 1. PIZZA: CATEGORIAS
            df_pie = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_pie.empty:
                st.plotly_chart(px.pie(df_pie, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            # 2. BARRA: RECEITA VS DESPESA
            df_fluxo = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_fluxo.empty:
                st.plotly_chart(px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', title="Receitas vs Despesas (Mês)"), use_container_width=True)

        st.divider()
        # 3. GRÁFICO DE METAS POR CATEGORIA (Novo)
        st.subheader("🎯 Metas de Gastos por Categoria")
        # Defina aqui suas metas (Exemplo: Mercado meta 1000)
        metas = {"Mercado": 1200, "Internet": 150, "Luz/Água": 300, "Pet: Milo": 400, "Pet: Bolt": 400, "Veículo": 600}
        
        df_gastos = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_gastos.empty:
            df_gastos['Meta'] = df_gastos['Categoria'].map(metas).fillna(500) # Se não tiver meta, assume 500
            
            fig_meta = go.Figure()
            fig_meta.add_trace(go.Bar(x=df_gastos['Categoria'], y=df_gastos['V_Num'], name='Gasto Atual', marker_color='red'))
            fig_meta.add_trace(go.Bar(x=df_gastos['Categoria'], y=df_gastos['Meta'], name='Meta Estipulada', marker_color='green', opacity=0.5))
            fig_meta.update_layout(barmode='group', title="Gasto Atual vs Meta (Verde)")
            st.plotly_chart(fig_meta, use_container_width=True)

        st.divider()
        st.subheader("🔍 Histórico e Pesquisa")
        f1, f2 = st.columns(2)
        s_bnc = f1.multiselect("Filtrar Banco:", sorted(df_base['Banco'].unique()))
        s_sta = f2.multiselect("Filtrar Status:", ["Pago", "Pendente"])
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        st.dataframe(df_v[['ID', 'Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Detalhes Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Total Acumulado", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Detalhes Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível', case=False, na=False)]
    st.metric("Total Acumulado", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)
