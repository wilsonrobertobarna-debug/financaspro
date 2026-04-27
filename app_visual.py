import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 15px;
        border-radius: 12px; text-align: center; margin-bottom: 15px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO
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

# 3. FUNÇÕES UTILITÁRIAS
@st.cache_data(ttl=60)
def carregar_aba(nome_aba):
    try:
        ws = sh.worksheet(nome_aba)
        dados = ws.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df.columns = [c.strip() for c in df.columns]
            return df
        return pd.DataFrame()
    except: return pd.DataFrame()

def limpar_moeda(v):
    if not v or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    return pd.to_numeric(v, errors='coerce') or 0.0

# 4. CARREGAMENTO INICIAL
df_bancos_cad = carregar_aba("Bancos")
df_cats_cad = carregar_aba("Categoria")

# 5. ABA PRINCIPAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Navegação:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    ws_fin = sh.get_worksheet(0)
    dados_fin = ws_fin.get_all_values()
    df_base = pd.DataFrame(dados_fin[1:], columns=dados_fin[0]) if len(dados_fin) > 1 else pd.DataFrame()
    
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # Padronização de colunas
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0:6]

        # Tratamento de dados
        df_base['V_Num'] = df_base[c_val].apply(limpar_moeda)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        # --- REATIVADO: PESQUISA POR BANCO ---
        st.write("### 🔍 Filtros e Resumo")
        banco_list = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("Filtrar por Banco:", banco_list)
        
        # Filtro dinâmico
        df_viva = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculos de Saldo (Apenas 'Pago')
        s_ini_total = df_bancos_cad['Saldo Inicial'].apply(limpar_moeda).sum() if not df_bancos_cad.empty else 0
        df_pago = df_base[df_base[c_sta] == 'Pago']
        t_rec = df_pago[df_pago[c_tip].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        t_des = df_pago[df_pago[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_geral = s_ini_total + t_rec - t_des

        # Métricas do Mês (Baseado no filtro de banco selecionado)
        df_mes = df_viva[df_viva['Mes_Ano'] == mes_atual]
        m_rec = df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum()
        m_des = df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum()
        m_ren = df_mes[df_mes[c_tip] == 'Rendimento']['V_Num'].sum()
        m_pen = df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum()

        economia = (m_rec + m_ren) - m_des
        perc_econ = (economia / (m_rec + m_ren) * 100) if (m_rec + m_ren) > 0 else 0

        # EXIBIÇÃO DASHBOARD
        st.markdown(f'<div class="saldo-container"><small>Saldo Realizado (Geral)</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", f"R$ {m_rec:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_des:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("💰 Rendimento", f"R$ {m_ren:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m4.metric("⏳ Pendente", f"R$ {m_pen:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        
        st.write(f"**Economia no mês ({banco_sel}):** R$ {economia:,.2f} ({perc_econ:.1f}%)")
        st.write("---")

        # --- SEÇÃO DE GRÁFICOS (CORRIGIDA) ---
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            st.subheader("🏦 Saldo Real por Banco")
            try:
                s_bancos = []
                for b in df_bancos_cad['Nome do Banco'].unique():
                    si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar_moeda).sum()
                    re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip].isin(['Receita', 'Rendimento']))]['V_Num'].sum()
                    de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] == 'Pago') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                    s_bancos.append({'Banco': b, 'Saldo': si + re - de})
                
                df_sb = pd.DataFrame(s_bancos)
                df_sb = df_sb[df_sb['Saldo'] != 0] # Mostra positivos e negativos, só remove o zero absoluto
                
                if not df_sb.empty:
                    fig_p = px.pie(df_sb, values='Saldo', names='Banco', hole=.5, color_discrete_sequence=px.colors.qualitative.Pastel)
                    fig_p.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20), legend=dict(orientation="h", y=-0.1))
                    st.plotly_chart(fig_p, use_container_width=True)
                else:
                    st.info("Sem saldos para exibir.")
            except Exception as e:
                st.error(f"Erro no gráfico de bancos: {e}")

        with col_g2:
            st.subheader("📊 Receita x Despesa (Mensal)")
            try:
                # Agrupando por mês e tipo para o gráfico de evolução
                df_evol = df_viva.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0)
                if not df_evol.empty:
                    # Garantir que as colunas existam para não quebrar
                    colunas_evol = [c for c in ['Receita', 'Despesa', 'Rendimento'] if c in df_evol.columns]
                    st.bar_chart(df_evol[colunas_evol])
                else:
                    st.info("Dados insuficientes para evolução mensal.")
            except Exception as e:
                st.error(f"Erro no gráfico de evolução: {e}")

        st.write("---")
        # Gráfico de Metas (Abaixo dos principais)
        st.subheader(f"🎯 Controle de Metas ({mes_atual})")
        if not df_cats_cad.empty:
            df_cats_cad['Meta_N'] = df_cats_cad['Meta'].apply(limpar_moeda)
            g_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
            df_metas = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta_N'], 'Realizado': g_cat}).fillna(0)
            df_metas = df_metas[(df_metas['Meta'] > 0) | (df_metas['Realizado'] > 0)]
            
            if not df_metas.empty:
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(y=df_metas.index, x=df_metas['Meta'], name='Meta', orientation='h', marker_color='#E0E0E0'))
                fig_m.add_trace(go.Bar(y=df_metas.index, x=df_metas['Realizado'], name='Gasto', orientation='h', marker_color='#007bff'))
                fig_m.update_layout(barmode='group', height=400, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig_m, use_container_width=True)

        st.write("---")
        st.subheader("📋 Histórico de Lançamentos")
        st.dataframe(df_viva.drop(columns=['DT', 'V_Num', 'Mes_Ano'], errors='ignore').iloc[::-1], use_container_width=True)

    # BARRA LATERAL (CADASTRO E AÇÕES)
    with st.sidebar.form("f_novo"):
        st.write("### 🚀 Novo Registro")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Geral"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        f_parc = st.number_input("Nº Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            for i in range(f_parc):
                dt_p = f_dat + relativedelta(months=i)
                desc = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                ws_fin.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

    st.sidebar.write("---")
    st.sidebar.write("### ⚙️ Gerenciar")
    if not df_base.empty:
        lista = df_base.iloc[::-1].head(15)
        sel = st.sidebar.selectbox("Selecionar Item:", [""] + [f"{idx+2} | {r[c_dat]} | {r[c_cat]}" for idx, r in lista.iterrows()])
        if sel:
            idx_real = int(sel.split(" | ")[0])
            if st.sidebar.button("✅ Confirmar Pagamento"):
                ws_fin.update_cell(idx_real, 6, "Pago")
                st.cache_data.clear(); st.rerun()
            if st.sidebar.checkbox("🔓 Liberar Botão Excluir") and st.sidebar.button("🗑️ EXCLUIR DEFINITIVAMENTE"):
                ws_fin.delete_rows(idx_real)
                st.cache_data.clear(); st.rerun()
