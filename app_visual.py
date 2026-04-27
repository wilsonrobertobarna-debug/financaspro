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

# NOVO LANÇAMENTO
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
        m4.metric("⏳ Pendente Total", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty:
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty:
                st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="Fluxo de Caixa"), use_container_width=True)

        st.subheader("🎯 Metas")
        metas_f = {"Mercado": 1200, "Internet": 150, "Luz/Água": 350, "Pet: Milo": 400, "Pet: Bolt": 400, "Veículo": 600}
        df_metas = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_metas.empty:
            df_metas['Meta'] = df_metas['Categoria'].map(metas_f).fillna(400.0)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['V_Num'], name='Real', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
            fig_m.update_layout(barmode='group', height=300)
            st.plotly_chart(fig_m, use_container_width=True)

        st.divider()
        st.subheader("🔍 Pesquisa")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Banco:", sorted(df_base['Banco'].unique()))
        s_sta = c2.multiselect("Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Descrição:")

        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['ID', 'Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Ração|Milo|Bolt', case=False, na=False)]
    st.dataframe(df_pet[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("Vá de ÁLCOOL!")
        else: c3.warning("Vá de GASOLINA!")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['ID', 'Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

# 6. ALTERAR LANÇAMENTO (BARRINHA CORRIGIDA)
st.sidebar.divider()
if not df_base.empty:
    # AQUI ESTÁ A CORREÇÃO: Montando o texto da barrinha com ID, Data, Valor e Descrição
    lista_edit = {f"ID {r['ID']} | {r['Data']} | R$ {r['Valor']} | {r['Descrição']}": r for _, r in df_base.tail(30).iterrows()}
    escolha = st.sidebar.selectbox("⚙️ Alterar Lançamento:", [""] + list(lista_edit.keys()))
    
    if escolha:
        dados_item = lista_edit[escolha]
        st.sidebar.warning(f"Editando Registro ID: {dados_item['ID']}")
        
        # Campos que aparecem logo abaixo da escolha
        ed_data = st.sidebar.text_input("Data:", value=str(dados_item['Data']))
        ed_desc = st.sidebar.text_input("Descrição:", value=str(dados_item['Descrição']))
        ed_valor = st.sidebar.text_input("Valor:", value=str(dados_item['Valor']))
        
        c_bt1, c_bt2 = st.sidebar.columns(2)
        if c_bt1.button("💾 GRAVAR"):
            ws_base.update_cell(int(dados_item['ID']), 1, ed_data)
            ws_base.update_cell(int(dados_item['ID']), 3, ed_desc)
            ws_base.update_cell(int(dados_item['ID']), 2, ed_valor)
            st.cache_data.clear(); st.rerun()
            
        if c_bt2.button("🚨 APAGAR"):
            ws_base.delete_rows(int(dados_item['ID']))
            st.cache_data.clear(); st.rerun()
