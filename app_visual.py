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

# 3. CARREGAMENTO E FORMATAÇÃO
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
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
    f_bnc = st.selectbox("Banco", ["Dinheiro", "Pix", "Inter", "Itau - Fabiana", "Itau - Wilson", "Itau - Previdencia Vinicius", "Itau - Previdencia Fabiana", "Caixa Economica Federal", "Mercado Pago", "PicPay", "PagBank", "Invest - XP", "Invest - PagBank", "Invest Inter CDB", "Invest Inter Conserv.FIRF", "Invest Inter HEDGE", "Invest. Inter LCI", "Invest. Inter Tesouro Direto"])
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
    c_g1, c_g2 = st.columns(2)
    with c_g1:
        df_evol = df_base.groupby(['Ano_Mes_Sort', 'Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
        st.plotly_chart(px.bar(df_evol[df_evol['Tipo'].isin(['Receita', 'Despesa'])], x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="Evolução Mensal"), use_container_width=True)
    with c_g2:
        metas = {"Mercado": 1200.0, "Aluguel": 2500.0, "Pet: Milo": 500.0, "Pet: Bolt": 500.0}
        gastos_cat = df_m[df_m['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        gastos_cat['Meta'] = gastos_cat['Categoria'].map(metas).fillna(500.0)
        fig_m = go.Figure()
        fig_m.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['V_Num'], name='Real', marker_color='#EF553B'))
        fig_m.add_trace(go.Bar(x=gastos_cat['Categoria'], y=gastos_cat['Meta'], name='Meta', marker_color='#3B82F6', opacity=0.4))
        st.plotly_chart(fig_m.update_layout(title="Gasto x Meta", barmode='overlay'), use_container_width=True)

    st.divider()
    st.write("### 🔍 Pesquisa e Ações")
    psq = st.text_input("Buscar Descrição:")
    df_f = df_base[df_base['Descrição'].str.contains(psq, case=False, na=False)] if psq else df_base
    st.dataframe(df_f[['Data', 'Descrição', 'Valor', 'Tipo', 'Banco', 'Status']].iloc[::-1], use_container_width=True)

    t1, t2, t3 = st.tabs(["💸 Transferência", "📝 Alterar", "🚨 Excluir"])
    with t1:
        with st.form("transf"):
            tv = st.number_input("Valor", 0.0); td = st.text_input("Descrição", "Transferência")
            co, cd = st.columns(2)
            to = co.selectbox("Sai de:", sorted(df_base['Banco'].unique())); tdest = cd.selectbox("Entra em:", sorted(df_base['Banco'].unique()))
            if st.form_submit_button("EXECUTAR"):
                hj = datetime.now().strftime("%d/%m/%Y"); vs = f"{tv:.2f}".replace('.', ',')
                ws_base.append_rows([[hj, vs, td, "Transferência", "Despesa", to, "Pago"], [hj, vs, td, "Transferência", "Receita", tdest, "Pago"]])
                st.cache_data.clear(); st.rerun()
    with t2:
        ult = {f"{r['Data']} | {r['Descrição']}": r for _, r in df_base.tail(20).iterrows()}
        sel = st.selectbox("Lançamento:", [""] + list(ult.keys()))
        if sel:
            it = ult[sel]
            with st.form("edit"):
                edat = st.text_input("Data", it['Data']); edesc = st.text_input("Descrição", it['Descrição'])
                eval = st.text_input("Valor", it['Valor']); ebnc = st.selectbox("Banco", sorted(df_base['Banco'].unique()), index=sorted(df_base['Banco'].unique()).index(it['Banco']))
                if st.form_submit_button("SALVAR"):
                    ws_base.update(f"A{it['ID_Linha']}:G{it['ID_Linha']}", [[edat, eval, edesc, it['Categoria'], it['Tipo'], ebnc, it['Status']]])
                    st.cache_data.clear(); st.rerun()
    with t3:
        excl = st.selectbox("Excluir:", [""] + list(ult.keys()), key="ex")
        if st.button("CONFIRMAR EXCLUSÃO") and excl:
            ws_base.delete_rows(int(ult[excl]['ID_Linha'])); st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Milo & Bolt")
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False)].copy()
    st.metric("Gasto Total Pets", m_fmt(df_p['V_Num'].sum()))
    df_p_m = df_p.groupby(['Ano_Mes_Sort', 'Mes_Ano'])['V_Num'].sum().reset_index()
    st.plotly_chart(px.bar(df_p_m, x='Mes_Ano', y='V_Num', title="Gastos Mensais Pets"), use_container_width=True)
    st.dataframe(df_p[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Meu Veículo")
    v1, v2 = st.columns(2)
    a = v1.number_input("Álcool", 0.0); g = v2.number_input("Gasolina", 0.0)
    if a > 0 and g > 0:
        st.success("Vá de ÁLCOOL!") if a/g <= 0.7 else st.warning("Vá de GASOLINA!")
    df_v = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])].copy()
    st.dataframe(df_v[['Data', 'Descrição', 'Valor', 'Status']].iloc[::-1], use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato Bancário")
    b_sel = st.selectbox("Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    df_b['Saldo'] = df_b['Saldo_Acum'].apply(m_fmt)
    st.dataframe(df_b[['Data', 'Descrição', 'Valor', 'Saldo']].iloc[::-1], use_container_width=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório para WhatsApp")
    c1, c2 = st.columns(2)
    d_i = c1.date_input("Início", datetime.now().replace(day=1))
    d_f = c2.date_input("Fim", datetime.now())
    
    df_r = df_base[(df_base['DT'].dt.date >= d_i) & (df_base['DT'].dt.date <= d_f)]
    rec = df_r[df_r['Tipo'] == 'Receita']['V_Num'].sum()
    des = df_r[df_r['Tipo'] == 'Despesa']['V_Num'].sum()
    rend = df_r[df_r['Tipo'] == 'Rendimento']['V_Num'].sum()
    sobra = rec - des
    
    bancos_txt = ""
    for b in ["Dinheiro", "Pix", "Inter", "Itau - Fabiana", "Itau - Wilson", "Itau - Previdencia Vinicius", "Itau - Previdencia Fabiana", "Caixa Economica Federal", "Mercado Pago", "PicPay", "PagBank", "Invest - XP", "Invest - PagBank", "Invest Inter CDB", "Invest Inter Conserv.FIRF", "Invest Inter HEDGE", "Invest. Inter LCI", "Invest. Inter Tesouro Direto"]:
        valor_b = df_base[df_base['Banco'] == b]['V_Real'].sum()
        if valor_b != 0: bancos_txt += f"- {b}: {m_fmt(valor_b)}\n"

    msg = (f"RELATÓRIO WILSON\n"
           f"Período: {d_i.strftime('%d/%m/%Y')} a {d_f.strftime('%d/%m/%Y')}\n"
           f"========================================\n"
           f"REC: {m_fmt(rec)}\n"
           f"DES: {m_fmt(des)}\n"
           f"REND: {m_fmt(rend)}\n"
           f"SOBRA: {m_fmt(sobra)}\n"
           f"========================================\n\n"
           f"SALDOS:\n{bancos_txt}"
           f"TOTAL BANCOS: {m_fmt(df_base['V_Real'].sum())}\n"
           f"TOTAL CARTÕES: R$ 0,00\n"
           f"PATRIMÔNIO: {m_fmt(df_base['V_Real'].sum())}")
    
    st.text_area("Modelo WhatsApp:", msg, height=400)
    st.markdown(f'<a href="https://wa.me/?text={urllib.parse.quote(msg)}" target="_blank">📲 ENVIAR PARA WHATSAPP</a>', unsafe_allow_html=True)
