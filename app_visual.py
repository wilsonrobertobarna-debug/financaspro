import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF
import tempfile
import os
import unicodedata

# 1. CONFIGURAÇÃO (Deve ser o primeiro comando Streamlit)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.3")

# Funções auxiliares
def remover_acentos(texto):
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto)) if unicodedata.category(c) != "Mn"
    )

def m_fmt(v):
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return "R$ 0,00"

# ESTILO PARA VALORES E RÓTULOS DOS METRICS
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    [data-testid='stMetricValue'] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

# 2. CONEXÃO
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets!"); st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# IDENTIFICAÇÃO DAS ABAS
ws_base = sh.get_worksheet(0)
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# FUNÇÕES DE CARREGAMENTO DIRETO
def carregar_dados_gs():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_manual_gs():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

# INICIALIZA O CACHE NA SESSÃO
if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados_gs()
if 'df_bancos_info' not in st.session_state:
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

# FUNÇÃO PARA ATUALIZAR O ESTADO
def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

# INTEGRAÇÃO DE AVISOS NO WHATSAPP VIA TWILIO
def enviar_whatsapp_pendencias(df):
    now = datetime.now()
    if now.hour >= 8:
        if 'last_wa_date' not in st.session_state or st.session_state['last_wa_date'] != now.date():
            twilio_secrets = st.secrets.get("twilio", {})
            sid = twilio_secrets.get("account_sid")
            token = twilio_secrets.get("auth_token")
            w_from = twilio_secrets.get("whatsapp_from")
            w_to = twilio_secrets.get("whatsapp_to")
            
            if sid and token and w_from and w_to:
                try:
                    from twilio.rest import Client
                    client_tw = Client(sid, token)
                    df_aviso = df[df['Status'] == 'Pendente'].copy()
                    if not df_aviso.empty:
                        df_aviso['Dias'] = (df_aviso['DT'] - pd.to_datetime(now)).dt.days
                        df_venc = df_aviso[df_aviso['Dias'].isin([0, 1, 3]) | (df_aviso['Dias'] < 0)].copy()
                        if not df_venc.empty:
                            mensagem = "🔔 *Aviso de Pendências - FinançasPro*\n\n"
                            for _, row in df_venc.iterrows():
                                if row['Dias'] < 0:
                                    mensagem += f"⚠️ Lançamento Atrasado: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 0:
                                    mensagem += f"⚠️ Vence Hoje: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 1:
                                    mensagem += f"🚨 Vence Amanhã: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 3:
                                    mensagem += f"⚠️ Vence em 3 dias: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                            
                            client_tw.messages.create(body=mensagem, from_=w_from, to=w_to)
                            st.session_state['last_wa_date'] = now.date()
                except Exception as e:
                    pass

enviar_whatsapp_pendencias(df_base)

# CARREGA OS BANCOS DINAMICAMENTE DA PLANILHA OU USA OS PADRÕES
if not df_bancos_info.empty:
    bancos = df_bancos_info.iloc[:, 0].tolist() if df_bancos_info.shape[1] > 0 else []
else:
    bancos = ["Nubank", "Itaú", "Bradesco", "Banco do Brasil", "Caixa"]

# ==========================================
# 3. INTERFACE DO USUÁRIO PRINCIPAL
# ==========================================
st.title("💰 FinançasPro - Dashboard e Controle")

if df_base.empty:
    st.warning("Nenhum dado encontrado na planilha. Verifique a aba inicial.")
else:
    aba_dash, aba_lancamentos, aba_relatorios, aba_bancos = st.tabs([
        "📊 Dashboard", "➕ Lançamentos", "📑 Relatórios", "🏦 Controle Bancário"
    ])

    with aba_dash:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Receitas", m_fmt(df_base[df_base['Tipo'] == 'Receita']['V_Num'].sum()))
        with col2:
            st.metric("Total Despesas", m_fmt(df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()))
        with col3:
            saldo = df_base[df_base['Tipo'] == 'Receita']['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
            st.metric("Saldo Líquido", m_fmt(saldo))

        st.subheader("Visualização de Gastos por Categoria")
        if 'Categoria' in df_base.columns and not df_base[df_base['Tipo'] == 'Despesa'].empty:
            fig = px.pie(df_base[df_base['Tipo'] == 'Despesa'], names='Categoria', values='V_Num', title="Despesas por Categoria")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Dados de categorias não encontrados para gerar o gráfico.")

    with aba_lancamentos:
        st.subheader("Adicionar Novo Lançamento")
        with st.form("form_lancamento"):
            c1, c2 = st.columns(2)
            with c1:
                descricao = st.text_input("Descrição")
                valor = st.number_input("Valor (R$)", value=0.00, step=0.01)
            with c2:
                tipo = st.selectbox("Tipo", ["Despesa", "Receita"])
                categoria = st.selectbox("Categoria", ["Alimentação", "Transporte", "Moradia", "Saúde", "Outros"])
                banco_sel = st.selectbox("Conta/Banco", bancos)
            
            submit = st.form_submit_button("Salvar")
            if submit:
                # Salva no Google Sheets
                nova_linha = [datetime.now().strftime('%d/%m/%Y'), descricao, tipo, f"R$ {valor:.2f}".replace(".", ","), banco_sel, "Pendente", categoria]
                ws_base.append_row(nova_linha)
                atualizar_sessao()
                st.success("Lançamento salvo com sucesso!")
                st.rerun()

        st.dataframe(df_base[['Data', 'Descrição', 'Tipo', 'Valor', 'Banco', 'Status']], use_container_width=True)

    with aba_relatorios:
        st.subheader("Exportar Relatório PDF")
        if st.button("Gerar PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Relatorio de Financas", ln=1, align="C")
            pdf.cell(200, 10, txt="FinancasPro - Wilson", ln=1, align="C")
            pdf.ln(10)
            
            for index, row in df_base.iterrows():
                desc = remover_acentos(str(row['Descrição']))
                val = str(row['Valor'])
                pdf.cell(200, 10, txt=f"{row['Data']} - {desc} : {val}", ln=1)
                
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmpfile:
                pdf.output(tmpfile.name)
                with open(tmpfile.name, "rb") as f:
                    st.download_button(
                        label="Baixar PDF",
                        data=f,
                        file_name="relatorio_financas.pdf",
                        mime="application/pdf"
                    )

    with aba_bancos:
        st.subheader("Controle de Bancos")
        if not df_bancos_info.empty:
            st.dataframe(df_bancos_info, use_container_width=True)
        else:
            st.info("Nenhuma informação detalhada de bancos encontrada na planilha.")
