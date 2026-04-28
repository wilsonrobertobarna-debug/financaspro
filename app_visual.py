import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="FinançasPro Wilson v2.2", layout="wide")

@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

@st.cache_data(ttl=2)
def carregar_dados():
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Planilha'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. MENU LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Resumo", "✏️ Editar", "🐾 Milo & Bolt", "🚗 Veículo"])

# NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor Parcela", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_par = st.number_input("Nº Parcelas", min_value=1, value=1)
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Obra", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix"])
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                data_parc = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
                desc_f = f"{f_des} ({i+1}/{f_par})" if f_par > 1 else f_des
                ws.append_row([data_parc, v_str, desc_f, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# EXCLUSÃO RÁPIDA
with st.sidebar.expander("🗑️ Excluir"):
    if not df_base.empty:
        df_recente = df_base.tail(20).iloc[::-1]
        opcoes = [f"{r['ID_Planilha']} - {r['Data']} - {r['Descrição']}" for _, r in df_recente.iterrows()]
        sel = st.selectbox("Escolha para apagar:", [""] + opcoes)
        if sel and st.button("CONFIRMAR EXCLUSÃO"):
            id_del = int(sel.split(" - ")[0])
            ws.delete_rows(id_del)
            st.cache_data.clear(); st.rerun()

# --- 3. TELAS ---

if aba == "💰 Resumo":
    st.title("🛡️ Resumo Geral")
    if not df_base.empty:
        st.dataframe(df_base.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Categoria", "Banco"), 
                     use_container_width=True, hide_index=True)

elif aba == "✏️ Editar":
    st.title("✏️ Alterar Lançamento")
    id_edit = st.number_input("ID do Lançamento:", min_value=2, step=1)
    item = df_base[df_base['ID_Planilha'] == id_edit]
    if not item.empty:
        with st.form("form_edit_v2"):
            st.info(f"Editando: {item['Descrição'].iloc[0]}")
            n_data = st.date_input("Data", item['DT'].iloc[0].to_pydatetime(), format="DD/MM/YYYY")
            n_val = st.number_input("Valor", value=float(item['V_Num'].iloc[0]))
            n_desc = st.text_input("Descrição", value=item['Descrição'].iloc[0])
            if st.form_submit_button("✅ SALVAR"):
                v_f = f"{n_val:.2f}".replace('.', ',')
                d_f = n_data.strftime("%d/%m/%Y")
                ws.update_cell(id_edit, 1, d_f)
                ws.update_cell(id_edit, 2, v_f)
                ws.update_cell(id_edit, 3, n_desc)
                st.cache_data.clear(); st.success("Sucesso!"); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)].copy()
    if not df_p.empty:
        st.metric("Total Gasto com Pets", m_fmt(df_p['V_Num'].sum()))
        # Adicionado ID e Tipo para controle total
        st.dataframe(df_p.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Tipo", "Status"), 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento encontrado para Milo & Bolt.")

elif aba == "🚗 Veículo":
    st.title("🚗 Gestão do Veículo")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)].copy()
    if not df_v.empty:
        st.metric("Total Gasto com Veículo", m_fmt(df_v['V_Num'].sum()))
        # Adicionado ID e Tipo para controle total
        st.dataframe(df_v.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Tipo", "Status"), 
                     use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento encontrado para o Veículo.")
