import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 10px 20px; border-radius: 12px; text-align: center; margin-bottom: 10px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .resumo-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-top: 10px; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
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
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
            
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df.columns = [c.strip() for c in df.columns]
            return df_b, df_c, df
        return df_b, df_c, pd.DataFrame()
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

# 4. PROCESSAMENTO
if not df_base.empty:
    for col in ['Data', 'Valor', 'Descrição', 'Categoria', 'Tipo', 'Banco', 'Status']:
        if col not in df_base.columns: df_base[col] = ""
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR - LANÇAMENTO CORRIGIDO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo"):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    f_des = st.text_input("Descrição (Ex: Ração Milo)")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    f_cat = st.selectbox("Categoria", lista_cats)
    
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_p = f"{f_des} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_des
            # ORDEM CRUCIAL: A=Data, B=Valor, C=Descrição, D=Categoria, E=Tipo, F=Banco, G=Status
            ws.append_row([
                dt_p.strftime("%d/%m/%Y"), 
                str(f_val).replace('.', ','), 
                desc_p, 
                f_cat, 
                f_tip, 
                f_bnc, 
                f_sta
            ])
        st.cache_data.clear(); st.rerun()

# 6. CONTEÚDO
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        bancos_unicos = ["Todos"] + sorted(df_base['Banco'].unique().tolist())
        banco_sel = st.selectbox("🔍 Pesquisar por Banco:", bancos_unicos)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base['Banco'] == banco_sel]

        # MÉTRICAS
        df_real_filt = df_filtrado[df_filtrado['Status'].str.strip() != 'Pendente']
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_valor).sum()
        t_in = df_real_filt[df_real_filt['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        t_out = df_real_filt[df_real_filt['Tipo'] == 'Despesa']['V_Num'].sum()
        
        st.markdown(f'<div class="saldo-container"><small>Saldo Realizado ({banco_sel})</small><h2>R$ {s_ini + t_in - t_out:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {df_mes[df_mes['Status'].str.strip() == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.write("---")
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_filtrado.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1].head(15), use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        palavras_chave = 'Milo|Bolt|Pet|Ração|Racao|Vacina|Vet|Banho'
        df_pets = df_base[
            df_base['Categoria'].str.contains(palavras_chave, case=False, na=False) | 
            df_base['Descrição'].str.contains(palavras_chave, case=False, na=False)
        ]
        st.info(f"Investimento Total nos Pets: **R$ {df_pets['V_Num'].sum():,.2f}**".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_pets.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. GERENCIADOR (SINCRONIZADO)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar")
if not df_base.empty:
    df_manag = df_base.copy()
    df_manag['Linha_Planilha'] = df_manag.index + 2
    lista_edit = df_manag.iloc[::-1].head(10)
    
    opcoes = {f"Linha {row['Linha_Planilha']} | {row['Data']} | {row['Descrição']}": row['Linha_Planilha'] for _, row in lista_edit.iterrows()}
    sel = st.sidebar.selectbox("Selecionar para Ação:", [""] + list(opcoes.keys()))
    
    if sel:
        linha_alvo = opcoes[sel]
        col_btn1, col_btn2 = st.sidebar.columns(2)
        if col_btn1.button("🗑️ EXCLUIR"):
            sh.get_worksheet(0).delete_rows(int(linha_alvo))
            st.cache_data.clear(); st.rerun()
        if col_btn2.button("✅ QUITAR"):
            # Coluna 7 é o Status (G)
            sh.get_worksheet(0).
