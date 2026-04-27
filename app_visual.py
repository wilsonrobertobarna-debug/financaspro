import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .resumo-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        # Bancos e Categorias
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        
        # Base Principal (Geral)
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        if len(dados) > 1:
            df_base = pd.DataFrame(dados[1:], columns=dados[0])
        else:
            df_base = pd.DataFrame(columns=["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"])
        
        return df_b, df_c, df_base
    except Exception as e:
        st.error(f"Erro ao carregar Planilha: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

# 4. PROCESSAMENTO
if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    # Garante que as colunas essenciais existem
    cols_necessarias = ["Data", "Valor", "Categoria", "Tipo", "Banco", "Status"]
    for col in cols_necessarias:
        if col not in df_base.columns: df_base[col] = ""
        
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR (LANÇAMENTOS E NAVEGAÇÃO)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# FORMULÁRIO ÚNICO (Geral ou Pets)
with st.sidebar.form("f_novo"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    
    # Se estiver na aba pet, sugere categorias pet, senão as gerais
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    if aba == "🐾 Milo & Bolt":
        lista_cats = ["Pet: Milo - Ração", "Pet: Milo - Vet", "Pet: Bolt - Ração", "Pet: Bolt - Vet", "Gasto Geral Pet"]
    
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_p = f"{f_cat} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_cat
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_p, f_tip, f_bnc, f_sta])
        st.cache_data.clear()
        st.rerun()

# 6. CONTEÚDO DAS ABAS
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Métricas
        df_realizado = df_base[df_base['Status'] != 'Pendente']
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0
        t_rec = df_realizado[(df_realizado['Tipo'] == 'Receita') | (df_realizado['Tipo'] == 'Rendimento')]['V_Num'].sum()
        t_des = df_realizado[df_realizado['Tipo'] == 'Despesa']['V_Num'].sum()
        saldo_geral = s_ini + t_rec - t_des

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        df_mes = df_base[df_base['Mes_Ano'] == mes_atual]
        m_rec = df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum()
        m_des = df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum()
        m_ren = df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum()
        m_pen = df_mes[df_mes['Status'] == 'Pendente']['V_Num'].sum()

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {m_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # Tabela e Resumo
        st.write("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_base.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1].head(20), use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        df_pets = df_base[df_base['Categoria'].str.contains('Milo|Bolt|Pet|Ração', case=False)]
        st.info(f"Total Investido nos Pets: **R$ {df_pets['V_Num'].sum():,.2f}**".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_pets.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. GERENCIADOR (Lado de fora para aparecer em qualquer aba)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar")
if not df_base.empty:
    lista_edit = df_base.iloc[::-1].head(10)
    opcoes = [f"{idx+2} | {row['Data']} | {row['Categoria']} | {row['Valor']}" for idx, row in lista_edit.iterrows()]
    sel = st.sidebar.selectbox("Editar/Excluir:", [""] + opcoes)
    if sel:
        linha = int(sel.split(" | ")[0])
        if st.sidebar.button("🗑️ Excluir"):
            sh.get_worksheet(0).delete_rows(linha)
            st.cache_data.clear(); st.rerun()
        if st.sidebar.button("✅ Quitar"):
            sh.get_worksheet(0).update_cell(linha, 6, "Pago")
            st.cache_data.clear(); st.rerun()
