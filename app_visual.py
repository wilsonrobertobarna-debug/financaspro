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

# 3. CARREGAMENTO E FUNÇÕES
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
    df['Ano_Mes_Sort'] = df['DT'].dt.strftime('%Y-%m') # Para ordenação correta
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def gerar_pdf_extrato(df, banco, p_ini, p_fim):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"EXTRATO BANCARIO - {banco}", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(190, 10, f"Periodo: {p_ini.strftime('%d/%m/%Y')} ate {p_fim.strftime('%d/%m/%Y')}", ln=True, align="C")
    pdf.ln(5)
    pdf.set_fill_color(200, 200, 200)
    pdf.set_font("Arial", "B", 9)
    pdf.cell(25, 8, "Data", 1, 0, "C", True)
    pdf.cell(80, 8, "Descricao", 1, 0, "L", True)
    pdf.cell(40, 8, "Valor", 1, 0, "R", True)
    pdf.cell(45, 8, "Saldo", 1, 1, "R", True)
    pdf.set_font("Arial", "", 8)
    for _, r in df.iloc[::-1].iterrows():
        pdf.cell(25, 7, str(r['Data']), 1, 0, "C")
        pdf.cell(80, 7, str(r['Descrição'])[:45], 1, 0, "L")
        pdf.cell(40, 7, r['Valor Item'], 1, 0, "R")
        pdf.cell(45, 7, r['Saldo'], 1, 1, "R")
    return pdf.output(dest='S').encode('latin-1', errors='replace')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (FORMULÁRIOS PROTEGIDOS)
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

st.sidebar.divider()

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "XP", "Mercado Pago"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_dt = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
            ws_base.append_row([nova_dt, v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

with st.sidebar.form("f_transf", clear_on_submit=True):
    st.write("### 💸 Transferência")
    t_val = st.number_input("Valor", min_value=0.0)
    t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
    t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
    if st.form_submit_button("EXECUTAR"):
        d_s = datetime.now().strftime("%d/%m/%Y")
        v_s = f"{t_val:.2f}".replace('.', ',')
        ws_base.append_row([d_s, v_s, f"Transf: {t_orig} > {t_dest}", "Transferência", "Despesa", t_orig, "Pago"])
        ws_base.append_row([d_s, v_s, f"Transf: {t_orig} > {t_dest}", "Transferência", "Receita", t_dest, "Pago"])
        st.cache_data.clear(); st.rerun()

st.sidebar.divider()
st.sidebar.write("### ⚙️ Ajustes")
ultimos = {f"{r['ID']} | {r['Descrição']}": r for _, r in df_base.tail(10).iterrows()}
escolha = st.sidebar.selectbox("Excluir:", [""] + list(ultimos.keys()))
if escolha and st.sidebar.button("🚨 EXCLUIR"):
    ws_base.delete_rows(int(ultimos[escolha]['ID']))
    st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
    
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3, m4 = st.columns(4)
    gasto_atual = df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()
    m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
    m2.metric("📉 Gasto", m_fmt(gasto_atual))
    m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
    m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
    
    st.divider()
    
    # --- GRÁFICOS SOLICITADOS ---
    col_g1, col_g2 = st.columns(2)
    
    with col_g1:
        # Gráfico Receita x Despesa Mes a Mes
        df_agrupado = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        df_agrupado = df_agrupado[df_agrupado['Tipo'].isin(['Receita', 'Despesa'])]
        fig_evolucao = px.bar(df_agrupado, x='Mes_Ano', y='V_Num', color='Tipo', 
                              barmode='group', title="Evolução Mensal: Receita x Despesa",
                              color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
        st.plotly_chart(fig_evolucao, use_container_width=True)
        
    with col_g2:
        # Gráfico de Meta de Gastos (Exemplo: Meta de R$ 5.000,00)
        meta = 5000.00 
        progresso = (gasto_atual / meta) * 100 if meta > 0 else 0
        fig_meta = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = gasto_atual,
            title = {'text': f"Meta de Gastos Mensal (R$ {meta:,.2f})"},
            domain = {'x': [0, 1], 'y': [0, 1]},
            gauge = {
                'axis': {'range': [None, meta * 1.2]},
                'bar': {'color': "#EF553B" if gasto_atual > meta else "#3B82F6"},
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': meta}
            }
        ))
        st.plotly_chart(fig_meta, use_container_width=True)

    st.divider()
    st.dataframe(df_base[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco']].iloc[::-1], use_container_width=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_pets = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.metric("Total Acumulado Pets", m_fmt(df_pets['V_Num'].sum()))
    fig_pets = px.area(df_pets.sort_values('DT'), x='DT', y='V_Num', title="Histórico de Gastos com os Pets")
    st.plotly_chart(fig_pets, use_container_width=True)
    st.table(df_pets[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    st.write("### ⛽ Calculadora Álcool x Gasolina")
    cv1, cv2 = st.columns(2)
    p_alc = cv1.number_input("Preço Álcool", min_value=0.0, step=0.01, key="calc_alc")
    p_gas = cv2.number_input("Preço Gasolina", min_value=0.0, step=0.01, key="calc_gas")
    if p_alc > 0 and p_gas > 0:
        if p_alc / p_gas <= 0.7: st.success("✅ ÁLCOOL compensa!")
        else: st.warning("⛽ GASOLINA compensa!")
    st.divider()
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Banco', 'Status']].iloc[::-1])

elif aba == "📊 Extrato Diário":
    st.title("📊 Pesquisa e Extrato Detalhado")
    
    # --- PESQUISA E FILTROS ---
    f1, f2, f3 = st.columns([1, 1, 2])
    data_ini = f1.date_input("De:", datetime.now().replace(day=1))
    data_fim = f2.date_input("Até:", datetime.now())
    busca_txt = f3.text_input("🔍 Pesquisar na Descrição:", placeholder="Ex: Mercado, Posto...")
    
    b_sel = st.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b = df_b[(df_b['DT'].dt.date >= data_ini) & (df_b['DT'].dt.date <= data_fim)]
    if busca_txt:
        df_b = df_b[df_b['Descrição'].str.contains(busca_txt, case=False, na=False)]
        
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Valor Item'] = df_b.apply(lambda r: f"-{m_fmt(r['V_Num'])}" if r['Tipo'] == 'Despesa' else m_fmt(r['V_Num']), axis=1)
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    
    c_btn1, c_btn2 = st.columns(2)
    with c_btn1:
        pdf_file = gerar_pdf_extrato(df_b, b_sel, data_ini, data_fim)
        st.download_button("📄 IMPRIMIR EXTRATO PDF", pdf_file, f"extrato_{b_sel}.pdf", "application/pdf", use_container_width=True)
    with c_btn2:
        st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote("Wilson, segue extrato do " + b_sel)}" target="_blank"><button style="width:100%;background-color:#25D366;color:white;padding:10px;border:none;border-radius:5px;font-weight:bold;cursor:pointer;">📲 MANDAR VIA WHATSAPP</button></a>', unsafe_allow_html=True)
    
    st.table(df_b[['Data', 'Descrição', 'Tipo', 'Valor Item', 'Saldo', 'Status']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatórios")
    # ... (Lógica de relatórios mantida)
