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
        escopos = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        credentials = Credentials.from_service_account_info(final_creds, scopes=escopos)
        return gspread.authorize(credentials)
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

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
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

# CAMPO DE METAS (O que tinha sumido!)
st.sidebar.divider()
st.sidebar.subheader("🎯 Minha Meta")
meta_valor = st.sidebar.number_input("Definir Meta Mensal (R$)", min_value=0.0, value=2000.0, step=100.0)

st.sidebar.divider()
# BARRINHAS DE AÇÃO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            ws_base.append_row([f_dat.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_l = df_m[df_m['Categoria'] != 'Transferência']
        
        receitas = df_l[df_l['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesas = df_l[df_l['Tipo'] == 'Despesa']['V_Num'].sum()
        saldo_mes = receitas - despesas

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Receitas", m_fmt(receitas))
        c2.metric("📉 Despesas", m_fmt(despesas))
        c3.metric("⚖️ Saldo Mês", m_fmt(saldo_mes))
        c4.metric("🎯 Meta Definida", m_fmt(meta_valor))
        
        st.divider()
        
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Progresso da Meta")
            fig_meta = go.Figure(go.Indicator(
                mode = "gauge+number",
                value = saldo_mes,
                number = {'prefix': "R$ ", 'font': {'size': 20}},
                domain = {'x': [0, 1], 'y': [0, 1]},
                gauge = {
                    'axis': {'range': [None, meta_valor if meta_valor > 0 else 1000]},
                    'bar': {'color': "darkblue"},
                    'steps': [
                        {'range': [0, meta_valor*0.5], 'color': "lightgray"},
                        {'range': [meta_valor*0.5, meta_valor], 'color': "gray"}],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': meta_valor}
                }
            ))
            st.plotly_chart(fig_meta, use_container_width=True)

        with g2:
            st.subheader("Distribuição de Gastos")
            if not df_l[df_l['Tipo']=='Despesa'].empty:
                fig_p = px.pie(df_l[df_l['Tipo']=='Despesa'], values='V_Num', names='Categoria', hole=0.4)
                st.plotly_chart(fig_p, use_container_width=True)

        st.divider()
        st.subheader("📑 Lançamentos do Mês")
        st.dataframe(df_m.iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão de Veículo")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    if not df_v.empty:
        total_v = df_v[df_v['Mes_Ano'] == mes_atual]['V_Num'].sum()
        st.info(f"### Total Gasto com Veículo no Mês: {m_fmt(total_v)}")
        
        st.subheader("Histórico Detalhado")
        st.dataframe(df_v.iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    d1 = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d2 = st.date_input("Fim", datetime.now())
    df_p = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    
    if not df_p.empty:
        rec = df_p[df_p['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
        sobra = rec - des
        
        rel = f"RELATÓRIO WILSON\nPeríodo: {d1.strftime('%d/%m/%Y')} a {d2.strftime('%d/%m/%Y')}\n"
        rel += f"========================================\nREC/REND: {m_fmt(rec)}\nDESPESAS: {m_fmt(des)}\nSOBRA: {m_fmt(sobra)}\n========================================\n\n"
        
        st.text_area("Conteúdo do Relatório", rel, height=250)
        st.markdown(f'[📲 Enviar WhatsApp](https://wa.me/?text={urllib.parse.quote(rel)})')
