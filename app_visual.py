import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

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
            "private_key": pk, "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E FORMATAÇÃO
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
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf(df, titulo):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(190, 10, titulo, ln=True, align="C")
    pdf.ln(5)
    pdf.set_font("Arial", "B", 9)
    cols = ["Data", "Descrição", "Valor", "Banco"]
    for c in cols: pdf.cell(45, 8, c, 1)
    pdf.ln()
    pdf.set_font("Arial", "", 8)
    for _, r in df.iloc[::-1].iterrows():
        pdf.cell(30, 7, str(r['Data']), 1)
        pdf.cell(75, 7, str(r['Descrição'])[:35], 1)
        pdf.cell(40, 7, f"R$ {r['V_Num']:.2f}", 1)
        pdf.cell(45, 7, str(r['Banco']), 1)
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
    f_bnc = st.selectbox("Banco/Cartão", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_dt = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
            ws_base.append_row([nova_dt, v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    st.metric("Gasto Mensal", m_fmt(-df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gastos Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.metric("Total Acumulado Pets", m_fmt(df_pets['V_Num'].sum()))
    st.dataframe(df_pets[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    
    # CALCULADORA ALCOOL X GASOLINA
    st.write("### ⛽ Álcool ou Gasolina?")
    col1, col2 = st.columns(2)
    preco_alc = col1.number_input("Preço do Álcool (R$)", min_value=0.0, step=0.01, format="%.2f")
    preco_gas = col2.number_input("Preço da Gasolina (R$)", min_value=0.0, step=0.01, format="%.2f")
    
    if preco_alc > 0 and preco_gas > 0:
        resultado = preco_alc / preco_gas
        if resultado <= 0.7:
            st.success(f"O resultado deu {resultado:.2f}. **Vá de ÁLCOOL!**")
        else:
            st.warning(f"O resultado deu {resultado:.2f}. **Vá de GASOLINA!**")
    
    st.divider()
    st.write("### 🛠️ Histórico de Gastos")
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False)]
    st.metric("Total Gasto com Veículo", m_fmt(df_v['V_Num'].sum()))
    st.dataframe(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Bancário")
    b_sel = st.selectbox("Escolha o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Valor Formatado'] = df_b.apply(lambda r: f"-R$ {r['V_Num']:.2f}".replace('.', ',') if r['Tipo'] == 'Despesa' else f"R$ {r['V_Num']:.2f}".replace('.', ','), axis=1)
    df_b['Saldo Diário'] = df_b['Saldo_Acum'].apply(m_fmt)
    
    st.download_button("📄 Baixar Extrato PDF", gerar_pdf(df_b, f"Extrato: {b_sel}"), f"extrato_{b_sel}.pdf", "application/pdf")
    st.table(df_b[['Data', 'Descrição', 'Valor Formatado', 'Saldo Diário']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Financeiro")
    d1, d2 = st.columns(2)
    ini = d1.date_input("Início", datetime.now().replace(day=1))
    fim = d2.date_input("Fim", datetime.now())
    
    df_p = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    saldos_txt = ""
    total_patrimonio = 0
    for b in sorted(df_base['Banco'].unique()):
        s = df_base[df_base['Banco'] == b]['V_Real'].sum()
        saldos_txt += f"- {b}: {m_fmt(s)}\n"
        total_patrimonio += s

    relat = f"RELATÓRIO WILSON\nPeríodo: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n"
    relat += "========================================\n"
    relat += f"REC: {m_fmt(df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum())}\n"
    relat += f"DES: {m_fmt(-df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum())}\n"
    relat += f"SOBRA: {m_fmt(df_p['V_Real'].sum())}\n"
    relat += "========================================\n\nSALDOS:\n"
    relat += saldos_txt
    relat += "========================================\n"
    relat += f"PATRIMÔNIO: {m_fmt(total_patrimonio)}"
    
    st.text_area("Texto para copiar:", relat, height=400)
    zap_url = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f'''<a href="{zap_url}" target="_blank"><button style="width:100%; height:50px; background-color:#25D366; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">📲 ENVIAR PARA WHATSAPP</button></a>''', unsafe_allow_html=True)

# 6. AJUSTES (EDITAR/EXCLUIR)
st.sidebar.divider()
if not df_base.empty:
    st.sidebar.write("### ⚙️ Ajustes Rápidos")
    lista = {f"{r['ID']} | {r['Data']} | {r['Descrição']}": r for _, r in df_base.tail(10).iterrows()}
    escolha = st.sidebar.selectbox("Selecionar para Ajuste:", [""] + list(lista.keys()))
    if escolha:
        item = lista[escolha]
        ed_v = st.sidebar.text_input("Novo Valor:", value=str(item['Valor']))
        if st.sidebar.button("💾 SALVAR ALTERAÇÃO"):
            ws_base.update_cell(int(item['ID']), 2, ed_v)
            st.cache_data.clear(); st.rerun()
