import streamlit as st
from datetime import datetime

# Configuração da página e layout minimalista
st.set_page_config(
    page_title="FinançasPro",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Exibição da versão no topo esquerdo
st.markdown("### FinançasPro - Versão 2.0.12")
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
    
    col1, col2 = st.columns(2)
    with col1:
        transaction_type = st.selectbox("Tipo", ["Receita", "Despesa"])
    with col2:
        status = st.selectbox("Status", ["Pago", "Pendente"])
        
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
                "Tipo": transaction_type,
                "Valor_Num": value,
                "Valor": f"R$ {value:.2f}",
                "Centro de Custo": cost_center,
                "Beneficiário": beneficiary,
                "Data": date.strftime("%d/%m/%Y"),
                "Status": status
            })
            st.success("Transação adicionada com sucesso!")
        else:
            st.error("Por favor, preencha todos os campos antes de continuar.")

# Cálculos Financeiros
total_receitas = 0.0
total_despesas = 0.0
total_pendente = 0.0

for t in st.session_state['transactions']:
    if t['Tipo'] == "Receita":
        total_receitas += t['Valor_Num']
    elif t['Tipo'] == "Despesa":
        total_despesas += t['Valor_Num']
        
    if t['Status'] == "Pendente":
        total_pendente += t['Valor_Num']

saldo = total_receitas - total_despesas

# Área de Resumo
st.markdown("---")
st.subheader("Resumo Financeiro")

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("Receitas", f"R$ {total_receitas:.2f}")
with c2:
    st.metric("Despesas", f"R$ {total_despesas:.2f}")
with c3:
    st.metric("Saldo", f"R$ {saldo:.2f}")
with c4:
    st.metric("Pendências", f"R$ {total_pendente:.2f}")

# Relatório para WhatsApp
st.markdown("---")
st.subheader("Relatório para WhatsApp")

whatsapp_text = (
    f"📋 *Resumo Financeiro FinançasPro*\n"
    f"------------------------\n"
    f"• *Receitas:* R$ {total_receitas:.2f}\n"
    f"• *Despesas:* R$ {total_despesas:.2f}\n"
    f"• *Saldo:* R$ {saldo:.2f}\n"
    f"• *Pendências:* R$ {total_pendente:.2f}\n\n"
    f"Atualizado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}"
)

# Campo de texto para fácil cópia
st.text_area("Copie o texto abaixo para compartilhar no WhatsApp:", whatsapp_text, height=140)

# Área de Visualização de Transações
st.markdown("---")
st.subheader("Transações Recentes")

if st.session_state['transactions']:
    for t in reversed(st.session_state['transactions']):
        st.markdown(
            f"**{t['Descrição']}** | {t['Tipo']} | Status: {t['Status']}\n"
            f"- Valor: {t['Valor']} | Data: {t['Data']}\n"
            f"- Centro de Custo: {t['Centro de Custo']} | Beneficiário: {t['Beneficiário']}"
        )
        st.markdown("")
else:
    st.info("Nenhuma transação registrada no momento.")
