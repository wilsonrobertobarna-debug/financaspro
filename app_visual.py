import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO BÁSICA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 20px;
        border-radius: 15px; text-align: center; margin-bottom: 20px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.5rem; }
    .stMetric { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA
@st.cache_resource
def conectar():
    try:
        info = st.secrets["connections"]["gsheets"]
        key = info["private_key"].replace("\\n", "\n").strip()
        creds = Credentials.from_service_account_info({
            "type": info["type"], "project_id": info["project_id"],
            "private_key_id": info["private_key_id"], "private_key": key,
            "client_email": info["client_email"], "token_uri": info["token_uri"],
        }, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
# SUA PLANILHA
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. FUNÇÕES DE TRATAMENTO
@st.cache_data(ttl=60)
def buscar_dados(nome_aba):
    ws = sh.worksheet(nome_aba)
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df.columns = [c.strip() for c in df.columns]
        return df
    return pd.DataFrame()

def p_num(v):
    if not v: return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

# 4. CARREGAR DADOS
df_bancos_cad = buscar_dados("Bancos")
df_cats_cad = buscar_dados("Categoria")

# 5. INTERFACE PRINCIPAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo"])

if aba == "💰 Finanças":
    ws_fin = sh.get_worksheet(0)
    dados = ws_fin.get_all_values()
    df = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
    
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df.empty:
        df.columns = [c.strip() for c in df.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df.columns[0:6]

        # Tratamento de Colunas
        df['V_Num'] = df[c_val].apply(p_num)
        df['DT'] = pd.to_datetime(df[c_dat], dayfirst=True, errors='coerce')
        df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # --- FILTRO DE BUSCA POR BANCO ---
        st.write("### 🔍 Pesquisa")
        bancos_disponiveis = ["Todos"] + sorted(df[c_bnc].unique().tolist())
        banco_filtro = st.selectbox("Escolha um banco para filtrar o resumo:", bancos_disponiveis)
        
        df_filtrado = df if banco_filtro == "Todos" else df[df[c_bnc] == banco_filtro]

        # --- CÁLCULO SALDO GERAL ---
        s_ini = df_bancos_cad['Saldo Inicial'].apply(p_num).sum() if not df_bancos_cad.empty else 0
        df_pago = df[df[c_sta] == 'Pago']
        total_in = df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        total_out = df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_atual = s_ini + total_in - total_out

        # --- MÉTRICAS DO MÊS (Filtradas) ---
        df_m = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        m_in = df_m[df_m[c_tip] == 'Receita']['V_Num'].sum()
        m_out = df_m[df_m[c_tip] == 'Despesa']['V_Num'].sum()
        m_ren = df_m[df_m[c_tip] == 'Rendimento']['V_Num'].sum()
        m_pen = df_m[df_m[c_sta] == 'Pendente']['V_Num'].sum()

        # Dashboard de Valores
        st.markdown(f'<div class="saldo-container"><small>Saldo Real em Conta (Líquido)</small><h2>R$ {saldo_atual:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Receitas", f"R$ {m_in:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        c2.metric("📉 Despesas", f"R$ {m_out:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        c3.metric("💰 Rendimento", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        c4.metric("⏳ Pendente", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        st.write("---")

        # --- SEÇÃO DE GRÁFICOS ---
        g1, g2 = st.columns(2)
        
        with g1:
            st.subheader("🏦 Saldo por Banco")
            lista_bancos = []
            for b in df_bancos_cad['Nome do Banco'].unique():
                ini = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(p_num).sum()
                entradas = df[(df[c_bnc] == b) & (df[c_sta] == 'Pago') & (df[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                saidas = df[(df[c_bnc] == b) & (df[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                lista_bancos.append({'Banco': b, 'Saldo': ini + entradas - saidas})
            
            df_pie = pd.DataFrame(lista_bancos)
            df_pie = df_pie[df_pie['Saldo'] > 0]
            if not df_pie.empty:
                fig = px.pie(df_pie, values='Saldo', names='Banco', hole=.4, color_discrete_sequence=px.colors.qualitative.Pastel)
                st.plotly_chart(fig, use_container_width=True)

        with g2:
            st.subheader("📊 Receitas x Despesas")
            df_evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
            if not df_evol.empty:
                st.bar_chart(df_evol)

        st.write("---")
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_filtrado.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # --- FORMULÁRIO LATERAL ---
    with st.sidebar.form("novo"):
        st.write("### ➕ Novo")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist()))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            for i in range(f_par):
                dt_p = f_dat + relativedelta(months=i)
                desc = f"{f_cat} ({i+1}/{f_par})" if f_par > 1 else f_cat
                ws_fin.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

    st.sidebar.write("---")
    if not df.empty:
        item = st.sidebar.selectbox("Ação rápida:", [""] + [f"{idx+2}|{r[c_cat]}" for idx, r in df.iloc[::-1].head(10).iterrows()])
        if item:
            idx = int(item.split("|")[0])
            if st.sidebar.button("✅ Pagar"):
                ws_fin.update_cell(idx, 6, "Pago")
                st.cache_data.clear(); st.rerun()
            if st.sidebar.checkbox("Excluir?") and st.sidebar.button("🗑️ Apagar"):
                ws_fin.delete_rows(idx)
                st.cache_data.clear(); st.rerun()
