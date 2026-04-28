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
    df['ID_Linha'] = range(2, len(df) + 2) # ID real da linha na planilha
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    df['Ano_Mes_Sort'] = df['DT'].dt.strftime('%Y-%m')
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

# 4. SIDEBAR (NOVO LANÇAMENTO)
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

# 5. TELA DE FINANÇAS (COMPLETA)
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    patrimonio = df_base['V_Real'].sum()
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
    
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
    m2.metric("📉 Gasto", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
    m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
    m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
    
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Evolução Mensal"), use_container_width=True)
    with c2:
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(gastos_cat, x='Categoria', y='V_Num', title="Gastos por Categoria"), use_container_width=True)

    st.divider()
    st.write("### 🔍 Pesquisa e Ações")
    psq1, psq2, psq3 = st.columns([1, 1, 2])
    b_p = psq1.selectbox("Banco:", ["Todos"] + sorted(df_base['Banco'].unique().tolist()))
    t_p = psq2.selectbox("Tipo:", ["Todos", "Receita", "Despesa", "Rendimento"])
    d_p = psq3.text_input("Descrição Wilson:")
    
    df_f = df_base.copy()
    if b_p != "Todos": df_f = df_f[df_f['Banco'] == b_p]
    if t_p != "Todos": df_f = df_f[df_f['Tipo'] == t_p]
    if d_p: df_f = df_f[df_f['Descrição'].str.contains(d_p, case=False, na=False)]
    
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Categoria', 'Status']].iloc[::-1], use_container_width=True)

    # --- NOVO BLOCO DE AÇÕES (TRANSFERÊNCIA, BAIXA, EXCLUSÃO) ---
    st.divider()
    act1, act2, act3 = st.columns(3)

    with act1:
        st.write("### 💸 Transferência")
        with st.form("f_transf", clear_on_submit=True):
            t_v = st.number_input("Valor", min_value=0.0)
            t_o = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Mercado Pago"])
            t_d = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "XP", "Mercado Pago"])
            if st.form_submit_button("EXECUTAR TRANSFERÊNCIA"):
                hj = datetime.now().strftime("%d/%m/%Y")
                v_s = f"{t_v:.2f}".replace('.', ',')
                ws_base.append_row([hj, v_s, f"Transf: {t_o} > {t_d}", "Transferência", "Despesa", t_o, "Pago"])
                ws_base.append_row([hj, v_s, f"Transf: {t_o} > {t_d}", "Transferência", "Receita", t_d, "Pago"])
                st.cache_data.clear(); st.rerun()

    with act2:
        st.write("### 📝 Alterar Status")
        # Pega os últimos 15 lançamentos para alteração rápida
        opcoes_alt = {f"{r['Data']} - {r['Descrição']} ({r['Valor']})": r['ID_Linha'] for _, r in df_base.tail(15).iterrows()}
        sel_alt = st.selectbox("Escolha o lançamento:", [""] + list(opcoes_alt.keys()))
        novo_status = st.selectbox("Novo Status:", ["Pago", "Pendente"])
        if st.button("ATUALIZAR STATUS") and sel_alt:
            ws_base.update_cell(opcoes_alt[sel_alt], 7, novo_status) # Coluna 7 é o Status
            st.cache_data.clear(); st.rerun()

    with act3:
        st.write("### 🚨 Excluir")
        sel_exc = st.selectbox("Lançamento para excluir:", [""] + list(opcoes_alt.keys()))
        if st.button("EXCLUIR PERMANENTE") and sel_exc:
            ws_base.delete_rows(opcoes_alt[sel_exc])
            st.cache_data.clear(); st.rerun()

# --- AS OUTRAS ABAS MANTIDAS E FUNCIONAIS ---
elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato")
    b_sel = st.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    st.table(df_b[['Data', 'Descrição', 'Valor', 'Saldo']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatórios WhatsApp")
    r1, r2 = st.columns(2)
    i, f = r1.date_input("Início", datetime.now().replace(day=1)), r2.date_input("Fim", datetime.now())
    df_r = df_base[(df_base['DT'].dt.date >= i) & (df_base['DT'].dt.date <= f)]
    
    bancos_txt = "".join([f"• {b}: {m_fmt(df_base[df_base['Banco'] == b]['V_Real'].sum())}\n" for b in sorted(df_base['Banco'].unique())])
    msg = (f"*Relatório Wilson*\nREC: {m_fmt(df_r[df_r['Tipo']=='Receita']['V_Num'].sum())}\nDES: {m_fmt(-df_r[df_r['Tipo']=='Despesa']['V_Num'].sum())}\n"
           f"REND: {m_fmt(df_r[df_r['Tipo']=='Rendimento']['V_Num'].sum())}\nPEND: {m_fmt(df_r[df_r['Status']=='Pendente']['V_Num'].sum())}\n\n"
           f"*Saldos:*\n{bancos_txt}\n*PATRIMÔNIO:* {m_fmt(df_base['V_Real'].sum())}")
    st.text_area("Mensagem:", msg, height=250)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank">📲 ENVIAR WHATSAPP</a>', unsafe_allow_html=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.table(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])
