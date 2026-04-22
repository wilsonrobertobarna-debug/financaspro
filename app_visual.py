import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# 2. TELA DE LOGIN (Senha: 1234)
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("🔐 Acesso Wilson")
        senha = st.text_input("Digite a senha:", type="password")
        if st.button("Entrar"):
            if senha == "1234":
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Senha incorreta!")
    st.stop()

# 3. CONEXÃO GOOGLE SHEETS
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"

def carregar_dados():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", ttl=0)
        return df if df is not None else pd.DataFrame()
    except Exception as e:
        st.warning("Aguardando dados da planilha...")
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Pagamento', 'Beneficiário', 'Status', 'KM', 'Descrição'])

df_g = carregar_dados()

# 4. INTERFACE PRINCIPAL
st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["💰 Lançar", "📋 Extrato do Google"])

with tab1:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", date.today())
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita"], horizontal=True)
        
        c3, c4 = st.columns(2)
        benef = c3.text_input("Beneficiário/Loja:")
        valor = c4.number_input("Valor (R$):", 0.0)
        
        c5, c6 = st.columns(2)
        cat = c5.selectbox("Categoria:", ["Mercado", "Ração", "Combustível", "Lazer", "Outros"])
        status = c6.selectbox("Status:", ["⏳ Pendente", "✅ Pago"])
        
        desc = st.text_area("Descrição / Notas:")
        
        if st.button("🚀 GRAVAR NO GOOGLE SHEETS", use_container_width=True):
            novo_lancamento = pd.DataFrame([{
                "Data": dt_l.strftime('%d/%m/%Y'),
                "Tipo": tipo,
                "Categoria": cat,
                "Valor": valor,
                "Pagamento": "Pix", # Padrão para teste
                "Beneficiário": benef,
                "Status": status,
                "KM": 0,
                "Descrição": desc
            }])
            
            # Junta com o que já existe
            df_final = pd.concat([df_g, novo_lancamento], ignore_index=True)
            
            conn = st.connection("gsheets", type=GSheetsConnection)
            conn.update(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", data=df_final)
            st.success("✅ Gravado na Planilha com sucesso!")
            st.rerun()

with tab2:
    st.subheader("📊 Dados vindos da Planilha")
    if not df_g.empty:
        st.dataframe(df_g, use_container_width=True)
    else:
        st.info("A planilha está vazia ou ainda não conectou.")
