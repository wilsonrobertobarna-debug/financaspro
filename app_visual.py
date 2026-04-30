import streamlit as st
from datetime import datetime

# Configuração da página e layout minimalista
st.set_page_config(
    page_title="FinançasPro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Exibição da versão no topo esquerdo
st.markdown("### FinançasPro - Versão 2.0.11")
st.markdown("---")

# Inicializa o estado da sessão para armazenar transações
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = []

# Formulário de Nova Transação
st.subheader("Nova Transação")

with st.form("transaction_form"):
    # Puxa a data do sistema operacional
    current_date = datetime.now().date()
    
    description = st.text_input("Descrição")
    value = st.number_input("Valor (R$)", step=0.01, format="%.2f")
    cost_center = st.text_input("Centro de Custo")
    beneficiary = st.text_input("Beneficiário")
    date = st.date_input("Data", value=current_date)
    
    # Botão minimalista para envio
    submit_button = st.form_submit_button(label="Adicionar Transação")
    
    if submit_button:
        # Validação básica dos campos
        if description and value > 0 and cost_center and beneficiary:
            st.session_state['transactions'].append({
                "Descrição": description,
                "Valor": f"R$ {value:.2f}",
                "Centro de Custo": cost_center,
                "Beneficiário": beneficiary,
                "Data": date.strftime("%d/%m/%Y")
            })
            st.success("Transação adicionada com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos antes de continuar.")

# Área de Visualização
st.markdown("---")
st.subheader("Transações Recentes")

if st.session_state['transactions']:
    for index, t in enumerate(reversed(st.session_state['transactions'])):
        st.markdown(
            f"**{t['Descrição']}**\n"
            f"- Valor: {t['Valor']} | Data: {t['Data']}\n"
            f"- Centro de Custo: {t['Centro de Custo']} | Beneficiário: {t['Beneficiário']}"
        )
        st.markdown("")
else:
    st.info("Nenhuma transação registrada no momento.")
