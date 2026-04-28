import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. BASE INQUEBRÁVEL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

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
ws_base = sh.get_worksheet(0)

@st.cache_data(ttl=2)
def carregar_dados():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Linha'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 2. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# 3. FORMULÁRIOS LATERAIS (Lançamento e Transferência)
st.sidebar.divider()

with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# REINCLUÍDO: BLOCO DE TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferência entre Contas"):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data da TR", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor TR", min_value=0.0)
        t_sai = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_ent = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
        if st.form_submit_button("EFETUAR TRANSFERÊNCIA"):
            if t_sai != t_ent:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = t_dat.strftime("%d/%m/%Y")
                # Lança a saída e a entrada na planilha
                ws_base.append_row([d_str, v_str, f"TR: Saída para {t_ent}", "Transferência", "Despesa", t_sai, "Pago"])
                ws_base.append_row([d_str, v_str, f"TR: Entrada de {t_sai}", "Transferência", "Receita", t_ent, "Pago"])
                st.cache_data.clear(); st.rerun()
            else:
                st.error("Escolha bancos diferentes!")

# 4. CONTEÚDO DAS ABAS
try:
    if aba == "💰 Finanças":
        st.title("🛡️ FinançasPro - Geral")
        if not df_base.empty:
            rec = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
            des = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
            st.info(f"### Saldo Total: {m_fmt(rec - des)}")
            st.dataframe(df_base, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), use_container_width=True, hide_index=True)

    elif aba == "🐾 Milo & Bolt":
        st.title("🐾 Milo & Bolt")
        df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
        st.metric("Gasto Acumulado", m_fmt(df_p['V_Num'].sum()))
        st.dataframe(df_p, column_order=("Data", "Descrição", "Valor", "Status"), use_container_width=True, hide_index=True)

    elif aba == "🚗 Meu Veículo":
        st.title("🚗 Gestão Veículo")
        df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
        st.dataframe(df_v, column_order=("Data", "Descrição", "Valor", "Status"), use_container_width=True, hide_index=True)

    elif aba == "📄 Relatórios":
        st.title("📄 Relatórios")
        c1, c2 = st.columns(2)
        d1 = c1.date_input("Início", datetime.now() - relativedelta(months=1))
        d2 = c2.date_input("Fim", datetime.now())
        if not df_base.empty:
            df_r = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
            st.dataframe(df_r, use_container_width=True)

except Exception as e:
    st.error(f"Erro na aba: {e}")

# 5. EXCLUSÃO
st.sidebar.divider()
with st.sidebar.expander("🗑️ Excluir"):
    if not df_base.empty:
        lista = [f"{r['Data']} - {r['Descrição']}" for _, r in df_base.head(10).iterrows()]
        sel = st.selectbox("Apagar qual?", [""] + lista)
        if sel and st.button("CONFIRMAR"):
            idx = df_base.iloc[lista.index(sel)]['ID_Linha']
            ws_base.delete_rows(int(idx))
            st.cache_data.clear(); st.rerun()
