import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# --- 1. CONFIGURAÇÃO ---
st.set_page_config(page_title="FinançasPro Wilson v2.6", layout="wide")

@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

@st.cache_data(ttl=2)
def carregar_dados():
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Planilha'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. MENU LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📄 Relatório WhatsApp", "✏️ Editar", "🐾 Milo & Bolt", "🚗 Veículo"])

# (Mantenha aqui os formulários de Novo Lançamento e Transferência das versões anteriores...)

# --- 3. TELAS ---

if aba == "📄 Relatório WhatsApp":
    st.title("📄 Gerador de Relatório para WhatsApp")
    
    col1, col2 = st.columns(2)
    d_ini = col1.date_input("Data Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = col2.date_input("Data Fim", datetime.now(), format="DD/MM/YYYY")
    
    if st.button("GERAR RELATÓRIO"):
        # Filtra o período
        df_p = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
        
        if not df_p.empty:
            # Cálculos Globais
            rec = df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum()
            des = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
            rend = df_p[df_p['Tipo'] == 'Rendimento']['V_Num'].sum()
            sobra = (rec + rend) - des
            
            # Cálculos por Banco
            bancos = df_p.groupby('Banco')['V_Num'].apply(lambda x: x.sum()).to_dict()
            
            # Montagem do Texto (Formatação Wilson)
            texto = f"RELATÓRIO WILSON\n"
            texto += f"Período: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
            texto += "========================================\n"
            texto += f"REC: {m_fmt(rec)}\n"
            texto += f"DES: {m_fmt(des)}\n"
            texto += f"REND: {m_fmt(rend)}\n"
            texto += f"SOBRA: {m_fmt(sobra)}\n"
            texto += "========================================\n\n"
            texto += "SALDOS:\n"
            
            for b, v in bancos.items():
                # Lógica simples: se o banco teve mais saída que entrada no período, mostra negativo
                texto += f"- {b}: {m_fmt(v)}\n"
            
            texto += f"\nTOTAL PATRIMÔNIO: {m_fmt(sobra)}"
            
            # Exibe na tela para conferir
            st.text_area("Prévia do Relatório:", texto, height=300)
            
            # Botão de Envio
            link = f"https://wa.me/?text={urllib.parse.quote(texto)}"
            st.link_button("📲 ENVIAR PARA WHATSAPP", link)
        else:
            st.warning("Nenhum dado encontrado para estas datas.")

# (Mantenha as outras abas de Finanças, Editar, Pet e Veículo como na v2.5...)
