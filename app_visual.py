import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v2.5", layout="wide")

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
aba = st.sidebar.radio("Navegação:", ["💰 Finanças (Geral)", "✏️ Editar Lançamento", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

st.sidebar.divider()

# NOVO LANÇAMENTO (COM PARCELA)
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor da Parcela", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_par = st.number_input("Total de Parcelas", min_value=1, value=1)
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        if st.form_submit_button("SALVAR LANÇAMENTO"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(int(f_par)):
                dt_p = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
                desc_p = f"{f_des} [{i+1}/{int(f_par)}]" if f_par > 1 else f_des
                ws.append_row([dt_p, v_str, desc_p, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# TRANSFERÊNCIA (COM DESCRIÇÃO)
with st.sidebar.expander("💸 Transferência"):
    with st.form("f_tr"):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0)
        t_des = st.text_input("Descrição/Motivo")
        t_sai = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_ent = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
        if st.form_submit_button("EXECUTAR"):
            v_s = f"{t_val:.2f}".replace('.', ',')
            d_s = t_dat.strftime("%d/%m/%Y")
            ws.append_row([d_s, v_s, f"TR: {t_des} (De {t_sai} para {t_ent})", "Transferência", "Despesa", t_sai, "Pago"])
            ws.append_row([d_s, v_s, f"TR: {t_des} (De {t_sai} para {t_ent})", "Transferência", "Receita", t_ent, "Pago"])
            st.cache_data.clear(); st.rerun()

# EXCLUSÃO (DETALHADA)
st.sidebar.divider()
with st.sidebar.expander("🗑️ Excluir Lançamento"):
    if not df_base.empty:
        recente = df_base.tail(20).iloc[::-1]
        opcoes = [f"{r['ID_Planilha']} | {r['Data']} | {r['Descrição']} | {m_fmt(r['V_Num'])}" for _, r in recente.iterrows()]
        sel_del = st.selectbox("Escolha o item para apagar:", [""] + opcoes)
        if sel_del and st.button("CONFIRMAR EXCLUSÃO"):
            id_id = int(sel_del.split(" | ")[0])
            ws.delete_rows(id_id)
            st.cache_data.clear(); st.rerun()

# --- 3. TELAS ---

if aba == "💰 Finanças (Geral)":
    st.title("🛡️ FinançasPro - Geral")
    if not df_base.empty:
        rec = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### Saldo Atual: {m_fmt(rec - des)}")
        st.dataframe(df_base.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Categoria", "Banco", "Tipo"), 
                     use_container_width=True, hide_index=True)

elif aba == "✏️ Editar Lançamento":
    st.title("✏️ Editar")
    id_e = st.number_input("Digite o ID do Lançamento:", min_value=2, step=1)
    it = df_base[df_base['ID_Planilha'] == id_e]
    if not it.empty:
        with st.form("ed_wilson"):
            st.warning(f"Editando: {it['Descrição'].iloc[0]}")
            n_d = st.date_input("Data", it['DT'].iloc[0].to_pydatetime(), format="DD/MM/YYYY")
            n_v = st.number_input("Valor", value=float(it['V_Num'].iloc[0]))
            n_txt = st.text_input("Descrição", value=it['Descrição'].iloc[0])
            n_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Outros"], index=0)
            if st.form_submit_button("SALVAR ALTERAÇÕES"):
                ws.update_cell(id_e, 1, n_d.strftime("%d/%m/%Y"))
                ws.update_cell(id_e, 2, f"{n_v:.2f}".replace('.', ','))
                ws.update_cell(id_e, 3, n_txt)
                ws.update_cell(id_e, 4, n_cat)
                st.cache_data.clear(); st.success("Atualizado!"); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_p.empty:
        st.metric("Total Gasto Pets", m_fmt(df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()))
        st.dataframe(df_p.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Banco", "Tipo"), 
                     use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    if not df_v.empty:
        st.metric("Total Gasto Veículo", m_fmt(df_v[df_v['Tipo'] == 'Despesa']['V_Num'].sum()))
        st.dataframe(df_v.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Banco", "Tipo"), 
                     use_container_width=True, hide_index=True)
