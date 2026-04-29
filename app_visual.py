import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO (BLINDADA)
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
st.sidebar.divider()

# BARRINHAS NA LATERAL
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf"):
        t_dat = st.date_input("Data", datetime.now())
        t_val = st.number_input("Valor", min_value=0.0)
        t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro"])
        t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro"])
        if st.form_submit_button("EXECUTAR"):
            v_str = f"{t_val:.2f}".replace('.', ',')
            ws_base.append_row([t_dat.strftime("%d/%m/%Y"), v_str, "TR Saída", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([t_dat.strftime("%d/%m/%Y"), v_str, "TR Entrada", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

with st.sidebar.expander("⚙️ Ajustar / Excluir", expanded=False):
    if not df_base.empty:
        lista = {f"{r['Data']} - {r['Descrição']}": r for _, r in df_base.tail(20).iterrows()}
        sel = st.selectbox("Escolha:", [""] + list(lista.keys()))
        if sel:
            item = lista[sel]
            if st.button("🚨 EXCLUIR REGISTRO"):
                ws_base.delete_rows(int(item['ID']))
                st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_l = df_m[df_m['Categoria'] != 'Transferência']
        
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Receitas", m_fmt(df_l[df_l['Tipo'] == 'Receita']['V_Num'].sum()))
        c2.metric("📉 Despesas", m_fmt(df_l[df_l['Tipo'] == 'Despesa']['V_Num'].sum()))
        c3.metric("💰 Rendimentos", m_fmt(df_l[df_l['Tipo'] == 'Rendimento']['V_Num'].sum()))
        c4.metric("⚖️ Saldo Mês", m_fmt((df_l[df_l['Tipo'].isin(['Receita','Rendimento'])]['V_Num'].sum()) - df_l[df_l['Tipo']=='Despesa']['V_Num'].sum()))
        
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            st.subheader("Gastos por Categoria")
            fig_p = px.pie(df_l[df_l['Tipo']=='Despesa'], values='V_Num', names='Categoria', hole=0.4)
            st.plotly_chart(fig_p, use_container_width=True)
        with g2:
            st.subheader("Receita vs Despesa")
            fig_b = px.bar(df_l.groupby('Tipo')['V_Num'].sum().reset_index(), x='Tipo', y='V_Num', color='Tipo')
            st.plotly_chart(fig_b, use_container_width=True)
            
        st.subheader("📑 Últimos Lançamentos")
        st.dataframe(df_base.tail(15).iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão de Veículos")
    df_c = df_base[df_base['Categoria'].isin(['Veículo', 'Combustível', 'Manutenção'])]
    if not df_c.empty:
        st.metric("Total Gasto (Mês)", m_fmt(df_c[df_c['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.subheader("⛽ Histórico de Combustível/Manutenção")
        st.dataframe(df_c.iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    d1 = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d2 = st.date_input("Fim", datetime.now())
    df_p = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    
    if not df_p.empty:
        rec = df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum()
        des = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
        ren = df_p[df_p['Tipo'] == 'Rendimento']['V_Num'].sum()
        sobra = (rec + ren) - des
        
        rel = f"RELATÓRIO WILSON\nPeríodo: {d1.strftime('%d/%m/%Y')} a {d2.strftime('%d/%m/%Y')}\n"
        rel += f"========================================\nREC: {m_fmt(rec)}\nDES: {m_fmt(des)}\nREND: {m_fmt(ren)}\nSOBRA: {m_fmt(sobra)}\n========================================\n\n"
        
        bancos = df_base['Banco'].unique()
        rel += "SALDOS:\n"
        for b in bancos:
            s = df_base[(df_base['Banco']==b) & (df_base['Tipo'].isin(['Receita','Rendimento']))]['V_Num'].sum() - df_base[(df_base['Banco']==b) & (df_base['Tipo']=='Despesa')]['V_Num'].sum()
            rel += f"- {b}: {m_fmt(s)}\n"
            
        st.text_area("Texto do Relatório", rel, height=300)
        st.markdown(f'[📲 Enviar WhatsApp](https://wa.me/?text={urllib.parse.quote(rel)})')
