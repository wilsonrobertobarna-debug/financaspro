import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.express as px

# Configuração da Página
st.set_page_config(page_title="FinançasPro - Wilson", layout="wide")

# Título Principal
st.markdown("<h1 style='text-align: center; color: #2E7D32;'>💰 FinançasPro - Wilson</h1>", unsafe_allow_html=True)
st.divider()

# Conexão com Google Sheets (Puxa tudo do Secrets)
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    return conn.read(worksheet="LANCAMENTOS", ttl="0")

def salvar_dados(df_novo):
    conn.update(worksheet="LANCAMENTOS", data=df_novo)
    st.cache_data.clear()

# Carregamento Inicial
try:
    df_atual = carregar_dados()
except Exception as e:
    st.error("Erro ao conectar na Planilha. Verifique os Secrets.")
    st.stop()

# --- MENU LATERAL ---
aba = st.sidebar.radio("Navegação", ["Lançar Dados", "Extrato & Gráficos"])

if aba == "Lançar Dados":
    st.subheader("📝 Novo Lançamento")
    
    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            data = st.date_input("Data")
            valor = st.number_input("Valor (R$)", min_value=0.0, step=0.01)
            tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        with col2:
            categoria = st.text_input("Categoria (Ex: Mercado, Salário)")
            descricao = st.text_input("Descrição")
            banco = st.selectbox("Banco/Cartão", ["NuBank", "Itaú", "Inter", "Dinheiro"])
        
        btn_gravar = st.form_submit_button("🚀 GRAVAR NO GOOGLE SHEETS")

    if btn_gravar:
        novo_registro = pd.DataFrame([{
            "DATA": data.strftime("%d/%m/%Y"),
            "VALOR": valor if tipo == "Receita" else -valor,
            "CATEGORIA": categoria,
            "DESCRICAO": descricao,
            "BANCO": banco,
            "TIPO": tipo
        }])
        
        df_final = pd.concat([df_atual, novo_registro], ignore_index=True)
        salvar_dados(df_final)
        st.success("✅ Lançamento gravado com sucesso!")
        st.balloons()

elif aba == "Extrato & Gráficos":
    st.subheader("📊 Resumo Financeiro")
    
    if not df_atual.empty:
        # Cálculos Rápidos
        receitas = df_atual[df_atual['VALOR'] > 0]['VALOR'].sum()
        despesas = df_atual[df_atual['VALOR'] < 0]['VALOR'].sum()
        saldo = receitas + despesas
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receitas", f"R$ {receitas:,.2f}")
        c2.metric("Despesas", f"R$ {abs(despesas):,.2f}", delta_color="inverse")
        c3.metric("Saldo Atual", f"R$ {saldo:,.2f}")
        
        st.divider()
        
        # Tabela e Gráfico
        col_tab, col_gra = st.columns([1.2, 1])
        with col_tab:
            st.write("📋 Últimos Lançamentos")
            st.dataframe(df_atual.sort_index(ascending=False), use_container_width=True)
        
        with col_gra:
            st.write("💡 Despesas por Categoria")
            df_gastos = df_atual[df_atual['VALOR'] < 0]
            if not df_gastos.empty:
                fig = px.pie(df_gastos, values=abs(df_gastos['VALOR']), names='CATEGORIA', hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Nenhum dado encontrado na planilha.")
