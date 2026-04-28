import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

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
            "type": creds_dict["type"],
            "project_id": creds_dict["project_id"],
            "private_key": pk,
            "client_email": creds_dict["client_email"],
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro na conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E TRATAMENTO
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
    # Valor real para saldo (Receita + / Despesa -)
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO E LANÇAMENTOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
    f_par = st.number_input("Parcelas", min_value=1, value=1)
    f_des = st.text_input("Descrição / Beneficiário")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
    f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    if st.form_submit_button("SALVAR"):
        v_str = f"{f_val:.2f}".replace('.', ',')
        for i in range(f_par):
            nova_data = f_dat + relativedelta(months=i)
            ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Saldo Geral
        saldo_geral = df_base['V_Real'].sum()
        st.info(f"### 🏦 SALDO TOTAL (TODOS OS BANCOS): {m_fmt(saldo_geral)}")

        # Métricas do Mês
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo de Caixa"), use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato com Saldo Progressivo")
    c1, c2, c3 = st.columns(3)
    b_sel = c1.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    d_ini = c2.date_input("Início", datetime.now() - relativedelta(months=1))
    d_fim = c3.date_input("Fim", datetime.now())
    
    df_banco = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_banco['Saldo_Acum'] = df_banco['V_Real'].cumsum()
    
    mask = (df_banco['DT'].dt.date >= d_ini) & (df_banco['DT'].dt.date <= d_fim)
    df_relat = df_banco.loc[mask].copy()

    if not df_relat.empty:
        df_relat['Saldo Diário'] = ""
        # Marcar saldo apenas no último do dia
        last_indices = df_relat.groupby('DT').tail(1).index
        df_relat.loc[last_indices, 'Saldo Diário'] = df_relat.loc[last_indices, 'Saldo_Acum'].apply(m_fmt)
        
        st.table(df_relat[['Data', 'Descrição', 'Tipo', 'Valor', 'Saldo Diário']].iloc[::-1])
    else:
        st.warning("Sem dados para este período.")

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    st.dataframe(df_pet[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    d1, d2 = st.columns(2)
    ini = d1.date_input("Início Relatório", datetime.now() - relativedelta(months=1))
    fim = d2.date_input("Fim Relatório", datetime.now())
    
    df_p = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    if not df_p.empty:
        txt = f"RELATÓRIO WILSON\nPeríodo: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n"
        txt += f"========================================\n"
        txt += f"REC: {m_fmt(df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum())}\n"
        txt += f"DES: {m_fmt(df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum())}\n"
        txt += f"SOBRA: {m_fmt(df_p['V_Real'].sum())}\n"
        st.text_area("Copiar para Zap", txt, height=300)
        zap = f"https://wa.me/?text={urllib.parse.quote(txt)}"
        st.markdown(f"[📲 Enviar para WhatsApp]({zap})")

# AJUSTAR / EXCLUIR (No final da Sidebar)
st.sidebar.divider()
if not df_base.empty:
    st.sidebar.write("### ⚙️ Editar/Excluir")
    lista = {f"{r['ID']} - {r['Descrição']}": r for _, r in df_base.tail(20).iterrows()}
    item_edit = st.sidebar.selectbox("Escolha:", [""] + list(lista.keys()))
    if item_edit:
        it = lista[item_edit]
        if st.sidebar.button("🚨 EXCLUIR ESTE LANÇAMENTO"):
            ws_base.delete_rows(int(it['ID']))
            st.cache_data.clear(); st.rerun()
