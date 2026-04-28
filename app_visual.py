import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", initial_sidebar_state="expanded")

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets no Streamlit Cloud!"); st.stop()
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
        st.error(f"Erro na conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E TRATAMENTO DE DADOS
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

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - FORMULÁRIOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# FORMULÁRIO: NOVO LANÇAMENTO (TECLADO NUMÉRICO ATIVO)
with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor (Use ponto para centavos)", min_value=0.0, step=0.01, format="%.2f")
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
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

# FORMULÁRIO: TRANSFERÊNCIA
with st.sidebar.form("f_transf", clear_on_submit=True):
    st.write("### 💸 Transferência Entre Bancos")
    t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    t_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
    t_orig = st.selectbox("Origem (Sai):", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    t_dest = st.selectbox("Destino (Entra):", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
    t_desc = st.text_input("Nota da Transferência")
    if st.form_submit_button("CONFIRMAR TRANSFERÊNCIA"):
        if t_orig == t_dest: st.error("Escolha bancos diferentes!")
        else:
            v_str = f"{t_val:.2f}".replace('.', ',')
            d_str = t_dat.strftime("%d/%m/%Y")
            ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

# 5. TELA PRINCIPAL: FINANÇAS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # SALDO GERAL HISTÓRICO
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ACUMULADO: {m_fmt(saldo_geral)}")

        # FILTROS DO MÊS
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita (Abril)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto (Abril)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento (Abril)", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente (Abril)", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()

        # GERENCIADOR DE METAS (VISUAL)
        with st.expander("🎯 Configurar Metas do Mês"):
            c_meta1, c_meta2, c_meta3 = st.columns(3)
            val_mercado = c_meta1.number_input("Meta Mercado", value=1200.0)
            val_pets = c_meta2.number_input("Meta Pets", value=400.0)
            val_carro = c_meta3.number_input("Meta Veículo", value=600.0)
            metas_map = {"Mercado": val_mercado, "Pet: Milo": val_pets, "Pet: Bolt": val_pets, "Veículo": val_carro, "Internet": 150.0, "Luz/Água": 350.0}

        # GRÁFICOS
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_metas = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_metas.empty:
                df_metas['Meta'] = df_metas['Categoria'].map(metas_map).fillna(0.0)
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['V_Num'], name='Real', marker_color='#e74c3c'))
                fig_m.add_trace(go.Bar(x=df_metas['Categoria'], y=df_metas['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
                fig_m.update_layout(barmode='group', title="Metas vs Realizado", height=350); st.plotly_chart(fig_m, use_container_width=True)

        st.divider()
        st.subheader("🔍 Busca e Filtros")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Filtrar Banco:", sorted(df_base['Banco'].unique()))
        s_sta = c2.multiselect("Filtrar Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Buscar Beneficiário/Descrição:")

        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

# TELA: MILO & BOLT
elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.metric("Gasto Total com Pets (Abril)", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
    st.dataframe(df_pet[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

# TELA: VEÍCULO
elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("💡 RECOMENDAÇÃO: ABASTEÇA COM ÁLCOOL!")
        else: c3.warning("💡 RECOMENDAÇÃO: ABASTEÇA COM GASOLINA!")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

# FUNÇÃO EDITAR/APAGAR (RODAPÉ SIDEBAR)
st.sidebar.divider()
if not df_base.empty:
    lista_edit = {f"ID {r['ID']} | {r['Data']} | {r['Descrição']}": r for _, r in df_base.tail(20).iterrows()}
    escolha = st.sidebar.selectbox("⚙️ Editar Lançamento:", [""] + list(lista_edit.keys()))
    if escolha:
        item = lista_edit[escolha]
        ed_data = st.sidebar.text_input("Data:", value=str(item['Data']))
        ed_desc = st.sidebar.text_input("Descrição:", value=str(item['Descrição']))
        ed_valor = st.sidebar.text_input("Valor:", value=str(item['Valor']))
        c_ed1, c_ed2 = st.sidebar.columns(2)
        if c_ed1.button("💾 ATUALIZAR"):
            ws_base.update_cell(int(item['ID']), 1, ed_data)
            ws_base.update_cell(int(item['ID']), 3, ed_desc)
            ws_base.update_cell(int(item['ID']), 2, ed_valor)
            st.cache_data.clear(); st.rerun()
        if c_ed2.button("🚨 EXCLUIR"):
            ws_base.delete_rows(int(item['ID'])); st.cache_data.clear(); st.rerun()
