import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 0. VERSÃO E CONFIGURAÇÃO
VERSION = "2.1.0"
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# ESTILO CSS CUSTOMIZADO
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1rem !important; font-weight: bold !important; color: #666; }
    [data-testid='stMetricValue'] { font-size: 1.2rem !important; font-weight: 800 !important; color: #1E1E1E; }
    .main { background-color: #f8f9fa; }
    </style>
""", unsafe_allow_html=True)

# 1. CONEXÃO E CACHE
@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets.get("connections", {}).get("gsheets")
        if not creds_dict:
            st.error("⚠️ Secrets do GSheets não configurados!"); st.stop()
        
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=[
            "https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"
        ]))
    except Exception as e:
        st.error(f"Erro na conexão: {e}"); st.stop()

# Inicialização de dados
try:
    client = conectar()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws_base = sh.get_worksheet(0)
    ws_bancos = sh.worksheet("Bancos") if "Bancos" in [w.title for w in sh.worksheets()] else None
except Exception as e:
    st.error("Erro ao acessar as abas da planilha."); st.stop()

# 2. FUNÇÕES AUXILIARES
def m_fmt(n): 
    return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def p_float(v):
    try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
    except: return 0.0

def carregar_dados():
    # Base
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame(), pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    
    # Bancos
    df_b = pd.DataFrame()
    if ws_bancos:
        b_dados = ws_bancos.get_all_values()
        if len(b_dados) > 1: df_b = pd.DataFrame(b_dados[1:], columns=b_dados[0])
    
    return df, df_b

# 3. GESTÃO DE ESTADO (SESSION STATE)
if 'df_base' not in st.session_state or st.sidebar.button("🔄 Sincronizar Sheets"):
    st.session_state.df_base, st.session_state.df_bancos = carregar_dados()
    st.toast("Dados atualizados!", icon="✅")

df_base = st.session_state.df_base
df_bancos = st.session_state.df_bancos
bancos_list = df_bancos.iloc[:, 0].tolist() if not df_bancos.empty else ["Carteira", "Inter", "Nubank"]

# 4. SIDEBAR - LANÇAMENTOS
st.sidebar.caption(f"Wilson Finanças v{VERSION}")
aba = st.sidebar.selectbox("Ir para:", ["💰 Dashboard Principal", "📋 Pendências", "🐾 Milo & Bolt", "🚗 Veículo", "📲 Relatórios & Zap"])

with st.sidebar.expander("➕ Novo Registro", expanded=False):
    with st.form("add_form", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet", "Veículo", "Salário", "Investimento", "Outros"])
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_bnc = st.selectbox("Banco", bancos_list)
        f_sta = st.radio("Status", ["Pago", "Pendente"], horizontal=True)
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta, ""])
            st.rerun()

# 5. LÓGICA DAS TELAS
if aba == "💰 Dashboard Principal":
    st.title("🛡️ FinançasPro Wilson")
    
    # Filtro de Mês
    mes_ref = st.selectbox("Mês de Referência:", sorted(df_base['Mes_Ano'].unique(), reverse=True))
    df_mes = df_base[df_base['Mes_Ano'] == mes_ref]
    
    # KPIs
    rec = df_mes[(df_mes['Tipo'].isin(['Receita', 'Rendimento'])) & (df_mes['Status'] == 'Pago')]['V_Num'].sum()
    gas = df_mes[(df_mes['Tipo'] == 'Despesa') & (df_mes['Status'] == 'Pago')]['V_Num'].sum()
    pend = df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 Entradas", m_fmt(rec))
    m2.metric("📉 Saídas", m_fmt(gas))
    m3.metric("⚖️ Sobra", m_fmt(rec - gas))
    m4.metric("⏳ Total Pendente", m_fmt(pend), delta_color="inverse")

    st.divider()
    
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        # Gastos por Categoria
        df_cat_g = df_mes[df_mes['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        fig_pie = px.pie(df_cat_g, values='V_Num', names='Categoria', hole=0.5, title="Distribuição de Gastos")
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_g2:
        # Histórico 6 meses
        df_hist = df_base[df_base['Status'] == 'Pago'].groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        fig_bar = px.bar(df_hist, x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Evolução Mensal")
        st.plotly_chart(fig_bar, use_container_width=True)

elif aba == "📋 Pendências":
    st.title("📋 Lançamentos Pendentes")
    df_p = df_base[df_base['Status'] == 'Pendente'].copy()
    if not df_p.empty:
        st.dataframe(df_p[['Data', 'Descrição', 'Valor', 'Banco', 'Categoria']], use_container_width=True)
    else:
        st.success("Tudo em dia! Nenhuma pendência encontrada.")

elif aba == "🚗 Veículo":
    st.title("🚗 Gestão Automotiva")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("⛽ Álcool vs Gasolina")
        p_alc = st.number_input("Preço Álcool", format="%.3f")
        p_gas = st.number_input("Preço Gasolina", format="%.3f")
        if p_alc > 0 and p_gas > 0:
            ratio = p_alc / p_gas
            if ratio <= 0.7: st.success(f"Vantagem: ÁLCOOL ({ratio:.2%})")
            else: st.warning(f"Vantagem: GASOLINA ({ratio:.2%})")
    
    with c2:
        st.subheader("🔧 Manutenção")
        km_atual = st.number_input("KM Atual", step=100)
        km_troca = st.number_input("KM Última Troca Óleo", step=100)
        if km_atual > 0:
            rodado = km_atual - km_troca
            st.metric("KM Rodados com o óleo", f"{rodado} km", delta=f"{10000-rodado} km p/ troca")

elif aba == "📲 Relatórios & Zap":
    st.title("📲 Gerador de Relatórios")
    texto_relatorio = f"Relatório Wilson - {datetime.now().strftime('%d/%m')}\n"
    texto_relatorio += f"Sobra Mensal: {m_fmt(rec - gas)}\n"
    texto_relatorio += f"Pendências: {m_fmt(pend)}"
    
    st.text_area("Texto formatado:", texto_relatorio, height=150)
    link_zap = f"https://wa.me/?text={urllib.parse.quote(texto_relatorio)}"
    st.markdown(f"[🚀 Enviar para WhatsApp]({link_zap})")
elif "📋" in aba:
        st.title("📋 Gerador de Relatório PDF")
        
        c1, c2, c3 = st.columns(3)
        b_ini = c1.date_input("Data Inicial", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
        b_fim = c2.date_input("Data Final", datetime.now(), format="DD/MM/YYYY")
        
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
                    
                    # Cabeçalho do PDF
                    pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
                    pdf.ln(2)
                    pdf.cell(200, 10, txt=f"Periodo: {b_ini.strftime('%d/%m/%Y')} a {b_fim.strftime('%d/%m/%Y')}", ln=1, align="L")
                    
                    # Exibindo os filtros selecionados logo abaixo do período
                    filtros_texto = []
                    if s_bnc_rel:
                        filtros_texto.append(f"Bancos: {', '.join(s_bnc_rel)}")
                    if s_sta_rel:
                        filtros_texto.append(f"Status: {', '.join(s_sta_rel)}")
                    if b_desc_rel:
                        filtros_texto.append(f"Descrição: {b_desc_rel}")
                    
                    texto_filtros = "Filtros: " + (" | ".join(filtros_texto) if filtros_texto else "Nenhum")
                    pdf.cell(200, 10, txt=texto_filtros, ln=1, align="L")
                    pdf.ln(2)
                    
                    # Ordenar e calcular o saldo acumulado
                    df_v = df_v.sort_values(by='DT')
                    df_v['Saldo'] = df_v['V_Num'].cumsum()
                    
                    # Cabeçalho da tabela (ajustado para caber na largura da página sem quebras)
                    pdf.cell(20, 8, "Data", 1)
                    pdf.cell(25, 8, "Tipo", 1)
                    pdf.cell(25, 8, "Valor", 1)
                    pdf.cell(25, 8, "Saldo Acum.", 1)
                    pdf.cell(75, 8, "Descricao", 1)
                    pdf.cell(20, 8, "Status", 1)
                    pdf.ln()
                    
                    # Linhas da tabela
                    total_valor = 0.0
                    for index, row in df_v.iterrows():
                        pdf.cell(20, 6, str(row['Data']), 1)
                        pdf.cell(25, 6, str(row['Tipo']), 1)
                        pdf.cell(25, 6, f"R$ {row['V_Num']:.2f}".replace('.', ','), 1)
                        
                        # Imprime o saldo apenas na última movimentação do dia
                        if index == df_v[df_v['Data'] == row['Data']].index[-1]:
                            pdf.cell(25, 6, f"R$ {row['Saldo']:.2f}".replace('.', ','), 1)
                        else:
                            pdf.cell(25, 6, "", 1)
                            
                        pdf.cell(75, 6, str(row['Descrição']), 1)
                        pdf.cell(20, 6, str(row['Status']), 1)
                        pdf.ln()
                        total_valor += float(row['V_Num'])
                        
                    # Total da página
                    pdf.ln(2)
                    pdf.cell(20 + 25, 8, "Total", 1, 0, 'L')
                    pdf.cell(25, 8, f"R$ {total_valor:.2f}".replace('.', ','), 1, 0, 'R')
                    pdf.cell(25 + 75 + 20, 8, "", 1, 0, 'L')
                    
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
