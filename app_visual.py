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

# 3. CARREGAMENTO
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Linha'] = range(2, len(df) + 2)
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

# 4. SIDEBAR
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
        for i in range(f_par):
            nova_dt = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
            ws_base.append_row([nova_dt, f"{f_val:.2f}".replace('.', ','), f_des, f_cat, f_tip, f_bnc, f_sta])
        st.cache_data.clear(); st.rerun()

# 5. TELA DE FINANÇAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(df_base['V_Real'].sum())}")
    
    df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📈 Receita", m_fmt(df_m[df_m['Tipo'] == 'Receita']['V_Num'].sum()))
    m2.metric("📉 Gasto", m_fmt(df_m[df_m['Tipo'] == 'Despesa']['V_Num'].sum()))
    m3.metric("💰 Rendimento", m_fmt(df_m[df_m['Tipo'] == 'Rendimento']['V_Num'].sum()))
    m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
    
    st.divider()
    # --- GRÁFICOS RESTAURADOS ---
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        fig_evol = px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', 
                          title="Evolução Mensal (Rec x Desp)", color_discrete_map={'Receita': '#00CC96', 'Despesa': '#EF553B'})
        st.plotly_chart(fig_evol, use_container_width=True)
    with col_g2:
        metas = {"Mercado": 1200.0, "Aluguel": 2500.0, "Luz/Água": 400.0, "Internet": 150.0, "Pet: Milo": 500.0, "Pet: Bolt": 500.0, "Veículo": 1000.0}
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        gastos_cat['Meta'] = gastos_cat['Categoria'].map(metas).fillna(500.0)
        fig_meta = go.Figure()
        fig_meta.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['V_Num'], name='Gasto Real', marker_color='#EF553B'))
        fig_meta.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['Meta'], name='Meta', marker_color='#3B82F6', opacity=0.4))
        fig_meta.update_layout(title="Metas por Categoria (Mês Atual)", barmode='overlay')
        st.plotly_chart(fig_meta, use_container_width=True)

    st.divider()
    st.write("### 🔍 Pesquisa")
    p1, p2, p3 = st.columns([1, 1, 2])
    b_p = p1.selectbox("Banco:", ["Todos"] + sorted(df_base['Banco'].unique().tolist()))
    t_p = p2.selectbox("Tipo:", ["Todos", "Receita", "Despesa", "Rendimento"])
    d_p = p3.text_input("Descrição Wilson:")
    df_f = df_base.copy()
    if b_p != "Todos": df_f = df_f[df_f['Banco'] == b_p]
    if t_p != "Todos": df_f = df_f[df_f['Tipo'] == t_p]
    if d_p: df_f = df_f[df_f['Descrição'].str.contains(d_p, case=False, na=False)]
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Categoria', 'Status']].iloc[::-1], use_container_width=True)

    st.divider()
    st.write("### 🛠️ Ações de Lançamento")
    tab1, tab2, tab3 = st.tabs(["💸 Transferência", "📝 Alteração", "🚨 Exclusão"])

    with tab1:
        with st.form("form_transf", clear_on_submit=True):
            t_v = st.number_input("Valor", min_value=0.0)
            t_desc = st.text_input("Descrição da Transferência", "Transferência entre contas")
            c_o, c_d = st.columns(2)
            t_o = c_o.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Dinheiro"])
            t_d = c_d.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "XP", "Dinheiro"])
            if st.form_submit_button("EXECUTAR"):
                hj = datetime.now().strftime("%d/%m/%Y")
                v_s = f"{t_v:.2f}".replace('.', ',')
                ws_base.append_rows([[hj, v_s, t_desc, "Transferência", "Despesa", t_o, "Pago"], 
                                     [hj, v_s, t_desc, "Transferência", "Receita", t_d, "Pago"]])
                st.cache_data.clear(); st.rerun()

    with tab2:
        ultimos = {f"{r['Data']} | {r['Descrição']} ({r['Valor']})": r for _, r in df_base.tail(20).iterrows()}
        escolha = st.selectbox("Selecione para alterar:", [""] + list(ultimos.keys()))
        if escolha:
            item = ultimos[escolha]
            with st.form("form_alt"):
                a_dat = st.text_input("Data", item['Data'])
                a_des = st.text_input("Descrição", item['Descrição'])
                a_val = st.text_input("Valor", item['Valor'])
                a_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Dinheiro"])
                a_sta = st.selectbox("Status", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
                if st.form_submit_button("SALVAR ALTERAÇÕES"):
                    ws_base.update(f"A{item['ID_Linha']}:G{item['ID_Linha']}", [[a_dat, a_val, a_des, item['Categoria'], item['Tipo'], a_bnc, a_sta]])
                    st.cache_data.clear(); st.rerun()

    with tab3:
        exc_sel = st.selectbox("Lançamento para excluir:", [""] + list(ultimos.keys()))
        if st.button("CONFIRMAR EXCLUSÃO") and exc_sel:
            ws_base.delete_rows(int(ultimos[exc_sel]['ID_Linha']))
            st.cache_data.clear(); st.rerun()

# --- ABAS Milo, Veículo, Extrato e Relatórios ---
elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)]
    st.table(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    st.table(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1])

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato por Banco")
    b_sel = st.selectbox("Selecione o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    st.table(df_b[['Data', 'Descrição', 'Valor', 'Saldo']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório WhatsApp")
    bancos_txt = "".join([f"• {b}: {m_fmt(df_base[df_base['Banco'] == b]['V_Real'].sum())}\n" for b in sorted(df_base['Banco'].unique())])
    msg = f"*Relatório Wilson*\nPATRIMÔNIO: {m_fmt(df_base['V_Real'].sum())}\n\n*Saldos:*\n{bancos_txt}"
    st.text_area("Cópia:", msg, height=200)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank">📲 ENVIAR</a>', unsafe_allow_html=True)
