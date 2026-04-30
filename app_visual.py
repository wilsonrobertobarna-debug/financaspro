import streamlit as st
import pandas as pd
from datetime import date

# Configuração da página
st.set_page_config(
    page_title="FinançasPro",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Estilização limpa e minimalista
st.markdown("""
    <style>
    .version-tag {
        position: fixed;
        top: 10px;
        left: 10px;
        font-family: sans-serif;
        font-size: 10px;
        color: #7f8c8d;
        z-index: 1000;
    }
    .stButton>button {
        border-radius: 4px;
        border: 1px solid #bdc3c7;
        background-color: #ffffff;
        color: #333333;
    }
    .stButton>button:hover {
        border-color: #3498db;
        color: #3498db;
    }
    </style>
""", unsafe_allow_html=True)

# Exibe a versão atual do sistema no topo
st.markdown('<div class="version-tag">Versão 1</div>', unsafe_allow_html=True)

# Título do aplicativo
st.title("FinançasPro")
st.markdown("---")

# Inicialização do estado das transações na sessão
if "transacoes" not in st.session_state:
    st.session_state.transacoes = pd.DataFrame(columns=[
        "Data", "Tipo", "Valor", "Descrição", "Centro de Custo", "Beneficiário"
    ])

# Navegação por abas para manter o layout limpo
aba_dashboard, aba_lancamentos, aba_metas, aba_sistema = st.tabs([
    "Dashboard", "Lançamentos", "Metas", "Gerenciamento"
])

with aba_dashboard:
    st.subheader("Resumo Financeiro")
    
    if st.session_state.transacoes.empty:
        st.info("Nenhuma transação registrada no momento.")
    else:
        st.dataframe(st.session_state.transacoes, use_container_width=True)
        
        # Totalizadores
        total_despesas = st.session_state.transacoes[
            st.session_state.transacoes["Tipo"] == "Despesa"
        ]["Valor"].sum()
        
        total_outros = st.session_state.transacoes[
            st.session_state.transacoes["Tipo"] == "Outros"
        ]["Valor"].sum()
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total de Despesas", f"R$ {total_despesas:,.2f}")
        with col2:
            st.metric("Total de Outros", f"R$ {total_outros:,.2f}")

with aba_lancamentos:
    st.subheader("Lançar Nova Transação")
    
    with st.form("form_lancamento"):
        c1, c2 = st.columns(2)
        
        with c1:
            # Data sincronizada com o sistema operacional
            data_lancamento = st.date_input("Data", value=date.today())
            
            # Tipo de transação sem o botão de rendimentos
            tipo_lancamento = st.selectbox("Tipo de Lançamento", ["Despesa", "Outros"])
            
            # Valor em Reais
            valor_lancamento = st.number_input("Valor (R$)", min_value=0.0, step=0.01, format="%.2f")
            
        with c2:
            descricao = st.text_input("Descrição")
            centro_custo = st.text_input("Centro de Custo")
            beneficiario = st.text_input("Beneficiário")
            
        submit = st.form_submit_button("Adicionar Transação")
        
        if submit:
            nova_linha = pd.DataFrame([{
                "Data": data_lancamento,
                "Tipo": tipo_lancamento,
                "Valor": valor_lancamento,
                "Descrição": descricao,
                "Centro de Custo": centro_custo,
                "Beneficiário": beneficiario
            }])
            
            st.session_state.transacoes = pd.concat([st.session_state.transacoes, nova_linha], ignore_index=True)
            st.success("Transação adicionada com sucesso!")
            st.rerun()

with aba_metas:
    st.subheader("Acompanhamento de Metas")
    
    metas_map = {
        "Alimentação": 1500.00,
        "Moradia": 2500.00,
        "Transporte": 600.00
    }
    
    df_metas_graph = pd.DataFrame({
        'Categoria': ['Alimentação', 'Moradia', 'Transporte', 'Lazer'],
        'Valor': [1200.00, 2400.00, 450.00, 300.00]
    })
    
    # Linha corrigida sem o ponto final
    df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map)
    
    st.dataframe(df_metas_graph, use_container_width=True)

with aba_sistema:
    st.subheader("Configurações do Sistema")
    st.write("Gerencie os dados e os parâmetros do aplicativo.")
    
    if st.button("Limpar todos os registros"):
        st.session_state.transacoes = pd.DataFrame(columns=[
            "Data", "Tipo", "Valor", "Descrição", "Centro de Custo", "Beneficiário"
        ])
        st.success("Dados limpos com sucesso!")
        st.rerun()
