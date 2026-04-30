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

# --- 1. CONFIGURAÇÃO E ESTILO ---
st.set_page_config(page_title="FinançasPro Wilson v3.0", layout="wide")
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 1.8rem !important;}</style>", unsafe_allow_html=True)

# --- 2. CONEXÃO COM GOOGLE SHEETS (CORREÇÃO ERRO 92 / PEM) ---
@st.cache_resource
def conectar_planilha():
    try:
        # Pega as credenciais dos Secrets
        creds_dict = dict(st.secrets["connections"]["gsheets"])
        
        # O segredo para não dar erro de PEM: Limpar as barras invertidas e aspas
        if "private_key" in creds_dict:
            creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n").strip().strip('"').strip("'")
        
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        creds = Credentials.from_service_account_info(creds_dict, scopes=scopes)
        client = gspread.authorize(creds)
        
        # Abre a planilha pelo ID que você forneceu
        return client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4").get_worksheet(0)
    except Exception as e:
        st.error(f"Erro na conexão: {e}")
        st.stop()

ws = conectar_planilha()

# --- 3. FUNÇÕES DE DADOS ---
@st.cache_data(ttl=5)
def carregar_dados():
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID'] = range(2, len(df) + 2)
    
    def formatar_valor(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(formatar_valor)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df = carregar_dados()
mes_ref = datetime.now().strftime('%m/%y')

def real_br(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 4. BARRA LATERAL (SIDEBAR) ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📲 WhatsApp", "📄 PDF"])

st.sidebar.divider()

# NOVO LANÇAMENTO
with st.sidebar.expander("📝 Novo Lançamento"):
    with st.form("form_add", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0, format="%.2f")
        f_par = st.number_input("Parcelas", 1, 48)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Lazer", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Mercado Pago", "Dinheiro"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("Salvar"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                dt_parc = f_dat + relativedelta(months=i)
                ws.append_row([dt_parc.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear()
            st.rerun()

# TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferência"):
    with st.form("form_transf"):
        t_dat = st.date_input("Data", datetime.now())
        t_val = st.number_input("Valor", 0.0)
        t_des = st.text_input("Descrição", "Transferência entre contas")
        t_ori = st.selectbox("Origem", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_des_b = st.selectbox("Destino", ["Nubank", "Inter", "Itaú", "Santander", "Dinheiro"])
        if st.form_submit_button("Executar"):
            v_str = f"{t_val:.2f}".replace('.', ',')
            ws.append_row([t_dat.strftime("%d/%m/%Y"), v_str, f"{t_des} (Saída)", "Transferência", "Despesa", t_ori, "Pago"])
            ws.append_row([t_dat.strftime("%d/%m/%Y"), v_str, f"{t_des} (Entrada)", "Transferência", "Receita", t_des_b, "Pago"])
            st.cache_data.clear()
            st.rerun()

# EDITAR / EXCLUIR
with st.sidebar.expander("⚙️ Alterar / Excluir"):
    if not df.empty:
        opcoes = {f"{r['ID']} | {r['Data']} | {r['Descrição']} | R$ {r['Valor']}": r for _, r in df.tail(30).iloc[::-1].iterrows()}
        selecao = st.selectbox("Escolha o item", [""] + list(opcoes.keys()))
        if selecao:
            item = opcoes[selecao]
            new_val = st.number_input("Novo Valor", value=float(item['V_Num']))
            new_sta = st.selectbox("Status", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
            c1, c2 = st.columns(2)
            if c1.button("💾 Gravar"):
                ws.update_cell(int(item['ID']), 2, f"{new_val:.2f}".replace('.', ','))
                ws.update_cell(int(item['ID']), 7, new_sta)
                st.cache_data.clear()
                st.rerun()
            if c2.button("🗑️ Apagar"):
                ws.delete_rows(int(item['ID']))
                st.cache_data.clear()
                st.rerun()

# --- 5. ÁREAS DE CONTEÚDO ---

if aba == "💰 Finanças":
    st.title("🛡️ Finanças do Wilson")
    if not df.empty:
        rec = df[df['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des = df[df['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {real_br(rec - des)}")
        
        df_m = df[df['Mes_Ano'] == mes_ref].copy()
        col1, col2, col3 = st.columns(3)
        col1.metric("Ganhos (Mês)", real_br(df_m[df_m['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()))
        col2.metric("Gastos (Mês)", real_br(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
        col3.metric("Pendentes", real_br(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        # Metas Gráfico Horizontal
        st.divider()
        with st.expander("🎯 Metas de Gastos", expanded=True):
            cats_desp = sorted(df[df['Tipo']=='Despesa']['Categoria'].unique())
            if "Transferência" in cats_desp: cats_desp.remove("Transferência")
            
            fig_metas = go.Figure()
            for cat in cats_desp[:6]:
                gasto = df_m[df_m['Categoria'] == cat]['V_Num'].sum()
                meta_val = 1500.0 # Valor padrão
                fig_metas.add_trace(go.Bar(y=[cat], x=[meta_val], orientation='h', name='Meta', marker_color='rgba(0,0,0,0.1)'))
                fig_metas.add_trace(go.Bar(y=[cat], x=[gasto], orientation='h', name='Gasto', marker_color='#e74c3c' if gasto > meta_val else '#2ecc71'))
            
            fig_metas.update_layout(barmode='overlay', height=350, title="Progresso por Categoria")
            st.plotly_chart(fig_metas, use_container_width=True)

        st.subheader("🔍 Últimos Lançamentos")
        st.dataframe(df.iloc[::-1][['Data', 'Descrição', 'Valor', 'Categoria', 'Banco', 'Status']], use_container_width=True, hide_index=True)

elif aba == "🐾 Pets":
    st.title("🐾 Central Pets (Milo & Bolt)")
    df_p = df[df['Categoria'].str.contains("Pet|Milo|Bolt", case=False, na=False)]
    if not df_p.empty:
        st.metric("Gasto Total Pets", real_br(df_p['V_Num'].sum()))
        st.dataframe(df_p.iloc[::-1][['Data', 'Descrição', 'Valor', 'Status']], use_container_width=True)

elif aba == "🚗 Veículo":
    st.title("🚗 Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    pa = c1.number_input("Álcool", 0.0)
    pg = c2.number_input("Gasolina", 0.0)
    if pa > 0 and pg > 0:
        if pa/pg <= 0.7: c3.success("✅ VÁ DE ÁLCOOL")
        else: c3.warning("✅ VÁ DE GASOLINA")
    
    df_v = df[df['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.dataframe(df_v.iloc[::-1][['Data', 'Descrição', 'Valor', 'Banco']], use_container_width=True)

elif aba == "📲 WhatsApp":
    st.title("📲 Relatório WhatsApp")
    resumo = f"*BALANÇO WILSON*\n\n"
    for b in sorted(df['Banco'].unique()):
        if b.strip():
            s = df[df['Banco']==b][df['Tipo'].isin(['Receita','Rendimento'])]['V_Num'].sum() - df[(df['Banco']==b) & (df['Tipo']=='Despesa')]['V_Num'].sum()
            resumo += f"• {b}: {real_br(s)}\n"
    
    st.text_area("Cópia:", resumo, height=150)
    st.markdown(f"[📲 Enviar para WhatsApp](https://wa.me/?text={urllib.parse.quote(resumo)})")

elif aba == "📄 PDF":
    st.title("📄 Relatório em PDF")
    if st.button("Gerar e Baixar"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "RELATORIO FINANCEIRO", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        for _, r in df.tail(25).iterrows():
            pdf.cell(190, 8, f"{r['Data']} - {r['Descrição']} - {real_br(r['V_Num'])}", 1, 1)
        st.download_button("Baixar PDF", pdf.output(dest='S').encode('latin-1'), "financeiro_wilson.pdf")
