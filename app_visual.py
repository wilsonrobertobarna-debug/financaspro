import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. CONEXÃO COM GOOGLE SHEETS
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
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws_base = sh.get_worksheet(0)

# 3. CARREGAMENTO E TRATAMENTO DE DADOS
@st.cache_data(ttl=2)
def carregar():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Linha'] = range(2, len(df) + 2) # ID para controle interno
    
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
        
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): 
    return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO E LANÇAMENTOS
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 Relatórios"])

st.sidebar.divider()

# FORMULÁRIO DE NOVO LANÇAMENTO (COM PARCELAS)
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay"])
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

# TRANSFERÊNCIA ENTRE CONTAS
with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01)
        t_orig = st.selectbox("Origem (Sai):", ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix"])
        t_dest = st.selectbox("Destino (Entra):", ["Nubank", "Itaú", "Inter", "Santander", "Dinheiro", "Pix"])
        t_desc = st.text_input("Nota")
        
        if st.form_submit_button("EFETUAR TRANSFERÊNCIA"):
            if t_orig == t_dest: 
                st.error("Escolha bancos diferentes!")
            else:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago"])
                st.cache_data.clear(); st.rerun()

# 5. CONTEÚDO DAS TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        # Resumo Patrimonial
        rec_t = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des_t = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL: {m_fmt(rec_t - des_t)}")

        # Métricas do Mês
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Despesas", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimentos", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendentes", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        # Gráficos
        st.divider()
        g1, g2 = st.columns(2)
        with g1:
            df_cat = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_cat.empty:
                st.plotly_chart(px.pie(df_cat, values='V_Num', names='Categoria', title="Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_fluxo = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_fluxo.empty:
                st.plotly_chart(px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', title="Fluxo de Caixa Mensal"), use_container_width=True)

        # Tabela de Lançamentos
        st.subheader("🔍 Lançamentos Recentes")
        b_desc = st.text_input("Filtrar por descrição:")
        df_v = df_base.copy()
        if b_desc: 
            df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
        st.dataframe(df_v, column_order=("Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), use_container_width=True, hide_index=True)

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Gestão Milo & Bolt")
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)]
    if not df_pet.empty:
        st.metric("Total Gasto com Pets", m_fmt(df_pet['V_Num'].sum()))
        st.dataframe(df_pet, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum gasto registrado para os pets.")

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão do Veículo")
    v1, v2, v3 = st.columns([1, 1, 2])
    alc = v1.number_input("Álcool (R$)", value=0.0)
    gas = v2.number_input("Gasolina (R$)", value=0.0)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: v3.success("💡 RECOMENDAÇÃO: ABASTEÇA COM ÁLCOOL!")
        else: v3.warning("💡 RECOMENDAÇÃO: ABASTEÇA COM GASOLINA!")
    
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.metric("Gasto Total com Veículo", m_fmt(df_car['V_Num'].sum()))
        st.dataframe(df_car, column_order=("Data", "Descrição", "Valor", "Status", "Banco"), use_container_width=True, hide_index=True)

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    r1, r2 = st.columns(2)
    d_ini = r1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = r2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
    
    if not df_base.empty:
        df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
        if not df_per.empty:
            sobra = df_per[df_per['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_per[df_per['Tipo'] == 'Despesa']['V_Num'].sum()
            txt_relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n====================\nSOBRA: {m_fmt(sobra)}"
            st.text_area("Relatório para Copiar:", txt_relat, height=150)
            st.link_button("📲 Enviar para WhatsApp", f"https://wa.me/?text={urllib.parse.quote(txt_relat)}")
        else:
            st.warning("Nenhum dado no período selecionado.")

# 6. EDIÇÃO E EXCLUSÃO (SIDEBAR)
st.sidebar.divider()
if not df_base.empty:
    with st.sidebar.expander("⚙️ Ajustar Lançamento"):
        lista = [f"{r['Data']} - {r['Descrição']}" for _, r in df_base.head(20).iterrows()]
        selecao = st.selectbox("Escolha para editar/excluir:", [""] + lista)
        if selecao:
            st.write("Função de edição em manutenção.")
