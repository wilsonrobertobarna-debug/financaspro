import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO VISUAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 15px; }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
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
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

# 4. PROCESSAMENTO
if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 5. SIDEBAR (FORMULÁRIO COM BENEFICIÁRIO)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0)
    
    # NOVO CAMPO: Beneficiário
    f_ben = st.text_input("Beneficiário (Quem recebeu/pagou?)")
    
    # Opção de Pet para ajudar na descrição
    pet_ref = ""
    if aba == "🐾 Milo & Bolt":
        pet_ref = st.selectbox("Referente ao Pet:", ["Milo", "Bolt", "Ambos", "Nenhum"])
    
    f_des = st.text_input("Descrição do Gasto (Ex: Ração, Aluguel)")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    
    lista_cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
    if aba == "🐾 Milo & Bolt":
        lista_cats = ["Pet: Milo", "Pet: Bolt", "Geral Pet"]
    
    f_cat = st.selectbox("Categoria", lista_cats)
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR NOVO LANÇAMENTO"):
        ws = sh.get_worksheet(0)
        
        # Monta a descrição inteligente: "Descrição [Beneficiário] (Pet)"
        identificador = f" [{f_ben}]" if f_ben else ""
        pet_info = f" ({pet_ref})" if pet_ref and pet_ref != "Nenhum" else ""
        desc_completa = f"{f_des}{identificador}{pet_info}"
        
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_final = f"{desc_completa} ({i+1}/{int(f_parc)})" if f_parc > 1 else desc_completa
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_final, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 6. CONTEÚDO PRINCIPAL
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        # MÉTRICAS GERAIS
        df_real = df_base[df_base['Status'].str.strip() == 'Pago']
        t_in = df_real[df_real['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        t_out = df_real[df_real['Tipo'] == 'Despesa']['V_Num'].sum()
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0
        
        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {s_ini + t_in - t_out:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # TAGS DO MÊS
        df_mes = df_base[df_base['Mes_Ano'] == mes_atual]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {df_mes[df_mes['Tipo'] == 'Receita']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {df_mes[df_mes['Tipo'] == 'Despesa']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimentos", f"R$ {df_mes[df_mes['Tipo'] == 'Rendimento']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendência", f"R$ {df_mes[df_mes['Status'] == 'Pendente']['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        st.write("---")
        st.subheader("📋 Últimos Lançamentos")
        st.dataframe(df_base.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1].head(15), use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    df_pets = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
    st.info(f"Investimento Total nos Pets: **R$ {df_pets['V_Num'].sum():,.2f}**".replace(',', 'X').replace('.', ',').replace('X', '.'))
    st.dataframe(df_pets.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

# 8. GERENCIADOR DE EXCLUSÃO (BLINDADO COM ID REAL)
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar Registro")
if not df_base.empty:
    df_aux = df_base.copy()
    df_aux['ID_PLANILHA'] = df_aux.index + 2
    
    # Criamos a lista de exclusão com Valor e Descrição para você conferir
    opcoes_excluir = {}
    for _, r in df_aux.tail(15).iloc[::-1].iterrows():
        # Exemplo: L28 | Ração [PetShop] | R$ 150,00
        texto = f"L{r['ID_PLANILHA']} | {r['Descrição']} | R$ {r['Valor']}"
        opcoes_excluir[texto] = r['ID_PLANILHA']
    
    escolha = st.sidebar.selectbox("Apagar (Confira o Valor!):", [""] + list(opcoes_excluir.keys()))
    
    if escolha:
        linha_alvo = opcoes_excluir[escolha]
        if st.sidebar.button("🚨 CONFIRMAR EXCLUSÃO"):
            sh.get_worksheet(0).delete_rows(int(linha_alvo))
            st.sidebar.success(f"Linha {linha_alvo} removida!")
            st.cache_data.clear()
            st.rerun()
