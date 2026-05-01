import streamlit as st
from datetime import datetime
import pytz
import pandas as pd

# Configurações da página
st.set_page_config(
    page_title="FinançasPro",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Definir o fuso horário (America/Sao_Paulo para espelhar o sistema)
fuso_sp = pytz.timezone('America/Sao_Paulo')

# Inicializa o session state
if 'lancamentos' not in st.session_state:
    st.session_state['lancamentos'] = []

if 'pendencias' not in st.session_state:
    st.session_state['pendencias'] = []

# --- Funções Auxiliares ---
def obter_data_atual():
    """Retorna a data atual respeitando o fuso horário correto."""
    return datetime.now(fuso_sp).date()

# --- Sidebar ---
with st.sidebar:
    # Versão no canto superior esquerdo
    st.markdown("<h6 style='text-align: left; margin: 0;'>Versão 1.0.0</h6>", unsafe_allow_html=True)
    st.markdown("---")
    
    pagina = st.selectbox(
        "Menu",
        ["Dashboard", "Lançamentos", "Finanças", "Bancos", "Pendências"]
    )

# --- Lógica de Páginas ---

if pagina == "Dashboard":
    st.title("Dashboard")
    st.write("Acompanhe o resumo financeiro das suas contas.")
    
    df = pd.DataFrame(st.session_state['lancamentos'])
    if not df.empty:
        total_receitas = df[df['tipo'] == 'Receita']['valor'].sum()
        total_despesas = df[df['tipo'] == 'Despesa']['valor'].sum()
        saldo = total_receitas - total_despesas
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Receitas", f"R$ {total_receitas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col2.metric("Despesas", f"R$ {total_despesas:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        col3.metric("Saldo Líquido", f"R$ {saldo:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
    else:
        st.info("Nenhum lançamento registrado no sistema.")

elif pagina == "Lançamentos":
    st.title("Novo Lançamento")
    
    with st.form(key='form_lancamentos'):
        # Data sincronizada com o sistema operacional e fuso horário
        data_lancamento = st.date_input("Data do Lançamento", value=obter_data_atual())
        
        tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
        valor = st.number_input("Valor (R$)", min_value=0.01, step=0.01)
        descricao = st.text_input("Descrição")
        centro_custo = st.text_input("Centro de Custo")
        beneficiario = st.text_input("Beneficiário")
        
        submit_button = st.form_submit_button(label='Salvar Lançamento')
        
        if submit_button:
            novo_lancamento = {
                'data': data_lancamento,
                'tipo': tipo,
                'valor': valor,
                'descricao': descricao,
                'centro_custo': centro_custo,
                'beneficiario': beneficiario,
            }
            st.session_state['lancamentos'].append(novo_lancamento)
            st.success("Lançamento salvo com sucesso!")

elif pagina == "Finanças":
    st.title("Finanças")
    st.write("Gerenciamento do fluxo financeiro do período.")
    
    df = pd.DataFrame(st.session_state['lancamentos'])
    if not df.empty:
        st.dataframe(df.style.format({'valor': 'R$ {:,.2f}'}), use_container_width=True)
    else:
        st.info("Sem transações registradas.")

elif pagina == "Bancos":
    st.title("Bancos")
    st.write("Visão geral das contas bancárias.")
    
    st.info("Nenhuma integração bancária ativa. Adicione contas manuais se necessário.")

elif pagina == "Pendências":
    st.title("Pendências")
    st.write("Controle de contas e pendências atuais.")
    
    hoje = obter_data_atual()
    
    # Filtro de data: impede a exibição adiantada das pendências
    pendencias_do_dia = [p for p in st.session_state['pendencias'] if p['data'] <= hoje]
    
    with st.form(key='form_pendencia'):
        desc_pendencia = st.text_input("Descrição da Pendência")
        vencimento = st.date_input("Vencimento", value=hoje)
        valor_pendencia = st.number_input("Valor da Pendência (R$)", min_value=0.01, step=0.01)
        
        salvar_pendencia = st.form_submit_button("Adicionar Pendência")
        if salvar_pendencia:
            st.session_state['pendencias'].append({
                'descricao': desc_pendencia, 
                'data': vencimento, 
                'valor': valor_pendencia
            })
            st.rerun()
            
    if len(pendencias_do_dia) > 0:
        df_pendencias = pd.DataFrame(pendencias_do_dia)
        st.table(df_pendencias)
    else:
        st.success("Tudo em dia! Não há pendências para o horário atual.")
