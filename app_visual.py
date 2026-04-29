import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v2.3", layout="wide")

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

# --- 2. MENU LATERAL (Ações Rápidas) ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Resumo Geral", "✏️ Editar Lançamento", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

st.sidebar.divider()

# FORMULÁRIO: NOVO LANÇAMENTO (COM PARCELAMENTO)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor da Parcela", min_value=0.0)
        f_des = st.text_input("Descrição do Gasto")
        f_par = st.number_input("Total de Parcelas", min_value=1, value=1)
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Obra", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        
        if st.form_submit_button("LANÇAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                data_p = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
                # Coloca a parcela direto na descrição para fácil leitura
                desc_p = f"{f_des} [{i+1}/{f_par}]" if f_par > 1 else f_des
                ws.append_row([data_p, v_str, desc_p, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# FORMULÁRIO: TRANSFERÊNCIA (REINTEGRADO)
with st.sidebar.expander("💸 Transferência entre Bancos"):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0)
        t_des = st.text_input("Motivo/Descrição")
        t_sai = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_ent = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
        
        if st.form_submit_button("EXECUTAR TR"):
            if t_sai != t_ent:
                v_s = f"{t_val:.2f}".replace('.', ',')
                d_s = t_dat.strftime("%d/%m/%Y")
                ws.append_row([d_s, v_s, f"TR: Saída ({t_des})", "Transferência", "Despesa", t_sai, "Pago"])
                ws.append_row([d_s, v_s, f"TR: Entrada ({t_des})", "Transferência", "Receita", t_ent, "Pago"])
                st.cache_data.clear(); st.rerun()
            else:
                st.error("Os bancos precisam ser diferentes!")

# --- 3. TELAS PRINCIPAIS ---

if aba == "💰 Resumo Geral":
    st.title("🛡️ FinançasPro - Resumo")
    if not df_base.empty:
        # Saldo rápido
        r_t = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        d_t = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### Saldo Consolidado: {m_fmt(r_t - d_t)}")
        
        st.dataframe(df_base.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Categoria", "Banco", "Tipo"), 
                     use_container_width=True, hide_index=True)

elif aba == "✏️ Editar Lançamento":
    st.title("✏️ Ajustar Lançamento")
    id_e = st.number_input("Informe o ID para editar:", min_value=2, step=1)
    item = df_base[df_base['ID_Planilha'] == id_e]
    if not item.empty:
        with st.form("edicao_v3"):
            st.warning(f"Alterando: {item['Descrição'].iloc[0]}")
            c1, c2 = st.columns(2)
            n_d = c1.date_input("Nova Data", item['DT'].iloc[0].to_pydatetime(), format="DD/MM/YYYY")
            n_v = c2.number_input("Novo Valor", value=float(item['V_Num'].iloc[0]))
            n_txt = st.text_input("Nova Descrição", value=item['Descrição'].iloc[0])
            if st.form_submit_button("SALVAR ALTERAÇÃO"):
                v_f = f"{n_v:.2f}".replace('.', ',')
                d_f = n_d.strftime("%d/%m/%Y")
                ws.update_cell(id_e, 1, d_f)
                ws.update_cell(id_e, 2, v_f)
                ws.update_cell(id_e, 3, n_txt)
                st.cache_data.clear(); st.success("Atualizado!"); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Área Pet")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.metric("Total Gasto com Pets", m_fmt(df_p['V_Num'].sum()))
    st.dataframe(df_p.sort_values('DT', ascending=False), 
                 column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Tipo", "Status"), 
                 use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão Veicular")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.metric("Total Gasto com Veículo", m_fmt(df_v['V_Num'].sum()))
    st.dataframe(df_v.sort_values('DT', ascending=False), 
                 column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Tipo", "Status"), 
                 use_container_width=True, hide_index=True)

# 4. EXCLUSÃO (Rodapé da Sidebar)
st.sidebar.divider()
with st.sidebar.expander("🗑️ Remover Lançamento"):
    if not df_base.empty:
        recente = df_base.tail(15).iloc[::-1]
        lista = [f"{r['ID_Planilha']} | {r['Data']} | {r['Descrição']}" for _, r in recente.iterrows()]
        sel = st.selectbox("Escolha:", [""] + lista)
        if sel and st.button("CONFIRMAR DELEÇÃO"):
            id_d = int(sel.split(" | ")[0])
            ws.delete_rows(id_d)
            st.cache_data.clear(); st.rerun()
