import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configuração da página
st.set_page_config(page_title="FinançasPro", layout="wide")

# Inicialização do estado de sessão
if "lancamentos" not in st.session_state:
    st.session_state["lancamentos"] = []

st.title("FinançasPro - Sistema de Gestão Financeira")
st.write("Gerencie suas finanças de forma simples e organizada.")

# ==========================================
# 1. Formulário de Cadastro (Estrutura Mantida)
# ==========================================
st.sidebar.header("Adicionar Lançamento")

with st.sidebar.form(key="form_lancamento", clear_on_submit=True):
    descricao = st.text_input("Descrição")
    valor = st.number_input("Valor (R$)", value=0.00, step=0.01)
    tipo = st.selectbox("Tipo", ["Receita", "Despesa"])
    categoria = st.selectbox("Centro de Custo / Categoria", ["Alimentação", "Moradia", "Transporte", "Outros"])
    data = st.date_input("Data do Lançamento", datetime.now())
    status = st.selectbox("Status", ["Pago", "Pendente"])
    
    submit_button = st.form_submit_button(label="Salvar Lançamento")
    
    if submit_button:
        if descricao and valor > 0:
            novo_lancamento = {
                "Data": data.strftime("%d/%m/%Y"),
                "Descrição": descricao,
                "Valor": valor,
                "Tipo": tipo,
                "Categoria": categoria,
                "Status": status
            }
            st.session_state["lancamentos"].append(novo_lancamento)
            st.success("Lançamento adicionado com sucesso!")
        else:
            st.error("Preencha a descrição e defina um valor maior que zero.")

# ==========================================
# 2. Lançamentos e Pesquisa
# ==========================================
st.header("Lançamentos Registrados")

col1, col2 = st.columns(2)
with col1:
    busca_descricao = st.text_input("Filtrar por descrição")
with col2:
    busca_status = st.selectbox("Filtrar por status", ["Todos", "Pago", "Pendente"])

# Exibição dos lançamentos e filtros
if st.session_state["lancamentos"]:
    df = pd.DataFrame(st.session_state["lancamentos"])
    
    # Aplicação dos filtros
    df_filtrado = df.copy()
    if busca_descricao:
        df_filtrado = df_filtrado[df_filtrado["Descrição"].str.contains(busca_descricao, case=False, na=False)]
    if busca_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado["Status"] == busca_status]
        
    st.dataframe(df_filtrado, use_container_width=True)
else:
    st.info("Nenhum lançamento registrado no momento.")

# ==========================================
# 3. Área de Relatórios e Exportação PDF
# ==========================================
st.header("Gerar Relatório")

def gerar_pdf(dataframe):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    elements = []
    
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.HexColor('#1E3D59')
    )
    elements.append(Paragraph("Relatório de Lançamentos - FinançasPro", title_style))
    elements.append(Spacer(1, 10))
    
    if not dataframe.empty:
        data_table = [["Data", "Descrição", "Valor", "Tipo", "Categoria", "Status"]]
        for index, row in dataframe.iterrows():
            data_table.append([
                str(row['Data']),
                str(row['Descrição']),
                f"R$ {row['Valor']:.2f}",
                str(row['Tipo']),
                str(row['Categoria']),
                str(row['Status'])
            ])
            
        t = Table(data_table, colWidths=[80, 180, 80, 70, 90, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1E3D59')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F2F2F2')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
        ]))
        elements.append(t)
    else:
        elements.append(Paragraph("Nenhum dado encontrado para o relatório.", styles['Normal']))
        
    doc.build(elements)
    buffer.seek(0)
    return buffer

if st.session_state["lancamentos"]:
    df_all = pd.DataFrame(st.session_state["lancamentos"])
    pdf_file = gerar_pdf(df_all)
    
    st.download_button(
        label="📄 Baixar Relatório em PDF",
        data=pdf_file,
        file_name="relatorio_financas_financaspro.pdf",
        mime="application/pdf"
    )
else:
    st.warning("Adicione pelo menos um lançamento para habilitar a geração do PDF.")
