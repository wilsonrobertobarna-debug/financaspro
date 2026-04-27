import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO COM O GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique as chaves secretas no Streamlit!")
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
        st.error(f"Erro de conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO DE DADOS
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

# 4. BARRA LATERAL (SIDEBAR)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# FORMULÁRIO DE NOVO LANÇAMENTO
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

# 5. TELAS PRINCIPAIS
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
                st.plotly_chart(px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="Resumo Mensal"), use_container_width=True)

        st.divider()
        # --- GRÁFICO DE METAS (PROTEGIDO) ---
        st.subheader("🎯 Comparativo: Gasto Real vs Meta")
        metas_f = {"Mercado": 1200, "Internet": 150, "Luz/Água": 350, "Pet: Milo": 400, "Pet: Bolt": 400, "Veículo": 600}
        df_metas = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_metas.empty:
            df_metas['Meta'] = df_metas['Categoria'].map(metas_f).fillna(400.0)
            fig_meta = go.Figure()
            fig_meta.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['V_Num'], name='Gasto Atual', marker_color='#e74c3c'))
            fig_meta.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['Meta'], name='Meta Limite', marker_color='#2ecc71', opacity=0.4))
            fig_meta.update_layout(barmode='group')
            st.plotly_chart(fig_meta, use_container_width=True)

        st.divider()
        st.subheader("🔍 Histórico")
        st.dataframe(df_base[['ID', 'Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Ração|Milo|Bolt', case=False, na=False)]
    st.metric("Total Gasto", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("Vá de ÁLCOOL!")
        else: c3.warning("Vá de GASOLINA!")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True)

# EDIÇÃO NA SIDEBAR
st.sidebar.divider()
if not df_base.empty:
    lista = {f"ID: {r['ID']} | {r['Descrição']}": r for _, r in df_base.tail(15).iterrows()}
    sel = st.sidebar.selectbox("⚙️ Editar Lançamento:", [""] + list(lista.keys()))
    if sel:
        item = lista[sel]
        v_desc = st.sidebar.text_input("Descrição:", value=item['Descrição'])
        v_val = st.sidebar.text_input("Valor:", value=item['Valor'])
        if st.sidebar.button("💾 ATUALIZAR"):
            ws_base.update_cell(int(item['ID']), 3, v_desc)
            ws_base.update_cell(int(item['ID']), 2, v_val)
            st.cache_data.clear(); st.rerun()
