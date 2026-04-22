import streamlit as st
import pandas as pd
from datetime import date
from streamlit_gsheets import GSheetsConnection

st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# --- CONEXÃO ---
URL_PLANILHA = "https://docs.google.com/spreadsheets/d/147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4/edit#gid=0"
conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    try:
        # Tenta ler a aba LANCAMENTOS
        df = conn.read(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", ttl=0)
        return df
    except:
        return pd.DataFrame(columns=['Data', 'Tipo', 'Categoria', 'Valor', 'Beneficiário'])

df_g = carregar_dados()

# --- INTERFACE ---
st.title("🐾 FinançasPro Wilson")

with st.form("meu_formulario", clear_on_submit=True):
    c1, c2 = st.columns(2)
    dt = c1.date_input("Data", date.today())
    tp = c2.selectbox("Tipo", ["🔴 Despesa", "🟢 Receita"])
    
    ben = st.text_input("Beneficiário")
    val = st.number_input("Valor", 0.0)
    
    enviar = st.form_submit_button("🚀 GRAVAR NO GOOGLE")

    if enviar:
        novo_dado = pd.DataFrame([{
            "Data": dt.strftime('%d/%m/%Y'),
            "Tipo": tp,
            "Beneficiário": ben,
            "Valor": val
        }])
        
        # Junta o novo com o antigo
        df_atualizado = pd.concat([df_g, novo_dado], ignore_index=True)
        
        # Tenta atualizar
        try:
            conn.update(spreadsheet=URL_PLANILHA, worksheet="LANCAMENTOS", data=df_atualizado)
            st.success("✅ Gravado! Atualize a página.")
        except Exception as e:
            st.error(f"Erro ao gravar: {e}")
            st.info("Dica: Verifique se a planilha está aberta e com acesso de EDIÇÃO para qualquer pessoa com o link.")

st.subheader("Visualização da Planilha")
st.dataframe(df_g)
