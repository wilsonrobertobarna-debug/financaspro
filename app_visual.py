import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date
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

# 2. CONEXÃO E CARREGAMENTO
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", ttl=0)
        if df is not None:
            # Garante que a coluna Valor seja número para o gráfico não quebrar
            df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
            return df
        return pd.DataFrame()
    except:
        return pd.DataFrame()

df_g = carregar_dados()

# 3. BARRA LATERAL
with st.sidebar:
    st.title("🐾 FinançasPro")
    st.write(f"Wilson Roberto Barnabé")
    if not df_g.empty:
        total_desp = df_g[df_g['Tipo'].str.contains("Despesa", na=False)]['Valor'].sum()
        st.metric("Total Gasto", f"R$ {total_desp:,.2f}")
    if st.button("Sair"):
        st.session_state.autenticado = False
        st.rerun()

# 4. INTERFACE PRINCIPAL
st.markdown("<h2 style='text-align: center; color: #2E86C1;'>Controle Financeiro</h2>", unsafe_allow_html=True)
t1, t2, t3, t4 = st.tabs(["💰 Lançar", "✅ Baixas", "📊 Gráficos", "📋 Extrato"])

with t1:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", date.today())
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita"], horizontal=True)
        
        c3, c4 = st.columns(2)
        benef = c3.text_input("Beneficiário:")
        valor = c4.number_input("Valor:", 0.0)
        
        c5, c6 = st.columns(2)
        cat = c5.selectbox("Categoria:", ["Mercado", "Ração", "Combustível", "Saúde", "Lazer", "Outros"])
        status = c6.selectbox("Status:", ["⏳ Pendente", "✅ Pago"])
        
        if st.button("🚀 GRAVAR REGISTRO", use_container_width=True):
            novo = pd.DataFrame([{
                "Data": dt_l.strftime('%d/%m/%Y'),
                "Tipo": tipo,
                "Categoria": cat,
                "Valor": valor,
                "Beneficiário": benef,
                "Status": status
            }])
            df_final = pd.concat([df_g, novo], ignore_index=True)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", data=df_final)
            st.success("✅ Gravado!")
            st.rerun()

with t2:
    st.subheader("Contas Pendentes")
    if not df_g.empty:
        pendentes = df_g[df_g['Status'] == "⏳ Pendente"]
        if not pendentes.empty:
            st.dataframe(pendentes, use_container_width=True)
        else:
            st.success("Tudo pago! Nenhuma pendência.")

with t3:
    if not df_g.empty:
        despesas = df_g[df_g['Tipo'].str.contains("Despesa", na=False)]
        if not despesas.empty:
            fig = px.pie(despesas, values='Valor', names='Categoria', title='Distribuição de Gastos')
            st.plotly_chart(fig, use_container_width=True)

with t4:
    st.subheader("Histórico Completo")
    st.dataframe(df_g, use_container_width=True, height=500)
