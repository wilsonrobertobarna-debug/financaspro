import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v2.0", layout="wide")

@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
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

# --- 2. MENU LATERAL (Navegação e Exclusão) ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Resumo", "✏️ Editar Lançamentos", "🐾 Milo & Bolt", "🚗 Veículo"])

# LANÇAMENTO COM PARCELAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data Inicial", datetime.now())
        f_val = st.number_input("Valor (da parcela)", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_par = st.number_input("Nº de Parcelas", min_value=1, max_value=48, value=1)
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet", "Veículo", "Obra", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix"])
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                data_parc = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
                desc_final = f"{f_des} ({i+1}/{f_par})" if f_par > 1 else f_des
                ws.append_row([data_parc, v_str, desc_final, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# EXCLUSÃO DETALHADA (ID - DATA - DESC - VALOR)
with st.sidebar.expander("🗑️ Excluir (ID - Data - Desc - Valor)"):
    if not df_base.empty:
        # Criando a lista exatamente como você pediu
        opcoes = []
        for _, r in df_base.tail(20).iterrows(): # Mostra os últimos 20 lançamentos
            opcoes.append(f"{r['ID_Planilha']} - {r['Data']} - {r['Descrição']} - {m_fmt(r['V_Num'])}")
        
        selecao = st.selectbox("Selecione para apagar:", [""] + opcoes)
        if selecao and st.button("APAGAR AGORA"):
            id_para_deletar = int(selecao.split(" - ")[0])
            ws.delete_rows(id_para_deletar)
            st.cache_data.clear(); st.rerun()

# --- 3. CONTEÚDO PRINCIPAL ---

if aba == "💰 Resumo":
    st.title("🛡️ FinançasPro - Geral")
    if not df_base.empty:
        st.dataframe(df_base, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco"), use_container_width=True, hide_index=True)

elif aba == "✏️ Editar Lançamentos":
    st.title("✏️ Alterar Valor ou Data")
    st.warning("Use esta aba para corrigir erros sem precisar excluir.")
    
    if not df_base.empty:
        # Busca por ID
        col_id, col_btn = st.columns([1, 2])
        id_edit = col_id.number_input("Digite o ID para editar:", min_value=2, step=1)
        
        item = df_base[df_base['ID_Planilha'] == id_edit]
        
        if not item.empty:
            with st.form("form_edicao"):
                st.write(f"Editando: **{item['Descrição'].values[0]}**")
                nova_data = st.date_input("Nova Data", item['DT'].values[0])
                novo_valor = st.number_input("Novo Valor", value=float(item['V_Num'].values[0]))
                nova_desc = st.text_input("Nova Descrição", value=item['Descrição'].values[0])
                
                if st.form_submit_button("ATUALIZAR NA PLANILHA"):
                    v_edit = f"{novo_valor:.2f}".replace('.', ',')
                    d_edit = nova_data.strftime("%d/%m/%Y")
                    # Atualiza células específicas (Coluna A=Data, B=Valor, C=Descrição)
                    ws.update_cell(id_edit, 1, d_edit)
                    ws.update_cell(id_edit, 2, v_edit)
                    ws.update_cell(id_edit, 3, nova_desc)
                    st.cache_data.clear(); st.success("Atualizado!"); st.rerun()
        else:
            st.info("ID não encontrado. Verifique o número na lista de exclusão.")

# ... (Abas de Pet e Veículo seguem o padrão anterior)
