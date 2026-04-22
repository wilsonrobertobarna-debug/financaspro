import streamlit as st
import pandas as pd
from datetime import date, timedelta
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO E LOGIN
st.set_page_config(page_title="FinançasPro Wilson V601", layout="wide")

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("🔐 Acesso FinançasPro")
        senha = st.text_input("Senha:", type="password")
        if st.button("Entrar"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Incorreta!")
    st.stop()

# 2. CONEXÃO COM O GOOGLE
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados(aba):
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet=aba, ttl=0)
        return df if df is not None else pd.DataFrame()
    except:
        return pd.DataFrame()

# Carregando as informações
df_g = carregar_dados("LANCAMENTOS")
df_b = carregar_dados("BANCOS")

# 3. INTERFACE WILSON V601
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson</h1>", unsafe_allow_html=True)

# Aqui as abas voltam a existir!
t1, t2, t3, t4 = st.tabs(["💰 Lançar", "✅ Baixas", "📊 Gráficos", "📋 Extrato"])

with t1:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", date.today())
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita", "💎 Rendimento"], horizontal=True)
        
        c3, c4 = st.columns(2)
        benef = c3.text_input("Beneficiário:")
        valor = c4.number_input("Valor:", 0.0)
        
        c5, c6 = st.columns(2)
        cat = c5.selectbox("Categoria:", ["Mercado", "Ração", "Combustível", "Saúde", "Lazer", "Outros"])
        conta = c6.selectbox("Conta/Banco:", ["Dinheiro", "Pix", "Conta Corrente"])
        
        status = st.selectbox("Status:", ["⏳ Pendente", "✅ Pago"])
        desc = st.text_area("Descrição:")

        if st.button("🚀 GRAVAR NO GOOGLE", use_container_width=True):
            novo = pd.DataFrame([{
                "Data": dt_l.strftime('%d/%m/%Y'),
                "Tipo": tipo,
                "Categoria": cat,
                "Valor": valor,
                "Pagamento": conta,
                "Beneficiário": benef,
                "Status": status,
                "KM": 0,
                "Descrição": desc
            }])
            df_final = pd.concat([df_g, novo], ignore_index=True)
            try:
                conn.update(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", data=df_final)
                st.success("✅ Gravado com sucesso!")
                st.rerun()
            except:
                st.error("Erro ao gravar. Verifique se a planilha está como EDITOR.")

with t4:
    st.subheader("📋 Extrato Completo")
    st.dataframe(df_g, use_container_width=True)
