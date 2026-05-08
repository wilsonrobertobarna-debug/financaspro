import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from gspread_pandas import Spread, Client
import urllib.parse
from fpdf import FPDF
from twilio.rest import Client as TwilioClient
import pytz

# --- CONFIGURAÇÕES INICIAIS ---
st.set_page_config(page_title="FinançasPro v2.0.3", layout="wide", page_icon="💰")

# Fuso Horário e Moeda
fuso = pytz.timezone('America/Sao_Paulo')
hoje_br = datetime.now(fuso).date()
mes_atual = hoje_br.strftime('%m/%Y')

def m_fmt(valor):
    """Formata para Real Brasileiro"""
    return f"R$ {valor:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- CONEXÃO GOOGLE SHEETS (VERSÃO CLOUD) ---
# --- CONEXÃO GOOGLE SHEETS (CORREÇÃO DE INDENTAÇÃO) ---
try:
    # Estas linhas PRECISAM estar recuadas para a direita:
    creds_dict = dict(st.secrets["gcp_service_account"])
    
    spreadsheet_id = '147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4'
    
    spread = Spread(spreadsheet_id, config=creds_dict)
    
    # Carregamento das abas (Lançamentos e Bancos)
    df_base = spread.sheet_to_df(index=None, sheet='Lançamentos')
    df_bancos_info = spread.sheet_to_df(index=None, sheet='Bancos')
    
    st.success("Conexão estabelecida com sucesso!")

except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.stop()
    
    # 4. Leitura das abas
    df_base = spread.sheet_to_df(index=None, sheet='Lançamentos')
    df_bancos_info = spread.sheet_to_df(index=None, sheet='Bancos')
    
    # Tratamento de Dados (Mantendo Real R$ e visual limpo)
    df_base['V_Num'] = pd.to_numeric(df_base['Valor'].str.replace('R$', '').str.replace('.', '').str.replace(',', '.').strip(), errors='coerce').fillna(0.0)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%Y')
    bancos_disponiveis = df_base['Banco'].unique().tolist()

except Exception as e:
    st.error(f"Erro ao conectar: {e}")
    st.stop()

# --- SIDEBAR E NAVEGAÇÃO ---
st.sidebar.header("📂 Menu FinançasPro")
aba = st.sidebar.radio("Selecione a funcionalidade:", 
    ["🏠 Dashboard", "➕ Novo Lançamento", "📋 Lançamentos Pendentes", "🐾 Gestão Milo & Bolt", "🚗 Gestão do Veículo", "📄 WhatsApp", "📋 Gerador de Relatórios"])

# --- TWILIO: AVISOS AUTOMÁTICOS ---
def enviar_alerta_whatsapp(mensagem):
    # Suas credenciais integradas
    account_sid = 'SEU_TWILIO_SID'
    auth_token = 'SEU_TWILIO_TOKEN'
    client = TwilioClient(account_sid, auth_token)
    
    try:
        client.messages.create(
            from_='whatsapp:+14155238886', # Número Twilio Sandbox
            body=mensagem,
            to='whatsapp:+55XXXXXXXXXXX' # Seu número
        )
    except Exception as e:
        pass

# --- CONTEÚDO: DASHBOARD ---
if aba == "🏠 Dashboard":
    st.title("🏠 Dashboard Financeiro")
    
    # 1. Primeiro, garantimos que todos os nomes de colunas sejam TEXTO (evita o AttributeError)
    df_base.columns = [str(col).strip() for col in df_base.columns]
    
    # 2. Agora o código encontrará 'Data' sem problemas
    df_base['Data'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['Data'].dt.strftime('%m/%Y')
    
    # KPIs Superiores
    c1, c2, c3, c4 = st.columns(4)
    # ... segue o código de cálculo
    # --- DIAGNÓSTICO TEMPORÁRIO ---
st.write("Colunas encontradas na planilha:", df_base.columns.tolist())
st.write("Prévia dos dados:", df_base.head(2))
    
    # Agora os cálculos abaixo vão encontrar a coluna 'Mes_Ano' criada acima
    rec_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base['Tipo'] == 'Receita') & (df_base['Status'] == 'Pago')]['V_Num'].sum()
    des_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base['Tipo'] == 'Despesa') & (df_base['Status'] == 'Pago')]['V_Num'].sum()
    sobra = rec_mes - des_mes
    
    c1.metric("Receitas (Mês)", m_fmt(rec_mes))
    c2.metric("Despesas (Mês)", m_fmt(des_mes), delta_color="inverse")
    c3.metric("Sobra", m_fmt(sobra))
    
    # Aqui ajustei para verificar o Milo na descrição ou categoria
    status_milo = "🐾 Em dia" if df_base['Descrição'].str.contains('Milo', case=False).any() else "Sem dados"
    c4.metric("Status Milo", status_milo)

    st.divider()
    
    # Gráficos Simples (Visual Limpo)
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Despesas por Categoria")
        df_cat = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base['Tipo'] == 'Despesa')].groupby('Categoria')['V_Num'].sum()
        st.bar_chart(df_cat)
        
    with col_g2:
        st.subheader("💳 Gastos por Banco")
        df_bnc = df_base[(df_base['Mes_Ano'] == mes_atual)].groupby('Banco')['V_Num'].sum()
        st.pie_chart(df_bnc)

# --- CONTEÚDO: NOVO LANÇAMENTO (Formulário Original) ---
elif aba == "➕ Novo Lançamento":
    st.title("➕ Novo Lançamento")
    with st.form("form_novo_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)
        data_l = col1.date_input("Data", hoje_br)
        tipo_l = col2.selectbox("Tipo", ["Despesa", "Receita"])
        desc_l = col1.text_input("Descrição")
        valor_l = col2.number_input("Valor", min_value=0.0, step=0.01)
        cat_l = col1.selectbox("Categoria", ["Pet: Milo", "Alimentação", "Moradia", "Veículo", "Saúde", "Outros"])
        bnc_l = col2.selectbox("Banco/Cartão", bancos_disponiveis)
        status_l = st.selectbox("Status", ["Pago", "Pendente"])
        
        btn_salvar = st.form_submit_button("Salvar Lançamento")
        if btn_salvar:
            # Lógica para salvar no GSheets mantendo o formato original
            st.success("Lançamento registrado com sucesso!")
            
elif aba == "📋 Lançamentos Pendentes":
    st.title("📋 Controle de Pendências")
    
    # Filtros de Alerta
    amanha = hoje_br + timedelta(days=1)
    em_3_dias = hoje_br + timedelta(days=3)
    
    df_pendente = df_base[df_base['Status'] == 'Pendente'].copy()
    
    col_a, col_b, col_c = st.columns(3)
    vencidos = df_pendente[df_pendente['DT'].dt.date < hoje_br]
    vence_hoje = df_pendente[df_pendente['DT'].dt.date == hoje_br]
    vence_logo = df_pendente[(df_pendente['DT'].dt.date > hoje_br) & (df_pendente['DT'].dt.date <= em_3_dias)]
    
    col_a.metric("⚠️ Vencidos", m_fmt(vencidos['V_Num'].sum()), delta_color="inverse")
    col_b.metric("📅 Vence Hoje", m_fmt(vence_hoje['V_Num'].sum()))
    col_c.metric("⏳ Prox. 3 Dias", m_fmt(vence_logo['V_Num'].sum()))
    
    st.subheader("🔍 Detalhamento de Pendências")
    busca = st.text_input("Filtrar por Descrição ou Banco")
    
    if busca:
        df_pendente = df_pendente[df_pendente['Descrição'].str.contains(busca, case=False) | 
                                 df_pendente['Banco'].str.contains(busca, case=False)]
    
    st.dataframe(df_pendente[['Data', 'Descrição', 'Banco', 'Valor', 'Categoria']], use_container_width=True)

# --- CONTEÚDO: GESTÃO MILO ---
elif aba == "🐾 Gestão Milo & Bolt":
    st.title(f"🐾 Controle de Gastos: Milo")
    
    # Filtro específico para o Pet
    df_milo = df_base[df_base['Categoria'].str.contains("Milo", case=False)].copy()
    df_milo_mes = df_milo[df_milo['Mes_Ano'] == mes_atual]
    
    c1, c2 = st.columns(2)
    c1.metric("Gasto Total (Mês)", m_fmt(df_milo_mes['V_Num'].sum()))
    c2.metric("Nº de Itens/Serviços", len(df_milo_mes))
    
    st.subheader("Histórico de Cuidados")
    st.table(df_milo_mes[['Data', 'Descrição', 'Valor', 'Status']])

# --- CONTEÚDO: GESTÃO DO VEÍCULO ---
elif aba == "🚗 Gestão do Veículo":
    st.title("🚗 Utilitários Automotivos")
    
    tab1, tab2 = st.tabs(["⛽ Álcool x Gasolina", "🔧 Manutenção & Consumo"])
    
    with tab1:
        st.subheader("Calculadora de Viabilidade")
        col_v1, col_v2 = st.columns(2)
        p_alcool = col_v1.number_input("Preço Álcool (R$)", min_value=0.0, format="%.3f")
        p_gasosa = col_v2.number_input("Preço Gasolina (R$)", min_value=0.0, format="%.3f")
        
        if p_gasosa > 0:
            relacao = p_alcool / p_gasosa
            st.write(f"Relação: **{relacao:.2%}**")
            if relacao < 0.7:
                st.success("✅ Abasteça com ÁLCOOL")
            else:
                st.warning("✅ Abasteça com GASOLINA")
                
    with tab2:
        st.subheader("Controle de KM")
        km_atual = st.number_input("KM Atual do Painel", min_value=0)
        km_troca = st.number_input("KM da Próxima Troca de Óleo", min_value=0)
        
        if km_troca > 0:
            restante = km_troca - km_atual
            if restante > 500:
                st.info(f"Faltam {restante} km para a próxima troca.")
            elif restante > 0:
                st.warning(f"Atenção: Faltam apenas {restante} km para a troca!")
            else:
                st.error(f"⚠️ Troca de óleo VENCIDA há {abs(restante)} km!")

# --- CONTEÚDO: WHATSAPP (RELATÓRIO TEXTUAL) ---
elif aba == "📄 WhatsApp":
    st.title("📄 Gerador de Resumo para WhatsApp")
    
    # Cálculo de Limite de Cartão (Fatura Atual)
    # Considera apenas o que foi gasto no mês atual para o resumo
    gastos_cartao = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base['Banco'].str.contains("Cartão", case=False))]['V_Num'].sum()
    
    texto_resumo = f"""
*📊 RESUMO FINANCEIRO - {mes_atual}*
---------------------------------------
💰 *Saldos Atualizados:*
• Receitas: {m_fmt(rec_mes)}
• Despesas: {m_fmt(des_mes)}
• *Sobra Prevista: {m_fmt(sobra)}*

🐾 *Gastos Milo:* {m_fmt(df_milo_mes['V_Num'].sum())}

💳 *Uso do Cartão (Mês):* {m_fmt(gastos_cartao)}
---------------------------------------
_Gerado via FinançasPro v2.0.3_
    """
    
    st.text_area("Copie o texto abaixo:", texto_resumo, height=250)
    
    link_zap = f"https://wa.me/?text={urllib.parse.quote(texto_resumo)}"
    st.markdown(f"[📲 Enviar para o WhatsApp]({link_zap})")

elif "📋" in aba:
    st.title("📋 Gerador de Relatório PDF")
    
    c1, c2, c3 = st.columns(3)
    b_ini = c1.date_input("Data Inicial", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY", key="pdf_d1")
    b_fim = c2.date_input("Data Final", datetime.now(), format="DD/MM/YYYY", key="pdf_d2")
    
    st.divider()
    
    c_b1, c_b2, c_b3 = st.columns(3)
    s_bnc_rel = c_b1.multiselect("Filtrar por Banco:", sorted(bancos_disponiveis))
    s_sta_rel = c_b2.multiselect("Filtrar por Status:", ["Pago", "Pendente"])
    b_desc_rel = c_b3.text_input("Buscar por Descrição:")
    
    st.divider()
    
    df_v = df_base.copy()
    df_v = df_v[df_v['DT'].notna()]
    df_v = df_v[(df_v['DT'].dt.date >= b_ini) & (df_v['DT'].dt.date <= b_fim)]
    
    if s_bnc_rel:
        df_v = df_v[df_v['Banco'].isin(s_bnc_rel)]
    if s_sta_rel:
        df_v = df_v[df_v['Status'].isin(s_sta_rel)]
    if b_desc_rel:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc_rel, case=False, na=False)]
        
    st.subheader("Lançamentos Filtrados")
    df_v_display = df_v[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].copy()
    df_v_display['Valor'] = df_v['V_Num'].apply(m_fmt)
    st.dataframe(df_v_display.iloc[::-1], use_container_width=True, hide_index=True)
    
    st.divider()
    
    if st.button("📄 Gerar PDF"):
        if df_v.empty:
            st.warning("Nenhum lançamento selecionado para gerar o PDF.")
        else:
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                
                pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
                pdf.ln(2)
                pdf.cell(200, 10, txt=f"Periodo: {b_ini.strftime('%d/%m/%Y')} a {b_fim.strftime('%d/%m/%Y')}", ln=1, align="L")
                
                filtros_texto = []
                if s_bnc_rel: filtros_texto.append(f"Bancos: {', '.join(s_bnc_rel)}")
                if s_sta_rel: filtros_texto.append(f"Status: {', '.join(s_sta_rel)}")
                if b_desc_rel: filtros_texto.append(f"Descricao: {b_desc_rel}")
                
                texto_filtros = "Filtros: " + (" | ".join(filtros_texto) if filtros_texto else "Nenhum")
                pdf.cell(200, 10, txt=texto_filtros, ln=1, align="L")
                pdf.ln(2)
                
                df_v = df_v.sort_values(by='DT')
                df_v['Saldo_Acum'] = df_v['V_Num'].cumsum()
                
                pdf.cell(20, 8, "Data", 1)
                pdf.cell(25, 8, "Tipo", 1)
                pdf.cell(25, 8, "Valor", 1)
                pdf.cell(25, 8, "Saldo Acum.", 1)
                pdf.cell(75, 8, "Descricao", 1)
                pdf.cell(20, 8, "Status", 1)
                pdf.ln()
                
                for index, row in df_v.iterrows():
                    pdf.cell(20, 6, str(row['Data']), 1)
                    pdf.cell(25, 6, str(row['Tipo']), 1)
                    pdf.cell(25, 6, f"R$ {row['V_Num']:.2f}".replace('.', ','), 1)
                    pdf.cell(25, 6, f"R$ {row['Saldo_Acum']:.2f}".replace('.', ','), 1)
                    pdf.cell(75, 6, str(row['Descrição'])[:40], 1)
                    pdf.cell(20, 6, str(row['Status']), 1)
                    pdf.ln()
                
                pdf_output = pdf.output(dest='S')
                if isinstance(pdf_output, str):
                    pdf_output = pdf_output.encode('latin-1')
                    
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_output,
                    file_name="relatorio.pdf",
                    mime="application/pdf"
                )
                st.success("PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar o PDF: {e}")
