import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
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

# 3. CARREGAMENTO (Com ID de Linha para Exclusão)
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    
    # O segredo para a exclusão: mapear a linha exata da planilha
    df['ID_Linha'] = range(2, len(df) + 2)
    
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

# 4. SIDEBAR - NAVEGAÇÃO E LANÇAMENTOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# LANÇAMENTO COM PARCELAS
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, "Despesa", f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Resumo
        rec = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(rec - des)}")

        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        # Tabelas com Visual Limpo
        st.subheader("🔍 Lançamentos Recentes")
        st.dataframe(df_base, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.dataframe(df_pet, column_order=("Data", "Descrição", "Valor", "Status"), use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_car, column_order=("Data", "Descrição", "Valor", "Status"), use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatórios")
    # Filtro de data simplificado
    d_ini = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d_fim = st.date_input("Fim", datetime.now())
    if not df_base.empty:
        df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)]
        st.dataframe(df_per, column_order=("Data", "Descrição", "Valor", "Status"), use_container_width=True)

# 6. FERRAMENTA DE EXCLUSÃO (A CORREÇÃO QUE VOCÊ PEDIU)
st.sidebar.divider()
with st.sidebar.expander("⚙️ Gerenciar Lançamentos"):
    if not df_base.empty:
        # Mostra os últimos 15 para facilitar a busca
        lista_recente = df_base.head(15)
        opcoes = [f"{r['Data']} - {r['Descrição']} ({m_fmt(r['V_Num'])})" for _, r in lista_recente.iterrows()]
        selecao = st.selectbox("Selecione para excluir:", [""] + opcoes)
        
        if selecao:
            # Pegamos o ID da linha que guardamos lá no carregar()
            idx_interno = lista_recente.index[opcoes.index(selecao)]
            linha_para_deletar = int(lista_recente.loc[idx_interno, 'ID_Linha'])
            
            st.error(f"⚠️ Excluir: {selecao}?")
            if st.button("CONFIRMAR EXCLUSÃO"):
                try:
                    ws_base.delete_rows(linha_para_deletar)
                    st.success("Removido!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro: {e}")
