import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from fpdf import FPDF

# 1. CONFIGURAÇÃO E CONEXÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        if pk.startswith('"') and pk.endswith('"'): pk = pk[1:-1]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro de conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 2. FUNÇÕES DE SUPORTE
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT_ORDEM'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Status_LIMPO'] = df['Status'].str.strip().str.upper()
    return df.sort_values(['DT_ORDEM'])

def m_fmt(n): 
    if n == "" or pd.isna(n) or n == 0: return "R$ 0,00"
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf(df, titulo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 12)
    pdf.cell(190, 10, f"RELATORIO: {titulo}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "", 8)
    for _, r in df.iterrows():
        desc = str(r['Descrição'])[:40]
        txt = f"{r['Data']} - {desc} - {r['Valor']}"
        pdf.cell(190, 7, txt.encode('latin-1', 'ignore').decode('latin-1'), border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()

# 3. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "🐾 Milo & Bolt", "🚗 Meu Veículo"])
st.sidebar.markdown("---")
st.sidebar.link_button("💬 Abrir WhatsApp", "https://web.whatsapp.com")

# 4. TELA MEU VEÍCULO
if aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo - Manutenção e Combustível")
    
    # Filtro inteligente para capturar tudo relacionado ao veículo
    termos_veiculo = 'Carro|Moto|Gasolina|Combustível|Etanol|Oficina|Óleo|Pneu|Mecânico|Peças'
    df_car = df_base[df_base['Descrição'].str.contains(termos_veiculo, case=False, na=False)].copy()
    
    if not df_car.empty:
        c1, c2 = st.columns([1, 3])
        with c1:
            pdf_c = gerar_pdf(df_car, "Relatorio Veiculo")
            st.download_button("🖨️ Imprimir Relatório (PDF)", pdf_c, "relatorio_veiculo.pdf")
        
        with c2:
            total_veiculo = df_car['V_Num'].sum()
            st.info(f"**Total Investido no Veículo:** {m_fmt(total_veiculo)}")

        st.divider()
        
        # Exibição Limpa
        st.dataframe(
            df_car.iloc[::-1], 
            column_order=("Data", "Descrição", "Valor", "Status", "Banco"),
            column_config={
                "Data": st.column_config.TextColumn("Data", width="small"),
                "Descrição": st.column_config.TextColumn("Descrição", width="large"),
                "Valor": st.column_config.TextColumn("Valor", width="medium"),
            },
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Nenhum registro de veículo encontrado na planilha com os termos monitorados.")

# Restante do código das outras abas (Finanças, Extrato, Pets) segue a mesma lógica...
