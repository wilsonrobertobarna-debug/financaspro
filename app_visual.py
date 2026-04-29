import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="FinançasPro Wilson v3.1", layout="wide")

@st.cache_resource
def conectar():
    try:
        creds_dict = st.secrets["connections"]["gsheets"]
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key": pk, "client_email": creds_dict["client_email"], 
            "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except: return None

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
ws = sh.get_worksheet(0)

@st.cache_data(ttl=2)
def carregar_dados():
    dados = ws.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    df['ID_Planilha'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    return df

df_base = carregar_dados()
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# --- 2. MENU LATERAL ---
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças (Geral)", "📄 Relatório WhatsApp", "✏️ Editar Lançamento", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

st.sidebar.divider()

with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data Inicial", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor da Parcela", min_value=0.0)
        f_des = st.text_input("Descrição")
        f_par = st.number_input("Total de Parcelas", min_value=1, value=1)
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Obra", "Outros"])
        f_bnc = st.selectbox("Banco", ["Santander", "Itaú", "Inter", "Nubank", "Pix", "Dinheiro"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(int(f_par)):
                dt_p = (f_dat + relativedelta(months=i)).strftime("%d/%m/%Y")
                desc_p = f"{f_des} [{i+1}/{int(f_par)}]" if f_par > 1 else f_des
                ws.append_row([dt_p, v_str, desc_p, f_cat, "Despesa", f_bnc, "Pago"])
            st.cache_data.clear(); st.rerun()

# --- 3. TELAS ---

if aba == "💰 Finanças (Geral)":
    st.title("🛡️ Resumo Geral")
    if not df_base.empty:
        rec = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        des = df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.metric("Saldo Atual", m_fmt(rec - des))
        st.dataframe(df_base.sort_values('DT', ascending=False), 
                     column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Categoria", "Banco", "Status"), 
                     use_container_width=True, hide_index=True)

elif aba == "📄 Relatório WhatsApp":
    st.title("📄 Relatório Wilson")
    d1 = st.date_input("Início", datetime.now() - relativedelta(days=30), format="DD/MM/YYYY")
    d2 = st.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
    if st.button("GERAR"):
        df_p = df_base[(df_base['DT'].dt.date >= d1) & (df_base['DT'].dt.date <= d2)]
        rec = df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum()
        des = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
        rel = f"RELATÓRIO WILSON\nPeríodo: {d1.strftime('%d/%m/%Y')} a {d2.strftime('%d/%m/%Y')}\n"
        rel += "========================================\n"
        rel += f"REC: {m_fmt(rec)}\nDES: {m_fmt(des)}\nSOBRA: {m_fmt(rec - des)}\n"
        rel += "========================================\n\nSALDOS:\n"
        bancos = df_p.groupby('Banco')['V_Num'].sum()
        for b, v in bancos.items(): rel += f"- {b}: {m_fmt(v)}\n"
        st.text_area("Copiável:", rel, height=250)
        st.link_button("📲 WHATSAPP", f"https://wa.me/?text={urllib.parse.quote(rel)}")

elif aba == "✏️ Editar Lançamento":
    st.title("✏️ Editar")
    id_e = st.number_input("ID do Item:", min_value=2, step=1)
    it = df_base[df_base['ID_Planilha'] == id_e]
    if not it.empty:
        with st.form("ed_w"):
            n_d = st.date_input("Data", it['DT'].iloc[0].to_pydatetime(), format="DD/MM/YYYY")
            n_v = st.number_input("Valor", float(it['V_Num'].iloc[0]))
            n_t = st.text_input("Descrição", it['Descrição'].iloc[0])
            n_st = st.selectbox("Status", ["Pago", "Pendente"], index=0 if it['Status'].iloc[0] == "Pago" else 1)
            if st.form_submit_button("SALVAR"):
                ws.update_cell(id_e, 1, n_d.strftime("%d/%m/%Y")); ws.update_cell(id_e, 2, f"{n_v:.2f}".replace('.', ',')); ws.update_cell(id_e, 3, n_t); ws.update_cell(id_e, 7, n_st)
                st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Painel de Cuidado: Milo & Bolt")
    
    # 1. Indicadores Rápidos
    df_p = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False)].copy()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Gasto (Histórico)", m_fmt(df_p['V_Num'].sum()))
    
    # Filtro de Gastos em Saúde (Veterinário, Vacina, Remédios)
    saude = df_p[df_p['Descrição'].str.contains('Vet|Vacina|Vermif|Remed|Saude', case=False, na=False)]
    c2.metric("Investimento em Saúde", m_fmt(saude['V_Num'].sum()))
    
    # Última compra de ração/mimo
    mimos = df_p[df_p['Descrição'].str.contains('Ração|Petisco|Brinquedo', case=False, na=False)]
    if not mimos.empty:
        c3.metric("Último Mimo/Ração", m_fmt(mimos.iloc[-1]['V_Num']))

    # 2. Checklist de Saúde (Interativo apenas na interface)
    st.divider()
    st.subheader("🏥 Cronograma de Saúde Wilson")
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.info("**Checklist Milo (Golden Retriever)**")
        st.checkbox("Vacina V10 (Anual)")
        st.checkbox("Vacina Raiva (Anual)")
        st.checkbox("Antipulgas / Carrapatos (Em dia?)")
        st.checkbox("Vermífugo (Em dia?)")
        
    with col_b:
        st.info("**Checklist Bolt**")
        st.checkbox("Vacina V10/V8")
        st.checkbox("Vacina Raiva")
        st.checkbox("Antipulgas / Carrapatos")
        st.checkbox("Vermífugo")

    # 3. Tabela de Gastos
    st.divider()
    st.subheader("📑 Histórico de Lançamentos")
    st.dataframe(df_p.sort_values('DT', ascending=False), 
                 column_order=("ID_Planilha", "Data", "Descrição", "Valor", "Status"), 
                 use_container_width=True, hide_index=True)

elif aba == "🚗 Meu Veículo":
    st.title("🚗 Gestão Veicular")
    st.subheader("⛽ Calculadora Álcool x Gasolina")
    ca, cg = st.columns(2)
    p_alc = ca.number_input("Preço Álcool", min_value=0.0)
    p_gas = cg.number_input("Preço Gasolina", min_value=0.0)
    if p_gas > 0:
        if p_alc / p_gas <= 0.7: st.success("✅ Vá de ÁLCOOL")
        else: st.warning("⛽ Vá de GASOLINA")
    
    df_v = df_base[df_base['Categoria'].str.contains('Veículo|Combustível', case=False, na=False)]
    st.dataframe(df_v.sort_values('DT', ascending=False), use_container_width=True, hide_index=True)
