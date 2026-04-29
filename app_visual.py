# PROGRAMA: FinançasPro Wilson
# VERSÃO: V 2.1
# STATUS: RESTAURAÇÃO TOTAL (LÓGICA ORIGINAL) + TAGS CURTAS

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
st.sidebar.markdown(f"**Versão:** `V 2.1`")

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
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
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

# 4. SIDEBAR - PAINEL WILSON
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios", "📋 Relatório PDF"])
st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO (Tags Curtas)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parc.", min_value=1, value=1)
        f_des = st.text_input("Desc.")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Cat.", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Bco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# BARRINHA 2: TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01)
        t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        t_dest = st.selectbox("Para:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
        t_desc = st.text_input("Nota")
        if st.form_submit_button("TRANSFERIR"):
            if t_orig != t_dest:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago"])
                st.cache_data.clear(); st.rerun()

# BARRINHA 3: AJUSTE / EXCLUSÃO
with st.sidebar.expander("⚙️ Ajustar", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} | {r['Descrição']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione:", [""] + list(lista_edit.keys()))
        if escolha:
            item = lista_edit[escolha]
            ed_dat = st.date_input("Mudar Data:", value=datetime.strptime(item['Data'], "%d/%m/%Y"), format="DD/MM/YYYY")
            ed_sta = st.selectbox("Status:", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.button("💾 ATUALIZAR"):
                ws_base.update_cell(int(item['ID']), 1, ed_dat.strftime("%d/%m/%Y"))
                ws_base.update_cell(int(item['ID']), 7, ed_sta)
                st.cache_data.clear(); st.rerun()
            if c_ed2.button("🚨 EXCLUIR"):
                ws_base.delete_rows(int(item['ID']))
                st.cache_data.clear(); st.rerun()

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Rec.", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gast.", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rend.", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pend.", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        st.divider()
        with st.expander("🎯 Metas"):
            todas_cats = sorted(df_base['Categoria'].unique())
            metas_map = {cat: st.number_input(f"Meta: {cat}", value=1000.0) for cat in todas_cats if cat != "Transferência"}
        
        # Gráficos
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos (%)", hole=0.4), use_container_width=True)
        with g2:
            df_metas_graph = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_metas_graph.empty:
                df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map).fillna(0.0)
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Real', marker_color='#e74c3c'))
                fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
                fig_m.update_layout(barmode='group', height=350); st.plotly_chart(fig_m, use_container_width=True)

        st.subheader("🔍 Busca")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Bco:", sorted(df_base['Banco'].unique()))
        s_sta = c2.multiselect("Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Busca:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Pets")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto do Mês", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Veículo")
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Álcool", value=0.0)
    gas = c2.number_input("Gasolina", value=0.0)
    if alc > 0 and gas > 0:
        res = "⛽ ÁLCOOL" if (alc/gas) <= 0.7 else "⛽ GASOLINA"
        c3.success(f"Dica: {res}")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório")
    d1 = st.date_input("Início", datetime.now() - relativedelta(months=1))
    d2 = st.date_input("Fim", datetime.now())
    df_per = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
    if not df_per.empty:
        r_v = df_per[df_per['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
        rel = f"RELATÓRIO WILSON\nREC: {m_fmt(r_v)}\nDES: {m_fmt(d_v)}\nSOBRA: {m_fmt(r_v-d_v)}"
        st.text_area("Zap", rel, height=200)
        st.markdown(f'[📲 WhatsApp](https://wa.me/?text={urllib.parse.quote(rel)})')

elif aba == "📋 Relatório PDF":
    st.title("📋 PDF")
    if st.button("GERAR PDF"):
        pdf = FPDF()
        pdf.add_page(); pdf.set_font("Arial", 'B', 14)
        pdf.cell(190, 10, "FinançasPro Wilson", 0, 1, 'C')
        pdf.set_font("Arial", '', 9)
        for _, r in df_base.tail(30).iterrows():
            pdf.cell(190, 7, f"{r['Data']} - {r['Descrição']} - R$ {r['Valor']}", 1, 1)
        st.download_button("📥 Baixar PDF", pdf.output(dest='S').encode('latin-1','replace'), "relatorio.pdf")
