import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import datetime

# 1. CONFIGURAÇÃO E ESTILO (CSS para tags menores e organizadas)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    [data-testid="stMetricValue"] { font-size: 1.6rem !important; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem !important; }
    .stMetric { background-color: #f8f9fa; padding: 10px; border-radius: 8px; border: 1px solid #dee2e6; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SEGURA COM O GOOGLE SHEETS
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# --- FUNÇÃO DE TABELA DINÂMICA (Para exibir os dados abaixo dos gráficos) ---
def exibir_tabela_dinamica(aba_sheet, titulo):
    dados = aba_sheet.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        try:
            col_data = dados[0][0]
            df['Data_Sort'] = pd.to_datetime(df[col_data], dayfirst=True, errors='coerce')
            df = df.sort_values(by='Data_Sort', ascending=False).drop(columns=['Data_Sort'])
        except: pass
        st.subheader(f"📋 {titulo}")
        st.dataframe(df, use_container_width=True)

# 3. INTERFACE DE NAVEGAÇÃO LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# ==========================================
# ABA 1: FINANÇAS (DASHBOARD COLORIDO)
# ==========================================
if aba == "💰 Finanças":
    ws = sh.get_worksheet(0)
    st.title("🛡️ FinançasPro - Central Wilson")
    
    dados = ws.get_all_values()
    if len(dados) > 1:
        df = pd.DataFrame(dados[1:], columns=dados[0])
        df['Valor_Num'] = pd.to_numeric(df['Valor'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
        
        # Travas de segurança para nomes de colunas
        c_tipo = 'Tipo' if 'Tipo' in df.columns else (df.columns[3] if len(df.columns) > 3 else None)
        c_status = 'Status' if 'Status' in df.columns else ('Descrição' if 'Descrição' in df.columns else None)
        c_cat = 'Categoria' if 'Categoria' in df.columns else (df.columns[2] if len(df.columns) > 2 else None)

        # Cálculos para as Tags (Métricas)
        rec = df[df[c_tipo] == 'Receita']['Valor_Num'].sum() if c_tipo else 0
        desp = df[df[c_tipo] == 'Despesa']['Valor_Num'].sum() if c_tipo else 0
        rend = df[df[c_cat] == 'Rendimento']['Valor_Num'].sum() if c_cat else 0
        pend = df[df[c_status] == 'Pendente']['Valor_Num'].sum() if c_status else 0
        
        def format_brl(v): return f"R$ {v:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        
        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("🟢 Receitas", format_brl(rec))
        c2.metric("🔴 Despesas", format_brl(desp))
        c3.metric("💎 Saldo", format_brl(rec - desp))
        c4.metric("📈 Rend.", format_brl(rend))
        c5.metric("⏳ Pend.", format_brl(pend))

        st.write("---")
        g1, g2 = st.columns(2)

        with g1:
            st.subheader("📊 Receitas x Despesas Mensal")
            try:
                df['Data_DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                df['Mes_Ano'] = df['Data_DT'].dt.strftime('%m/%y')
                comp = df.groupby(['Mes_Ano', c_tipo])['Valor_Num'].sum().unstack().fillna(0)
                
                # CORES: Verde para Receita (#28a745), Vermelho para Despesa (#dc3545)
                cores_grafico = []
                if 'Receita' in comp.columns: cores_grafico.append('#28a745')
                if 'Despesa' in comp.columns: cores_grafico.append('#dc3545')
                
                st.bar_chart(comp, color=cores_grafico)
            except: st.info("Adicione dados com datas para ver o gráfico.")

        with g2:
            st.subheader("🍕 Gastos por Categoria")
            if c_tipo:
                gastos_cat = df[df[c_tipo] == 'Despesa'].groupby(c_cat)['Valor_Num'].sum()
                st.bar_chart(gastos_cat, color='#ffc107') # Amarelo para categorias

    with st.sidebar.form("f_fin", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor (R$)", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Shopee", "AserNet", "Skyfit", "Milo/Bolt", "Combustível", "Rendimento", "Outros"])
        f_stat = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("🚀 SALVAR FINANCEIRO"):
            ws.append_row([f_dat.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), f_cat, f_tip, "Nubank", f_stat])
            st.cache_data.clear(); st.rerun()
            
    exibir_tabela_dinamica(ws, "Histórico Geral")

# ==========================================
# ABA 2: MILO & BOLT
# ==========================================
elif aba == "🐾 Milo & Bolt":
    ws = sh.worksheet("Controle_Pets")
    st.title("🐾 Cuidados: Milo & Bolt")
    with st.sidebar.form("f_pet", clear_on_submit=True):
        p_pet = st.selectbox("Quem?", ["Milo", "Bolt", "Os Dois"])
        p_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        p_tip = st.selectbox("Tipo", ["Ração", "Vacina", "Banho", "Saúde"])
        p_val = st.number_input("Valor (R$)", min_value=0.0)
        if st.form_submit_button("🦴 SALVAR NO PET"):
            dt_s = p_dat.strftime("%d/%m/%Y")
            ws.append_row([dt_s, p_pet, p_tip, "Lançamento App", str(p_val).replace('.', ',')])
            sh.get_worksheet(0).append_row([dt_s, str(p_val).replace('.', ','), f"Pet: {p_tip}", "Despesa", "Nubank", "Pago"])
            st.cache_data.clear(); st.rerun()
    exibir_tabela_dinamica(ws, "Histórico dos Pets")

# ==========================================
# ABA 3: MEU VEÍCULO
# ==========================================
else:
    ws = sh.worksheet("Controle_Veiculo")
    st.title("🚗 Controle do Veículo")
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("⛽ Calculadora Flex")
        alc = st.number_input("Preço Álcool", min_value=0.0)
        gas = st.number_input("Preço Gasolina", min_value=0.0)
        if alc > 0 and gas > 0:
            res = alc / gas
            st.metric("Proporção", f"{res:.2f}")
            if res <= 0.7: st.success("VÁ DE ÁLCOOL! ✅")
            else: st.warning("VÁ DE GASOLINA! ⛽")
    with c2:
        with st.sidebar.form("f_vei", clear_on_submit=True):
            v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            v_tip = st.selectbox("Serviço", ["Abastecimento", "Troca de Óleo", "Manutenção", "Lavagem"])
            v_det = st.text_input("Descrição (Ex: Posto)")
            v_km = st.number_input("KM Atual", min_value=0)
            v_val = st.number_input("Valor Pago", min_value=0.0)
            if st.form_submit_button("🚗 SALVAR NO VEÍCULO"):
                dt_s = v_dat.strftime("%d/%m/%Y")
                # Ordem: Data, Serviço, Descrição, KM, Valor
                ws.append_row([dt_s, v_tip, v_det, str(v_km), str(v_val).replace('.', ',')])
                sh.get_worksheet(0).append_row([dt_s, str(v_val).replace('.', ','), f"Veículo: {v_tip}", "Despesa", "Nubank", "Pago"])
                st.cache_data.clear(); st.rerun()
    exibir_tabela_dinamica(ws, "Histórico do Veículo")
