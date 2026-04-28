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
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento', 'Entrada'] else -r['V_Num'], axis=1)
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
        desc = str(r.get('Descrição', r.get('Descricao', 'Sem Descrição')))[:40]
        txt = f"{r['Data']} - {desc} - {r['Valor']}"
        pdf.cell(190, 7, txt.encode('latin-1', 'ignore').decode('latin-1'), border=1, ln=True)
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()

# 3. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "📊 Extrato Diário", "🐾 Milo & Bolt", "🚗 Meu Veículo"])
st.sidebar.markdown("---")
st.sidebar.link_button("💬 Abrir WhatsApp", "https://web.whatsapp.com")

# 4. LOGICA DAS ABAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        total_pago = df_base[df_base['Status_LIMPO'] == 'PAGO']['V_Real'].sum()
        st.metric("Saldo Geral (Pago)", m_fmt(total_pago))
        st.divider()
        st.info("Utilize o menu lateral para navegar entre os extratos detalhados.")

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Diário Detalhado")
    c1, c2, c3 = st.columns([1, 1, 2])
    d_ini = c1.date_input("Início", datetime.now().replace(day=1), format="DD/MM/YYYY")
    d_fim = c2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
    b_sel = c3.selectbox("Filtrar Banco:", sorted(df_base['Banco'].unique()))
    
    df_b = df_base[df_base['Banco'] == b_sel].copy()
    if not df_b.empty:
        df_b['Saldo_Acum'] = df_b[df_b['Status_LIMPO'] == 'PAGO']['V_Real'].cumsum()
        df_b['Saldo_Acum'] = df_b['Saldo_Acum'].ffill().fillna(0)
        df_b['Saldo_Exibir'] = df_b['Saldo_Acum'].apply(m_fmt)
        
        df_f = df_b[(df_b['DT_ORDEM'].dt.date >= d_ini) & (df_b['DT_ORDEM'].dt.date <= d_fim)].copy()
        
        col_btn, col_txt = st.columns([1,3])
        with col_btn:
            pdf = gerar_pdf(df_f, f"Extrato {b_sel}")
            st.download_button("🖨️ Imprimir PDF", pdf, f"extrato_{b_sel}.pdf")
            
        st.dataframe(df_f.iloc[::-1], column_order=("Data", "Descrição", "Valor", "Status", "Saldo_Exibir"), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gastos com Milo & Bolt")
    termos_pets = 'Milo|Bolt|Ração|Veterinário|Pet|Banho'
    df_pets = df_base[df_base['Descrição'].str.contains(termos_pets, case=False, na=False)].copy()
    
    if not df_pets.empty:
        pdf_p = gerar_pdf(df_pets, "Gastos Pets")
        st.download_button("🖨️ Imprimir PDF", pdf_p, "gastos_pets.pdf")
        st.dataframe(df_pets.iloc[::-1], column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro encontrado para Milo ou Bolt.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo - Manutenção e Combustível")
    termos_veiculo = 'Carro|Moto|Gasolina|Combustível|Etanol|Oficina|Óleo|Pneu|Mecânico|Peças'
    df_car = df_base[df_base['Descrição'].str.contains(termos_veiculo, case=False, na=False)].copy()
    
    if not df_car.empty:
        pdf_c = gerar_pdf(df_car, "Relatorio Veiculo")
        st.download_button("🖨️ Imprimir PDF", pdf_c, "relatorio_veiculo.pdf")
        st.dataframe(df_car.iloc[::-1], column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum registro de veículo encontrado.")
