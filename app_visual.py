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
            "private_key": pk, "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO COMPLETO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Linha'] = range(2, len(df) + 2) # Para edição/exclusão
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): 
    return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. BARRA LATERAL (NAVEGAÇÃO E LANÇAMENTOS)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# LANÇAMENTO COM PARCELAS
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro", "XP", "Mercado Pago"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01)
        t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
        if st.form_submit_button("TRANSFERIR"):
            if t_orig != t_dest:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, f"TR: Saída", "Transferência", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, f"TR: Entrada", "Transferência", "Receita", t_dest, "Pago"])
                st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Saldo Geral
        rec_total = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des_total = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(rec_total - des_total)}")

        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        # Métricas do Mês
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Despesa", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        # Gráficos (Plotly de volta!)
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo de Caixa Mensal"), use_container_width=True)

        # Busca e Tabela Limpa
        st.subheader("🔍 Lançamentos Recentes")
        b_desc = st.text_input("Filtrar por descrição:")
        df_v = df_base.copy()
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
        # O segredo do visual limpo está aqui: column_order esconde as colunas técnicas
        st.dataframe(df_v, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Acumulado (Milo & Bolt)", m_fmt(df_pet['V_Num'].sum()))
        st.dataframe(df_pet, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro para os pets.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("💡 RECOMENDAÇÃO: ABASTEÇA COM ÁLCOOL!")
        else: c3.warning("💡 RECOMENDAÇÃO: ABASTEÇA COM GASOLINA!")
    
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.metric("Total Gasto com Veículo", m_fmt(df_car['V_Num'].sum()))
        st.dataframe(df_car, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim =
