import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

# RESOLUÇÃO DO FUSO HORÁRIO
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.4 - WhatsApp Fix")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES E RÓTULOS DOS METRICS
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1.1rem !important; font-weight: bold !important; }
    [data-testid='stMetricValue'] { font-size: 1.1rem !important; font-weight: bold !important; }
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

ws_base = sh.get_worksheet(0)
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# FUNÇÕES DE CARREGAMENTO
def carregar_dados_gs():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')   
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_manual_gs():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 1: return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados_gs()
if 'df_bancos_info' not in st.session_state:
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# WHATSAPP AUTOMÁTICO (TWILIO)
def enviar_whatsapp_pendencias(df):
    now = datetime.now()
    if now.hour >= 8:
        if 'last_wa_date' not in st.session_state or st.session_state['last_wa_date'] != now.date():
            twilio_secrets = st.secrets.get("twilio", {})
            sid, token = twilio_secrets.get("account_sid"), twilio_secrets.get("auth_token")
            w_from, w_to = twilio_secrets.get("whatsapp_from"), twilio_secrets.get("whatsapp_to")
            if sid and token:
                try:
                    from twilio.rest import Client
                    client_tw = Client(sid, token)
                    df_aviso = df[df['Status'] == 'Pendente'].copy()
                    if not df_aviso.empty:
                        df_aviso['Dias'] = (df_aviso['DT'] - pd.to_datetime(now)).dt.days
                        df_venc = df_aviso[df_aviso['Dias'].isin([0, 1, 3]) | (df_aviso['Dias'] < 0)].copy()
                        if not df_venc.empty:
                            msg = "🔔 *Aviso de Pendências - FinançasPro*\n\n"
                            for _, row in df_venc.iterrows():
                                status = "Atrasado" if row['Dias'] < 0 else ("Hoje" if row['Dias'] == 0 else f"em {row['Dias']} dias")
                                msg += f"⚠️ {status}: {row['Descrição']} - {m_fmt(row['V_Num'])}\n"
                            client_tw.messages.create(body=msg, from_=w_from, to=w_to)
                            st.session_state['last_wa_date'] = now.date()
                except: pass

enviar_whatsapp_pendencias(df_base)

# CONFIGURAÇÕES DINÂMICAS
if not df_bancos_info.empty:
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP"]

mes_atual = datetime.now().strftime('%m/%y')

# SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
if st.sidebar.button("🔄 Atualizar dados do Sheets"):
    atualizar_sessao(); st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF"])

# FORMULÁRIOS (MANTIDOS CONFORME SOLICITADO)
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_compra = st.date_input("🛍️ Data da Compra", value=datetime.now())
        f_dat = st.date_input("Vencimento", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água","Assinatura","Seguro", "Internet","Vestuário","Salário","Reembolso","Moradia", "Saúde","Taxas","Depósito","Transporte","Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta, ""])
            atualizar_sessao(); st.rerun()

# --- ABA WHATSAPP (RELATÓRIO MANUAL) ---
if "📄" in aba:
    st.title("📄 Relatório para WhatsApp")
    
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", hoje_br - timedelta(days=30), format="DD/MM/YYYY", key="zap_d1")
    d_fim = c2.date_input("Fim", hoje_br, format="DD/MM/YYYY", key="zap_d2")
    
    saldos_txt = ""
    total_patrimonio = 0.0 

    for b in sorted(bancos_disponiveis):
        valor_b, tipo_c, dia_venc_e = 0.0, "", 10
        
        if not df_bancos_info.empty:
            for _, row in df_bancos_info.iterrows():
                if str(row.iloc[0]).strip().upper() == str(b).strip().upper():
                    try:
                        v_raw = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        valor_b = float(v_raw) if v_raw and v_raw != 'nan' else 0.0
                        tipo_c = str(row.iloc[2]).strip().upper()
                        if len(row) >= 5:
                            ven_raw = str(row.iloc[4]).strip()
                            dia_venc_e = int(float(ven_raw)) if ven_raw and ven_raw != 'nan' else 10
                    except: pass
                    break
        
        if "CARTA" in tipo_c or "CART" in b.upper():
            df_cart_base = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].str.upper() == 'DESPESA') & (df_base['Status'].str.upper() == 'PENDENTE')].copy()
            df_cart_base['DT_ONLY'] = pd.to_datetime(df_cart_base['DT']).dt.date
            usado = df_cart_base[df_cart_base['DT_ONLY'] <= d_fim]['V_Num'].sum()
            dispo = valor_b - usado
            saldos_txt += f"💳 {b}: Limite: {m_fmt(valor_b)} | Usado: {m_fmt(usado)} | Disp: {m_fmt(dispo)} (Venc: {dia_venc_e})\n"
        else:
            mov_paga = df_base[(df_base['Banco'] == b) & (df_base['Status'].str.upper() == 'PAGO')]
            rec_b = mov_paga[mov_paga['Tipo'].str.upper().str.contains('RECEITA|REND', na=False)]['V_Num'].sum()
            des_b = mov_paga[mov_paga['Tipo'].str.upper() == 'DESPESA']['V_Num'].sum()
            s_final = valor_b + rec_b - des_b
            icone = "💰" if "INVEST" in tipo_c else "🏦"
            saldos_txt += f"{icone} {b}: Saldo: {m_fmt(s_final)}\n"
            total_patrimonio += s_final

    df_base['DT_ONLY'] = pd.to_datetime(df_base['DT']).dt.date
    df_per = df_base[(df_base['DT_ONLY'] >= d_ini) & (df_base['DT_ONLY'] <= d_fim)].copy()
    if not df_per.empty:
        df_per['T_UP'] = df_per['Tipo'].str.upper()
        df_per['C_UP'] = df_per['Categoria'].str.upper()
        rend_v = df_per[df_per['T_UP'].str.contains('REND', na=False) & (df_per['Status'] == 'Pago')]['V_Num'].sum()
        rec_v = df_per[(df_per['T_UP'] == 'RECEITA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        des_v = df_per[(df_per['T_UP'] == 'DESPESA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        sobra = rec_v - des_v
    else: rec_v = des_v = rend_v = sobra = 0.0

    relat = f"*RELATÓRIO WILSON*\n📅 Período: {d_ini.strftime('%d/%m')} a {d_fim.strftime('%d/%m')}\n\n{saldos_txt}\n"
    relat += f"💵 *Patrimônio Líquido:* {m_fmt(total_patrimonio)}\n📈 Rendimentos: {m_fmt(rend_v)}\n⚖️ Sobra Líquida: {m_fmt(sobra)}\n\nGerado em: {agora_br.strftime('%d/%m/%Y %H:%M')}"
    
    st.text_area("Copiável:", value=relat, height=350)
    st.markdown(f"[📲 Enviar para WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})")

# (Aqui continuariam as outras telas como 'Finanças & Bancos', 'Pendências', etc, seguindo a lógica do seu código original)
elif "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    # Lógica de Dashboard...
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    df_m_limpo = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
    saldo_geral = df_m_limpo[df_m_limpo['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
    st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
    # ... Restante dos gráficos do dashboard ...
