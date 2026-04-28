import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO (Mantenha seus segredos configurados no Streamlit Cloud)
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
    if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
    final_creds = {
        "type": creds_dict["type"], "project_id": creds_dict["project_id"],
        "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
        "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
    }
    return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df

df_base = carregar()

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. LÓGICA DE SALDOS POR BANCO
def calcular_saldos(df):
    saldos = {}
    bancos = df['Banco'].unique()
    for banco in bancos:
        rec = df[(df['Banco'] == banco) & (df['Tipo'].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
        des = df[(df['Banco'] == banco) & (df['Tipo'] == 'Despesa')]['V_Num'].sum()
        saldos[banco] = rec - des
    return saldos

# 5. SIDEBAR E NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# ... (Mantenha aqui os formulários de Novo Lançamento e Transferência que já usamos)

# 6. TELA DE RELATÓRIOS (A NOVIDADE)
if aba == "📄 Relatórios":
    st.title("📄 Relatório Consolidado Wilson")
    
    c1, c2 = st.columns(2)
    data_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1))
    data_fim = c2.date_input("Fim", datetime.now())
    
    # Filtrar dados para o período
    df_per = df_base[(df_base['DT'].dt.date >= data_ini) & (df_base['DT'].dt.date <= data_fim)].copy()
    
    if not df_per.empty:
        rec = df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum()
        des = df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        rend = df_per[df_per['Tipo'] == 'Rendimento']['V_Num'].sum()
        sobra = (rec + rend) - des
        
        saldos_bancos = calcular_saldos(df_base) # Saldo total histórico por banco
        total_bancos = sum(saldos_bancos.values())

        # MODELO DE TEXTO PARA WHATSAPP
        texto_relatorio = f"""RELATÓRIO WILSON
Período: {data_ini.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}
========================================
REC: {m_fmt(rec)}
DES: {m_fmt(des)}
REND: {m_fmt(rend)}
SOBRA: {m_fmt(sobra)}
========================================

SALDOS ATUAIS:"""
        for b, s in saldos_bancos.items():
            texto_relatorio += f"\n- {b}: {m_fmt(s)}"
            
        texto_relatorio += f"\n\nTOTAL PATRIMÔNIO: {m_fmt(total_bancos)}"

        st.text_area("Cópia para WhatsApp/E-mail", texto_relatorio, height=400)
        st.caption("Pressione Ctrl+A e Ctrl+C para copiar o texto acima.")
        
        if st.button("🖨️ Gerar Visualização para PDF"):
            st.write(texto_relatorio.replace("\n", "<br>"), unsafe_allow_html=True)
            st.info("Dica: Use o comando imprimir do navegador (Ctrl+P) e escolha 'Salvar como PDF'.")

# ... (Mantenha as outras abas de Finanças, Milo e Veículo)
