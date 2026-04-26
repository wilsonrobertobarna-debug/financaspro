import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go # Biblioteca para o gráfico lado a lado
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO E ESTILO (PADRÃO WILSON)
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 25px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
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

# 3. CARREGAMENTO E TRATAMENTO DE DADOS
@st.cache_data(ttl=60)
def carregar_tudo():
    try:
        # Categorias e Metas
        ws_cat = sh.worksheet("Categoria")
        df_c = pd.DataFrame(ws_cat.get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
        else: df_c['Meta'] = 0.0
        df_c['Nome'] = df_c['Nome'].astype(str).str.strip()

        # Lançamentos
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        
        # Bancos e Cartões
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_ct = pd.DataFrame(sh.worksheet("Cartoes").get_all_records())
        
        return df_b, df_c, df_ct, df_base
    except Exception as e:
        st.error(f"Erro: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_cartoes_cad, df_base = carregar_tudo()

# 4. INTERFACE PRINCIPAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3]
        c_bnc, c_sta = df_base.columns[4], df_base.columns[5]

        df_base['Valor_Num'] = df_base[c_val].astype(str).str.replace('.', '').str.replace(',', '.').str.strip()
        df_base['Valor_Num'] = pd.to_numeric(df_base['Valor_Num'], errors='coerce').fillna(0.0)
        df_base['Data_DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base = df_base.dropna(subset=['Data_DT'])
        df_base['Mes_Ano'] = df_base['Data_DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # Saldo Consolidado
        s_ini = pd.to_numeric(df_bancos_cad['Saldo Inicial'].astype(str).str.replace(',', '.'), errors='coerce').sum() if not df_bancos_cad.empty else 0
        rec_t = df_base[df_base[c_tip] == 'Receita']['Valor_Num'].sum()
        desp_t = df_base[df_base[c_tip] == 'Despesa']['Valor_Num'].sum()
        saldo_geral = s_ini + rec_t - desp_t
        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Consolidado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        st.write("---")
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader(f"📊 Metas vs Gasto ({mes_atual})")
            df_mes = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base[c_tip] == 'Despesa')].copy()
            gasto_por_cat = df_mes.groupby(c_cat)['Valor_Num'].sum()
            
            df_plot = pd.DataFrame({
                'Meta': df_cats_cad.set_index('Nome')['Meta'],
                'Real': gasto_por_cat
            }).fillna(0.0)
            df_plot = df_plot[(df_plot['Meta'] > 0) | (df_plot['Real'] > 0)]

            if not df_plot.empty:
                # GRÁFICO PLOTLY (FORÇA LADO A LADO)
                fig = go.Figure()
                fig.add_trace(go.Bar(y=df_plot.index, x=df_plot['Meta'], name='Meta Planejada', orientation='h', marker_color='#A0A0A0'))
                fig.add_trace(go.Bar(y=df_plot.index, x=df_plot['Real'], name='Gasto Real', orientation='h', marker_color='#007bff'))
                
                fig.update_layout(
                    barmode='group', # ESTE COMANDO COLOCA LADO A LADO
                    height=400,
                    margin=dict(l=20, r=20, t=20, b=20),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("⚠️ Verifique a coluna 'Meta' na aba 'Categoria'.")

        with col2:
            st.subheader("📈 Receita x Despesa Mensal")
            df_evol = df_base.groupby(['Mes_Ano', c_tip])['Valor_Num'].sum().unstack().fillna(0.0)
            if not df_evol.empty:
                st.bar_chart(df_evol)

        st.write("---")
        st.subheader("📋 Lançamentos Recentes")
        st.dataframe(df_base.drop(columns=['Data_DT', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # FORMULÁRIO LATERAL (MANTIDO)
    with st.sidebar.form("novo_lanc"):
        st.write("### 🚀 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now())
        f_val = st.number_input("Valor", min_value=0.0)
        f_parc = st.number_input("Parcelas", min_value=1, value=1)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        cats = sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"]
        f_cat = st.selectbox("Categoria", cats)
        f_bnc = st.selectbox("Banco/Cartão", ["Dinheiro"] + sorted(df_bancos_cad['Nome do Banco'].tolist() if not df_bancos_cad.empty else []))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        if st.form_submit_button("SALVAR"):
            ws = sh.get_worksheet(0)
            linhas = []
            for i in range(f_parc):
                dt = f_dat + relativedelta(months=i)
                nome_cat = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                linhas.append([dt.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), nome_cat, f_tip, f_bnc, f_sta])
            ws.append_rows(linhas)
            st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.title("🐾 Controle: Milo & Bolt")
    ws_p = sh.worksheet("Controle_Pets"); dados_p = ws_p.get_all_values()
    df_p = pd.DataFrame(dados_p[1:], columns=dados_p[0]) if len(dados_p) > 1 else pd.DataFrame()
    st.dataframe(df_p.iloc[::-1], use_container_width=True)

else:
    st.title("🚗 Meu Veículo")
    ws_v = sh.worksheet("Controle_Veiculo"); dados_v = ws_v.get_all_values()
    df_v = pd.DataFrame(dados_v[1:], columns=dados_v[0]) if len(dados_v) > 1 else pd.DataFrame()
    st.dataframe(df_v.iloc[::-1], use_container_width=True)
