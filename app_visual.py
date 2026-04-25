import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff;
        color: white;
        padding: 8px 15px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 20px;
        line-height: 1.2;
    }
    .saldo-container h2 { margin: 0; font-size: 1.8rem; }
    .saldo-container small { font-weight: bold; text-transform: uppercase; font-size: 0.7rem; }
    [data-testid="stMetricValue"] { font-size: 1.3rem !important; }
    .stMetric { background-color: #ffffff; padding: 8px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .economia-texto {
        color: #007bff;
        font-size: 1.1rem;
        font-weight: bold;
        text-align: center;
        margin-top: 15px;
        margin-bottom: 25px;
        padding: 10px;
    }
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

# 3. NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.title("🛡️ FinançasPro")
    
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Colunas e Padronização
        c_tipo = 'Tipo' if 'Tipo' in df.columns else (df.columns[3] if len(df.columns) > 3 else 'Tipo')
        c_cat = 'Categoria' if 'Categoria' in df.columns else (df.columns[2] if len(df.columns) > 2 else 'Categoria')
        c_stat = 'Status' if 'Status' in df.columns else (df.columns[5] if len(df.columns) > 5 else 'Status')
        df[c_tipo] = df[c_tipo].astype(str).str.strip().str.capitalize()
        df[c_stat] = df[c_stat].astype(str).str.strip().str.capitalize()

        # Datas para Gráficos
        df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        mes_atual = datetime.now().strftime('%m/%y')
        
        # Cálculos
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum()
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum()
        rend = df[df[c_cat].astype(str).str.contains('Rendimento', case=False)]['Valor_Num'].sum()
        pend = df[df[c_stat].astype(str).str.contains('Pendente', case=False)]['Valor_Num'].sum()
        saldo = rec - desp
        eco_perc = (saldo / rec * 100) if rec > 0 else 0
        def f_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

        # --- VISUALIZAÇÃO ---
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual em Conta</small><h2>{f_brl(saldo)}</h2></div>', unsafe_allow_html=True)

        t1, t2, t3, t4 = st.columns(4)
        t1.metric("🟢 Receitas", f_brl(rec)); t2.metric("🔴 Despesas", f_brl(desp))
        t3.metric("📈 Rendimentos", f_brl(rend)); t4.metric("⏳ Pendências", f_brl(pend))

        st.markdown(f'<div class="economia-texto">🔹 Economia Real: {f_brl(saldo)} ({eco_perc:.1f}%)</div>', unsafe_allow_html=True)

        # --- HISTÓRICO ---
        st.subheader("📋 Histórico de Lançamentos")
        st.dataframe(df.iloc[::-1], use_container_width=True)

        st.write("---")

        # --- GRÁFICOS ---
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("🍕 Gastos por Categoria (Mês)")
            df_mes = df.copy()
            df_mes['Mes'] = df_mes['Data_DT'].dt.strftime('%m/%y')
            gastos_cat = df_mes[(df_mes['Mes'] == mes_atual) & (df_mes[c_tipo] == 'Despesa')].groupby(c_cat)['Valor_Num'].sum()
            if not gastos_cat.empty:
                st.bar_chart(gastos_cat, color='#ffc107')
            else: st.info("Sem gastos este mês.")

        with g2:
            st.subheader("📊 Receitas x Despesas")
            try:
                df_mes['Mes'] = df_mes['Data_DT'].dt.strftime('%m/%y')
                comp = df_mes.groupby(['Mes', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
                # Forçar cores: Despesa=Vermelho, Receita=Verde
                cores_map = {'Receita': '#28a745', 'Despesa': '#dc3545'}
                cores_list = [cores_map.get(col, '#808080') for col in comp.columns]
                st.bar_chart(comp, color=cores_list)
            except: st.info("Dados insuficientes para o gráfico.")

    # FORMULÁRIO LATERAL
    with st.sidebar.form("f_fin", clear_on_submit=True):
        st.subheader("📝 Lançamento")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", ["Mercado", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
        f_bnc = st.selectbox("Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"])
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, f_bnc, f_stat])
            st.cache_data.clear(); st.rerun()

# Manter as outras abas conforme o código anterior
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets")
    st.dataframe(pd.DataFrame(ws_p.get_all_values()[1:], columns=ws_p.get_all_values()[0]).iloc[::-1], use_container_width=True)
else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo")
    st.dataframe(pd.DataFrame(ws_v.get_all_values()[1:], columns=ws_v.get_all_values()[0]).iloc[::-1], use_container_width=True)
