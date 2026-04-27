import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
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

# 4. SIDEBAR - LANÇAMENTO E MENU
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    
    lista_cats = ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo"]
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_data = f_dat + relativedelta(months=i)
            desc_parc = f"{f_des} ({i+1}/{f_par})" if f_par > 1 else f_des
            ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, desc_parc, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. GERENCIADOR - AGORA COM EDIÇÃO
st.sidebar.divider()
st.sidebar.subheader("⚙️ Editar/Alterar Valor")
if not df_base.empty:
    # Pegamos as últimas 20 linhas para editar
    df_edit = df_base.copy()
    df_edit['ID'] = df_edit.index + 2
    opcoes_edit = {f"L{r['ID']} | {r['Descrição']}": r for _, r in df_edit.tail(20).iterrows()}
    
    sel_edit = st.sidebar.selectbox("Escolha para alterar:", [""] + list(opcoes_edit.keys()))
    
    if sel_edit:
        item = opcoes_edit[sel_edit]
        with st.sidebar.container():
            # Campos preenchidos com o que já está na planilha
            new_val = st.text_input("Novo Valor:", value=str(item['Valor']))
            new_sta = st.selectbox("Novo Status:", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
            
            col1, col2 = st.columns(2)
            if col1.button("💾 ATUALIZAR"):
                # Atualiza a célula do Valor (Coluna 2) e Status (Coluna 7)
                ws_base.update_cell(int(item['ID']), 2, new_val)
                ws_base.update_cell(int(item['ID']), 7, new_sta)
                st.cache_data.clear(); st.rerun()
                
            if col2.button("🚨 APAGAR"):
                ws_base.delete_rows(int(item['ID']))
                st.cache_data.clear(); st.rerun()

# 6. VISUALIZAÇÃO (DEMAIS TELAS)
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
        st.subheader("🔍 Filtros e Lançamentos")
        f1, f2 = st.columns(2)
        s_bnc = f1.multiselect("Banco:", sorted(df_base['Banco'].unique()))
        s_sta = f2.multiselect("Status:", ["Pago", "Pendente"])
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        st.dataframe(df_v[['Data', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🐾" in aba:
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.metric("Total neles", m_fmt(df_pet['V_Num'].sum()))
    st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

elif "🚗" in aba:
    st.title("🚗 Meu Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Carro|Combustível', case=False, na=False)]
    st.metric("Total Veículo", m_fmt(df_car['V_Num'].sum()))
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Banco', 'Status']].iloc[::-1], use_container_width=True)
