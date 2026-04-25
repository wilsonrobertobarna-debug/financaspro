import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import date

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="💰")

# --- ÁREA DA CHAVE (SUBSTITUA PELO SEU CONTEÚDO REAL) ---
# Dica: Cole sua chave exatamente como está no arquivo .json
PK_LIST = [
    "-----BEGIN PRIVATE KEY-----",
    "SUA_CHAVE_AQUI_LINHA_1",
    "SUA_CHAVE_AQUI_LINHA_2",
    "SUA_CHAVE_AQUI_LINHA_X",
    "-----END PRIVATE KEY-----"
]

@st.cache_resource
def conectar_google():
    # O .strip() limpa espaços invisíveis e o .replace garante a leitura das quebras de linha
    private_key = "\n".join([l.strip() for l in PK_LIST]).replace("\\n", "\n")
    
    creds_info = {
        "type": "service_account",
        "project_id": "financaspro-wilson",
        "client_email": "financas-wilson@financaspro-wilson.iam.gserviceaccount.com",
        "token_uri": "https://oauth2.googleapis.com/token",
        "private_key": private_key
    }
    
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    return gspread.authorize(Credentials.from_service_account_info(creds_info, scopes=scope))

def salvar_registro():
    # Só salva se houver um valor maior que zero
    if st.session_state.v_valor > 0:
        # Captura os textos antes de limpar os campos da tela
        v_desc_fixa = st.session_state.v_desc
        v_benef_fixo = st.session_state.v_benef
        
        # Ordem das 11 colunas (A até K) para bater com sua planilha arrumada
        # A:Data | B:Valor | C:Cat | D:Banco | E:Desc | F:Benef | G:Conta | H:Obs | I:Obs | J:Status | K:Tipo
        nova_linha = [
            st.session_state.v_data.strftime('%d/%m/%Y'), # A
            st.session_state.v_valor,                      # B
            st.session_state.v_cat,                        # C
            st.session_state.v_banco,                      # D
            v_desc_fixa,                                   # E
            v_benef_fixo,                                  # F
            "Pessoal",                                      # G (Sempre fixo)
            "",                                             # H (Vazio)
            "",                                             # I (Vazio)
            st.session_state.v_status,                     # J (STATUS: Pago/Pendente)
            st.session_state.v_tipo                        # K (TIPO: Receita/Despesa)
        ]
        
        ws.append_row(nova_linha)
        
        # Limpa os campos após o sucesso
        st.session_state.v_valor = 0.0
        st.session_state.v_desc = ""
        st.session_state.v_benef = ""
        st.toast("✅ Lançamento gravado com sucesso!")

# --- EXECUÇÃO DO APP ---
try:
    client = conectar_google()
    sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")
    ws = sh.get_worksheet(0)
    
    st.title("🛡️ FinançasPro Wilson")

    # Layout em duas colunas (Formulário à esquerda, Tabela à direita)
    col_f, col_t = st.columns([1, 2.5])

    with col_f:
        st.subheader("📝 Novo Lançamento")
        st.radio("Tipo", ["Despesa", "Receita"], key="v_tipo", horizontal=True)
        st.date_input("Data", date.today(), key="v_data", format="DD/MM/YYYY")
        st.number_input("Valor (R$)", min_value=0.0, step=0.01, key="v_valor")
        st.text_input("Descrição", key="v_desc")
        st.text_input("Beneficiário", key="v_benef")
        st.selectbox("Categoria", ["Pets", "Aluguel", "Mercado", "Rendimento", "Trabalho", "Outros"], key="v_cat")
        st.selectbox("Banco", ["Nubank", "Itaú", "Inter", "Bradesco", "Dinheiro"], key="v_banco")
        st.selectbox("Status", ["Pago", "Pendente"], key="v_status")
        st.button("🚀 Gravar na Planilha", use_container_width=True, on_click=salvar_registro)

    with col_t:
        st.subheader("📋 Histórico da Planilha")
        dados_planilha = ws.get_all_records()
        if dados_planilha:
            df = pd.DataFrame(dados_planilha)
            # Mostra as últimas 15 linhas para conferência
            st.dataframe(df.tail(15), use_container_width=True, hide_index=True)
        else:
            st.info("Sua planilha parece estar vazia ou os cabeçalhos não foram detectados.")

except Exception as e:
    # Se der erro de chave, ele aparecerá aqui de forma clara
    st.error(f"Erro de Conexão: {e}")
    st.warning("Verifique se a PK_LIST contém todas as linhas da sua chave privada do Google.")
