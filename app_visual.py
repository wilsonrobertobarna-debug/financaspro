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

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.3")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

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
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"]

mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# FUNÇÃO PARA OBTER O VALOR PENDENTE ATUAL
def get_valor_pendente(df):
    now = datetime.now()
    end_of_month = datetime(now.year, now.month, 1) + relativedelta(months=1, days=-1)
    df_p = df[(df['Status'] == 'Pendente') & (df['DT'].dt.date <= end_of_month.date())]
    return df_p['V_Num'].sum()

# 4. SIDEBAR - NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")

if st.sidebar.button("🔄 Atualizar dados do Sheets"):
    atualizar_sessao()
    st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF"])

st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        
        f_cat = st.selectbox("Categoria", [
            "Mercado",
            "Aluguel",
            "Luz/Água",
            "Internet",
            "Vestuário",
            "Moradia",
            "Saúde",
            "Previdência",
            "Outros",
            "Pet: Milo - Ração",
            "Pet: Milo - Saúde",
            "Pet: Milo - Acessórios",
            "Pet: Bolt - Ração",
            "Pet: Bolt - Saúde",
            "Pet: Bolt - Acessórios",
            "Veículo - Combustível",
            "Veículo - Manutenção",
            "Veículo - Seguro",
            "Salário",
            "Rendimentos",
            "Reembolsos",
            "Transferência",
            "Seguro",
            "Imposto",
            "Salão Beleza",
            "Assinatura",
            "Celular"
        ])
        
        # Campo para preencher a subcategoria
        f_sub = st.text_input("Subcategoria (Opcional)")
        
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        f_venc_cartao = st.date_input("Vencimento do Cartão (Opcional)", value=None, format="DD/MM/YYYY")
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            venc_str = f_venc_cartao.strftime("%d/%m/%Y") if f_venc_cartao is not None else ""
            
            # Combina categoria e subcategoria
            cat_final = f"{f_cat} - {f_sub}" if f_sub.strip() else f_cat
            
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, cat_final, f_tip, f_bnc, f_sta, venc_str])
            
            atualizar_sessao()
            st.rerun()

# BARRINHA 2: NOVA TRANSFERÊNCIA
with st.sidebar.expander("💸 Nova Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data da Transferência", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor da Transferência", min_value=0.0, step=0.01, format="%.2f", key="t_val")
        t_orig = st.selectbox("Conta Origem", bancos_disponiveis, key="t_orig")
        t_dest = st.selectbox("Conta Destino", bancos_disponiveis, key="t_dest")
        t_obs = st.text_input("Observação / Descrição (Opcional)", key="t_obs")
        
        if st.form_submit_button("TRANSFERIR"):
            if t_val > 0:
                t_val_str = f"{t_val:.2f}".replace('.', ',')
                
                # Registra a saída na conta de origem
                ws_base.append_row([
                    t_dat.strftime("%d/%m/%Y"), 
                    t_val_str, 
                    f"Transferência para {t_dest} - {t_obs}", 
                    "Transferência", 
                    "Despesa", 
                    t_orig, 
                    "Pago", 
                    ""
                ])
                
                # Registra a entrada na conta de destino
                ws_base.append_row([
                    t_dat.strftime("%d/%m/%Y"), 
                    t_val_str, 
                    f"Transferência de {t_orig} - {t_obs}", 
                    "Transferência", 
                    "Receita", 
                    t_dest, 
                    "Pago", 
                    ""
                ])
                
                atualizar_sessao()
                st.rerun()

# 5. ABAS PRINCIPAIS
if aba == "💰 Finanças & Bancos":
    st.subheader("💰 Finanças & Bancos")
    st.info("Visão geral de finanças, lançamentos e movimentações bancárias.")
    
elif aba == "Pendências":
    st.subheader("📋 Pendências")
    st.info("Acompanhamento de contas a pagar e receber.")
    
elif aba == "🐾 Milo & Bolt":
    st.subheader("🐾 Milo & Bolt")
    
elif aba == "🚗 Meu Veículo":
    st.subheader("🚗 Meu Veículo")
    
elif aba == "📄 WhatsApp":
    st.subheader("📄 Relatórios e Envios para WhatsApp")
    
elif aba == "📋 Relatório PDF":
    st.subheader("📋 Gerador de Relatório PDF")
    
    col1, col2 = st.columns(2)
    with col1:
        p_inicio = st.date_input("Data Início", datetime.now().replace(day=1), format="DD/MM/YYYY")
    with col2:
        p_fim = st.date_input("Data Fim", datetime.now(), format="DD/MM/YYYY")
        
    col3, col4, col5 = st.columns(3)
    with col3:
        filtro_banco = st.selectbox("Filtrar por Banco", ["Todos"] + bancos_disponiveis)
    with col4:
        filtro_status = st.selectbox("Filtrar por Status", ["Todos", "Pago", "Pendente"])
    with col5:
        filtro_tipo = st.selectbox("Filtrar por Tipo", ["Todos", "Despesa", "Receita", "Rendimento"])
        
    filtro_busca = st.text_input("Buscar por Descrição ou Categoria")
    
    # Exibe os filtros selecionados logo abaixo, como solicitado
    st.markdown("##### 🔍 Filtros Ativos:")
    filtros_texto = f"**Período:** {p_inicio.strftime('%d/%m/%Y')} a {p_fim.strftime('%d/%m/%Y')}"
    if filtro_busca:
        filtros_texto += f" | **Busca:** {filtro_busca}"
    if filtro_banco != "Todos":
        filtros_texto += f" | **Banco:** {filtro_banco}"
    if filtro_status != "Todos":
        filtros_texto += f" | **Status:** {filtro_status}"
    if filtro_tipo != "Todos":
        filtros_texto += f" | **Tipo:** {filtro_tipo}"
        
    st.info(filtros_texto)
    
    # Filtragem dos dados na memória
    df_temp = df_base[
        (df_base['DT'].dt.date >= p_inicio) & 
        (df_base['DT'].dt.date <= p_fim)
    ].copy()
    
    if filtro_banco != "Todos":
        df_temp = df_temp[df_temp['Banco'] == filtro_banco]
    if filtro_status != "Todos":
        df_temp = df_temp[df_temp['Status'] == filtro_status]
    if filtro_tipo != "Todos":
        df_temp = df_temp[df_temp['Tipo'] == filtro_tipo]
    if filtro_busca:
        df_temp = df_temp[
            df_temp['Descrição'].str.contains(filtro_busca, case=False, na=False) |
            df_temp['Categoria'].str.contains(filtro_busca, case=False, na=False)
        ]
        
    # Aplicação do Saldo Acumulado Clássico Diário
    df_temp = df_temp.sort_values('DT')
    df_temp['Valor_Ajustado'] = df_temp.apply(
        lambda x: -x['V_Num'] if x['Tipo'] == 'Despesa' else x['V_Num'], axis=1
    )
    df_temp['Saldo_Acumulado'] = df_temp['Valor_Ajustado'].cumsum()
    
    # Exibição dos dados na tela
    st.dataframe(df_temp[['Data', 'Descrição', 'Categoria', 'Tipo', 'Banco', 'Valor', 'Status', 'Saldo_Acumulado']], use_container_width=True)
    
    if st.button("📥 Gerar PDF do Relatório"):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', size=12)
        pdf.cell(200, 10, txt="Relatorio Financeiro - FinancasPro", ln=1, align="C")
        pdf.ln(5)
        
        pdf.set_font("Arial", size=9)
        pdf.cell(200, 8, txt=filtros_texto.replace("**", ""), ln=1, align="C")
        pdf.ln(5)
        
        # Cabeçalhos da Tabela no PDF
        pdf.set_font("Arial", 'B', size=9)
        pdf.cell(28, 8, "Data", 1)
        pdf.cell(85, 8, "Descricao", 1)
        pdf.cell(22, 8, "Valor", 1)
        pdf.cell(25, 8, "Saldo Acum.", 1)
        pdf.ln()
        
        pdf.set_font("Arial", size=9)
        for _, row in df_temp.iterrows():
            pdf.cell(28, 6, str(row['Data']), 1)
            desc_text = str(row['Descrição'])[:40]
            pdf.cell(85, 6, desc_text.encode('latin-1', 'replace').decode('latin-1'), 1)
            pdf.cell(22, 6, str(row['Valor']), 1)
            pdf.cell(25, 6, f"{row['Saldo_Acumulado']:,.2f}".replace('.', ','), 1)
            pdf.ln()
            
        pdf_bytes = pdf.output(dest='S').encode('latin-1')
        st.download_button(
            label="📄 Baixar PDF Gerado",
            data=pdf_bytes,
            file_name="relatorio_financeiro.pdf",
            mime="application/pdf"
        )
