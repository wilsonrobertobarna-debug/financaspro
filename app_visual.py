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
    # Lógica de sinal: Receita/Rendimento é positivo, Despesa é negativo
    df['V_Real'] = df.apply(lambda r: r['V_Num'] if r['Tipo'] in ['Receita', 'Rendimento'] else -r['V_Num'], axis=1)
    return df.sort_values('DT')

df_base = carregar()
mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): 
    prefixo = "-" if n < 0 else ""
    return f"{prefixo}R$ {abs(n):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📊 Extrato Diário", "📄 Relatórios"])

# Form de lançamento omitido aqui para brevidade, mas mantido no seu app original

# 5. TELAS
if aba == "💰 Finanças":
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        patrimonio = df_base['V_Real'].sum()
        st.info(f"### 🏦 PATRIMÔNIO TOTAL: {m_fmt(patrimonio)}")
        
        # Grid de métricas e gráficos coloridos (Verde/Vermelho) conforme pedido anterior
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(-df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))

        g1, g2 = st.columns(2)
        with g1:
            df_fluxo = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            fig_bar = px.bar(df_fluxo, x='Tipo', y='V_Num', color='Tipo', 
                             color_discrete_map={'Receita':'#2ecc71', 'Despesa':'#e74c3c', 'Rendimento':'#27ae60'})
            st.plotly_chart(fig_bar, use_container_width=True)
        with g2:
            df_pie = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            st.plotly_chart(px.pie(df_pie, values='V_Num', names='Categoria'), use_container_width=True)

elif aba == "📊 Extrato Diário":
    st.title("📊 Extrato com Sinal de Negativo")
    b_sel = st.selectbox("Escolha o Banco:", sorted(df_base['Banco'].unique()))
    df_b = df_base[df_base['Banco'] == b_sel].copy().sort_values('DT')
    df_b['Saldo_Acum'] = df_b['V_Real'].cumsum()
    
    # Formatação com sinal negativo para despesas no extrato
    df_b['Valor Formatado'] = df_b.apply(lambda r: f"-R$ {r['V_Num']:.2f}".replace('.', ',') if r['Tipo'] == 'Despesa' else f"R$ {r['V_Num']:.2f}".replace('.', ','), axis=1)
    
    df_b['Saldo Diário'] = ""
    last_idx = df_b.groupby('DT').tail(1).index
    df_b.loc[last_idx, 'Saldo Diário'] = df_b.loc[last_idx, 'Saldo_Acum'].apply(m_fmt)
    st.table(df_b[['Data', 'Descrição', 'Tipo', 'Valor Formatado', 'Saldo Diário']].iloc[::-1])

elif aba == "📄 Relatórios":
    st.title("📄 Relatório Wilson")
    d1, d2 = st.columns(2)
    ini = d1.date_input("Início", datetime.now().replace(day=1))
    fim = d2.date_input("Fim", datetime.now())
    
    df_p = df_base[(df_base['DT'].dt.date >= ini) & (df_base['DT'].dt.date <= fim)]
    
    bancos_lista = sorted(df_base['Banco'].unique())
    saldos_txt = ""
    total_consolidado = 0
    for b in bancos_lista:
        s = df_base[df_base['Banco'] == b]['V_Real'].sum()
        saldos_txt += f"- {b}: {m_fmt(s)}\n"
        total_consolidado += s

    relat = f"RELATÓRIO WILSON\nPeríodo: {ini.strftime('%d/%m/%Y')} a {fim.strftime('%d/%m/%Y')}\n"
    relat += "========================================\n"
    relat += f"REC: {m_fmt(df_p[df_p['Tipo'] == 'Receita']['V_Num'].sum())}\n"
    relat += f"DES: {m_fmt(-df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum())}\n"
    relat += f"REND: {m_fmt(df_p[df_p['Tipo'] == 'Rendimento']['V_Num'].sum())}\n"
    relat += f"SOBRA: {m_fmt(df_p['V_Real'].sum())}\n"
    relat += "========================================\n\nSALDOS:\n"
    relat += saldos_txt
    relat += f"TOTAL BANCOS: {m_fmt(total_consolidado)}\n"
    relat += f"PATRIMÔNIO: {m_fmt(total_consolidado)}"
    
    st.text_area("Copiar Relatório:", relat, height=400)
    zap_url = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f'''<a href="{zap_url}" target="_blank"><button style="width:100%; height:50px; background-color:#25D366; color:white; border:none; border-radius:5px; font-weight:bold; cursor:pointer;">📲 ENVIAR PARA WHATSAPP</button></a>''', unsafe_allow_html=True)
