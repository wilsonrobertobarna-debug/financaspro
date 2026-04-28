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

# 5. TELAS
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
    cg1, cg2 = st.columns(2)
    with cg1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Evolução Mensal"), use_container_width=True)
    with cg2:
        metas = {"Mercado": 1200.0, "Aluguel": 2500.0, "Pet: Milo": 500.0, "Pet: Bolt": 500.0}
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        gastos_cat['Meta'] = gastos_cat['Categoria'].map(metas).fillna(500.0)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['V_Num'], name='Gasto', marker_color='#EF553B'))
        fig.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['Meta'], name='Meta', marker_color='#3B82F6', opacity=0.4))
        st.plotly_chart(fig.update_layout(title="Gasto x Meta", barmode='overlay'), use_container_width=True)

    st.divider()
    st.write("### 🔍 Pesquisa e Gestão")
    psq_txt = st.text_input("Filtrar Descrição Wilson:")
    df_f = df_base[df_base['Descrição'].str.contains(psq_txt, case=False, na=False)] if psq_txt else df_base
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

    t1, t2, t3 = st.tabs(["💸 Transferência", "📝 Alteração", "🚨 Exclusão"])
    with t1:
        with st.form("tr"):
            tv = st.number_input("Valor", 0.0); td = st.text_input("Descrição", "Transferência")
            co, cd = st.columns(2)
            to = co.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "XP", "Dinheiro"])
            tdest = cd.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "XP", "Dinheiro"])
            if st.form_submit_button("EXECUTAR"):
                hj = datetime.now().strftime("%d/%m/%Y"); vs = f"{tv:.2f}".replace('.', ',')
                ws_base.append_rows([[hj, vs, td, "Transferência", "Despesa", to, "Pago"], [hj, vs, td, "Transferência", "Receita", tdest, "Pago"]])
                st.cache_data.clear(); st.rerun()
    with t2:
        ult = {f"{r['Data']} | {r['Descrição']}": r for _, r in df_base.tail(20).iterrows()}
        sel = st.selectbox("Escolha para alterar:", [""] + list(ult.keys()))
        if sel:
            it = ult[sel]
            with st.form("alt"):
                ad = st.text_input("Data", it['Data']); adesc = st.text_input("Descrição", it['Descrição'])
                aval = st.text_input("Valor", it['Valor']); abnc = st.text_input("Banco", it['Banco'])
                asta = st.selectbox("Status", ["Pago", "Pendente"], index=0 if it['Status'] == "Pago" else 1)
                if st.form_submit_button("SALVAR"):
                    ws_base.update(f"A{it['ID_Linha']}:G{it['ID_Linha']}", [[ad, aval, adesc, it['Categoria'], it['Tipo'], abnc, asta]])
                    st.cache_data.clear(); st.rerun()
    with t3:
        sel_ex = st.selectbox("Excluir lançamento:", [""] + list(ult.keys()), key="exc")
        if st.button("EXCLUIR"):
            ws_base.delete_rows(int(ult[sel_ex]['ID_Linha'])); st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)].copy()
    st.metric("Total Gasto Acumulado", m_fmt(df_p['V_Num'].sum()))
    
    # --- GRÁFICO DOS PETS RESTAURADO ---
    df_p_mes = df_p.groupby(['Ano_Mes_Sort', 'Mes_Ano'])['V_Num'].sum().reset_index()
    fig_p = px.bar(df_p_mes, x='Mes_Ano', y='V_Num', title="Gastos Mensais com Milo & Bolt", color_discrete_sequence=['#AB63FA'])
    st.plotly_chart(fig_p, use_container_width=True)
    
    st.dataframe(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    c1, c2 = st.columns(2)
    alc = c1.number_input("Álcool", 0.0); gas = c2.number_input("Gasolina", 0.0)
    if alc > 0 and gas > 0:
        if alc/gas <= 0.7: st.success("Vá de ÁLCOOL!")
        else: st.warning("Vá de GASOLINA!")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])].copy()
    st.dataframe(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato")
    b_sel = st.selectbox("Selecione o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    st.dataframe(df_b[['Data', 'Descrição', 'Valor', 'Saldo']].iloc[::-1], use_container_width=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatórios WhatsApp")
    bancos_txt = "".join([f"• {b}: {m_fmt(df_base[df_base['Banco'] == b]['V_Real'].sum())}\n" for b in sorted(df_base['Banco'].unique())])
    msg = f"*Relatório Wilson*\nPATRIMÔNIO: {m_fmt(df_base['V_Real'].sum())}\n\n*Saldos:*\n{bancos_txt}"
    st.text_area("Cópia:", msg, height=250)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank">📲 ENVIAR</a>', unsafe_allow_html=True)
