import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO (PADRÃO WILSON)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 8px 15px;
        border-radius: 10px; text-align: center; margin-bottom: 20px; line-height: 1.1;
    }
    .saldo-container h2 { margin: 0; font-size: 1.8rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e0e0e0; }
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

# 3. CARREGAMENTO DOS CADASTROS (COM TRATAMENTO DE NÚMEROS)
@st.cache_data(ttl=60)
def carregar_cadastros():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        
        # Carrega categorias e limpa a coluna Meta para evitar erro PyArrow
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        if 'Meta' in df_c.columns:
            df_c['Meta'] = pd.to_numeric(df_c['Meta'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0).astype(float)
        else:
            df_c['Meta'] = 0.0
            
        df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
        return df_b, df_c, df_ct
    except:
        return pd.DataFrame(), pd.DataFrame(columns=['Nome', 'Meta']), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_cartoes_cad = carregar_cadastros()

# 4. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    # Título Original com as Patinhas
    st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>🛡️ FinançasPro Wilson</h1><p style='text-align: center; font-size: 1.5rem; margin-top: -10px;'>🐾<br>🐾</p>", unsafe_allow_html=True)
    
    dados_brutos = ws.get_all_values()
    if len(dados_brutos) > 1:
        df_base = pd.DataFrame(dados_brutos[1:], columns=dados_brutos[0])
        df_base.columns = [c.strip() for c in df_base.columns]
        
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        df_base['Valor_Num'] = pd.to_numeric(df_base[c_val].astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0).astype(float)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # Dashboard de Saldo
        s_ini = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if not df_bancos_cad.empty else 0
        rec_t = df_base[df_base[c_tip] == 'Receita']['Valor_Num'].sum()
        desp_t = df_base[df_base[c_tip] == 'Despesa']['Valor_Num'].sum()
        saldo_geral = s_ini + rec_t - desp_t

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Consolidado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        # --- ÁREA DE GRÁFICOS (PROTEGIDA CONTRA ERROS) ---
        st.write("---")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.subheader(f"📊 Metas vs Gasto ({mes_atual})")
            df_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base[c_tip] == 'Despesa')]
            gasto_por_cat = df_mes.groupby(c_cat)['Valor_Num'].sum().reset_index()
            
            df_metas_plot = pd.merge(df_cats_cad[['Nome', 'Meta']], gasto_por_cat, left_on='Nome', right_on=c_cat, how='left').fillna(0.0)
            df_metas_plot = df_metas_plot.rename(columns={'Nome': 'Categoria', 'Meta': 'Meta Planejada', 'Valor_Num': 'Gasto Real'})
            
            # Garante que as colunas são float para o PyArrow não reclamar
            df_metas_plot['Meta Planejada'] = df_metas_plot['Meta Planejada'].astype(float)
            df_metas_plot['Gasto Real'] = df_metas_plot['Gasto Real'].astype(float)
            
            df_metas_plot = df_metas_plot.set_index('Categoria')[['Meta Planejada', 'Gasto Real']]
            df_metas_plot = df_metas_plot[(df_metas_plot['Meta Planejada'] > 0) | (df_metas_plot['Gasto Real'] > 0)]
            
            if not df_metas_plot.empty:
                st.bar_chart(df_metas_plot, horizontal=True, color=['#007bff', '#ff4b4b'])
            else:
                st.info("Aguardando lançamentos ou metas para o gráfico.")

        with col_g2:
            st.subheader("📈 Receita x Despesa")
            if not df_base.empty:
                df_evol = df_base.groupby(['Mes_Ano', c_tip])['Valor_Num'].sum().unstack().fillna(0.0).astype(float)
                st.line_chart(df_evol)

        st.write("---")
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_base.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # FORMULÁRIO DE LANÇAMENTO (ESTRUTURA ORIGINAL MANTIDA)
    with st.sidebar.form("f_original"):
        st.write("### 🚀 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_parc = st.number_input("Qtd Parcelas", min_value=1, value=1)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        
        bancos = df_bancos_cad['Nome do Banco'].tolist() if not df_bancos_cad.empty else []
        cartoes = df_cartoes_cad['Nome do Cartão'].tolist() if not df_cartoes_cad.empty else []
        f_bnc = st.selectbox("Banco/Cartão", sorted(bancos + cartoes + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("SALVAR"):
            linhas = []
            for i in range(f_parc):
                dt = f_dat + relativedelta(months=i)
                cat_n = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                linhas.append([dt.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), cat_n, f_tip, f_bnc, f_sta])
            ws.append_rows(linhas)
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    dados_p = ws_p.get_all_values()
    if len(dados_p) > 1:
        df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0])
        st.dataframe(df_p.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_pet"):
        st.write("### ➕ Gasto com Pets")
        p_d = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_o = st.text_input("Descrição/Obs")
        p_v = st.number_input("Valor", min_value=0.0)
        if st.form_submit_button("Salvar Pet"):
            ws_p.append_row([p_d.strftime("%d/%m/%Y"), p_o, str(p_v).replace('.', ',')])
            st.cache_data.clear(); st.rerun()

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    dados_v = ws_v.get_all_values()
    if len(dados_v) > 1:
        df_v = pd.DataFrame(dados_v[1:], columns=dados_v[0])
        st.dataframe(df_v.iloc[::-1], use_container_width=True)
    
    with st.sidebar.form("f_car"):
        st.write("### ➕ Manutenção/KM")
        v_d = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        v_k = st.number_input("Kilometragem", min_value=0)
        v_o = st.text_input("O que foi feito?")
        if st.form_submit_button("Salvar Veículo"):
            ws_v.append_row([v_d.strftime("%d/%m/%Y"), str(v_k), v_o, "0"])
            st.cache_data.clear(); st.rerun()
