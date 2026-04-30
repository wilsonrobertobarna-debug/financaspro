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

st.markdown("""
    <style>
    [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

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

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Pets", "🚗 Veículo", "📲 WhatsApp", "📄 Relatório PDF"])

st.sidebar.divider()

# NOVO LANÇAMENTO
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

# TRANSFERÊNCIA (COM DESCRIÇÃO)
with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        t_des = st.text_input("Descrição", "Transferência")
        t_orig = st.selectbox("Sai de:", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        t_dest = st.selectbox("Entra em:", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
        if st.form_submit_button("EXECUTAR"):
            v_str = f"{t_val:.2f}".replace('.', ',')
            d_str = t_dat.strftime("%d/%m/%Y")
            ws_base.append_row([d_str, v_str, f"{t_des} (Saída)", "Transferência", "Despesa", t_orig, "Pago"])
            ws_base.append_row([d_str, v_str, f"{t_des} (Entrada)", "Transferência", "Receita", t_dest, "Pago"])
            st.cache_data.clear(); st.rerun()

# ALTERAR / EXCLUIR (SOMENTE DATA E VALOR)
with st.sidebar.expander("⚙️ Alterar / Excluir", expanded=False):
    if not df_base.empty:
        lista_edit = {f"{r['ID']} / {r['Data']} / {r['Descrição']} / R$ {r['Valor']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione o item:", [""] + list(lista_edit.keys()))
        
        if escolha:
            item = lista_edit[escolha]
            data_objeto = datetime.strptime(item['Data'], "%d/%m/%Y").date()
            ed_dat = st.date_input("Nova Data:", value=data_objeto, format="DD/MM/YYYY")
            ed_val = st.number_input("Novo Valor:", value=float(item['V_Num']), step=0.01, format="%.2f")
            ed_sta = st.selectbox("Novo Status:", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
            
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.button("💾 Salvar"):
                v_str_edit = f"{ed_val:.2f}".replace('.', ',')
                d_str_edit = ed_dat.strftime("%d/%m/%Y")
                ws_base.update_cell(int(item['ID']), 1, d_str_edit) 
                ws_base.update_cell(int(item['ID']), 2, v_str_edit) 
                ws_base.update_cell(int(item['ID']), 7, ed_sta)     
                st.cache_data.clear(); st.rerun()
            
            if c_ed2.button("🚨 Excluir"):
                ws_base.delete_rows(int(item['ID']))
                st.cache_data.clear(); st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(saldo_geral)}")
        
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Receitas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("Despesas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        
        # 🎯 GRÁFICO DE METAS (RESTAURADO)
        with st.expander("🎯 Metas de Gastos", expanded=True):
            todas_cats = sorted(df_base[df_base['Tipo']=='Despesa']['Categoria'].unique())
            if "Transferência" in todas_cats: todas_cats.remove("Transferência")
            
            metas_map = {}
            cols_m = st.columns(3)
            # Definindo metas padrão ou deixando Wilson editar
            for i, cat in enumerate(todas_cats):
                metas_map[cat] = cols_m[i % 3].number_input(f"Meta: {cat}", value=1500.0, key=f"meta_{cat}")
            
            # Cálculo para o Gráfico de Metas
            df_gastos_cat = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            
            fig_metas = go.Figure()
            for cat in todas_cats:
                gasto_atual = df_gastos_cat[df_gastos_cat['Categoria'] == cat]['V_Num'].sum()
                meta_valor = metas_map[cat]
                
                # Barra de Fundo (Meta)
                fig_metas.add_trace(go.Bar(y=[cat], x=[meta_valor], name='Meta', orientation='h', marker_color='rgba(52, 152, 219, 0.3)', showlegend=False))
                # Barra de Cima (Gasto)
                cor_barra = '#e74c3c' if gasto_atual > meta_valor else '#2ecc71'
                fig_metas.add_trace(go.Bar(y=[cat], x=[gasto_atual], name='Gasto', orientation='h', marker_color=cor_barra, showlegend=False))
            
            fig_metas.update_layout(barmode='overlay', title="Progresso das Metas (Gasto vs Meta)", height=400)
            st.plotly_chart(fig_metas, use_container_width=True)

        # OUTROS GRÁFICOS
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty:
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="Gastos por Categoria", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty:
                st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', title="Fluxo do Mês", 
                                     color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}), use_container_width=True)

        st.divider()
        st.subheader("🔍 Lançamentos")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Bco:", sorted(df_base['Banco'].unique()))
        s_sta = c2.multiselect("Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Busca:")
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        st.dataframe(df_v[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Pets")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Gasto Pets (Mês)", m_fmt(df_pet[df_pet['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        st.dataframe(df_pet[['Data', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "🚗" in aba:
    st.title("🚗 Veículo")
    st.subheader("⛽ Álcool ou Gasolina?")
    col_c1, col_c2, col_c3 = st.columns([1, 1, 2])
    p_alc = col_c1.number_input("Álcool", min_value=0.0, step=0.01)
    p_gas = col_c2.number_input("Gasolina", min_value=0.0, step=0.01)
    if p_alc > 0 and p_gas > 0:
        res = p_alc / p_gas
        if res <= 0.7: col_c3.success(f"✅ VÁ DE ÁLCOOL ({res:.2%})")
        else: col_c3.warning(f"✅ VÁ DE GASOLINA ({res:.2%})")
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    st.dataframe(df_car[['Data', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

# (Restante das abas WhatsApp e PDF mantidos como antes...)
