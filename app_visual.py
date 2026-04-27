import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container {
        background-color: #007bff; color: white; padding: 10px 20px;
        border-radius: 12px; text-align: center; margin-bottom: 10px;
    }
    .saldo-container h2 { margin: 0; font-size: 2.2rem; font-weight: bold; }
    [data-testid="stMetricValue"] { font-size: 1.4rem !important; }
    .stMetric { background-color: #ffffff; padding: 10px; border-radius: 10px; border: 1px solid #e0e0e0; }
    .resumo-box { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 5px solid #28a745; margin-top: 10px; }
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

# 3. CARREGAMENTO REFORÇADO
@st.cache_data(ttl=10)
def carregar_dados():
    try:
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_c.columns = [str(c).strip() for c in df_c.columns]
        if 'Meta' in df_c.columns:
            df_c['Meta'] = df_c['Meta'].astype(str).str.replace('R$', '').str.replace('.', '').str.replace(',', '.').str.strip()
            df_c['Meta'] = pd.to_numeric(df_c['Meta'], errors='coerce').fillna(0.0)
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        df_base = pd.DataFrame(dados[1:], columns=dados[0]) if len(dados) > 1 else pd.DataFrame()
        return df_b, df_c, df_base
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

# 4. INTERFACE
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        df_base.columns = [c.strip() for c in df_base.columns]
        c_dat, c_val, c_cat, c_tip, c_bnc, c_sta = df_base.columns[0], df_base.columns[1], df_base.columns[2], df_base.columns[3], df_base.columns[4], df_base.columns[5]

        def limpar_valor(v):
            v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
            return pd.to_numeric(v, errors='coerce') or 0.0

        df_base['V_Num'] = df_base[c_val].apply(limpar_valor)
        df_base['DT'] = pd.to_datetime(df_base[c_dat], dayfirst=True, errors='coerce')
        df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
        mes_atual = datetime.now().strftime('%m/%y')

        bancos_unicos = ["Todos"] + sorted(df_base[c_bnc].unique().tolist())
        banco_sel = st.selectbox("🔍 Pesquisar por Banco:", bancos_unicos)
        df_filtrado = df_base if banco_sel == "Todos" else df_base[df_base[c_bnc] == banco_sel]

        # Cálculos de Saldo
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if not df_bancos_cad.empty else 0
        df_realizado = df_base[df_base[c_sta] != 'Pendente']
        t_rec = df_realizado[df_realizado[c_tip] == 'Receita']['V_Num'].sum()
        t_des = df_realizado[df_realizado[c_tip] == 'Despesa']['V_Num'].sum()
        saldo_geral = s_ini + t_rec - t_des

        df_mes = df_filtrado[df_filtrado['Mes_Ano'] == mes_atual]
        m_receita = df_mes[df_mes[c_tip] == 'Receita']['V_Num'].sum()
        m_despesa = df_mes[df_mes[c_tip] == 'Despesa']['V_Num'].sum()
        m_pendente = df_mes[df_mes[c_sta] == 'Pendente']['V_Num'].sum()

        st.markdown(f'<div class="saldo-container"><small>Saldo Geral Realizado</small><h2>R$ {saldo_geral:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        m1, m2, m3 = st.columns(3)
        m1.metric("📈 Receitas", f"R$ {m_receita:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m2.metric("📉 Despesas", f"R$ {m_despesa:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        m3.metric("⏳ Pendência", f"R$ {m_pendente:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))

        # --- RESUMO ECONOMIA ---
        st.write("---")
        with st.container():
            col_rec, col_tabela = st.columns([1, 2])
            total_mes = m_receita
            sobra = total_mes - m_despesa
            perc_sobra = (sobra / total_mes * 100) if total_mes > 0 else 0
            
            with col_rec:
                st.markdown(f"""
                <div class="resumo-box">
                    <h4>💰 Economia do Mês</h4>
                    <p style='font-size: 1.2rem; margin-bottom: 0;'>Sobrou: <b>R$ {sobra:,.2f}</b></p>
                    <p style='color: #28a745;'>Corresponde a <b>{perc_sobra:.1f}%</b> do que entrou.</p>
                </div>
                """.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)
            
            with col_tabela:
                if not df_mes.empty:
                    df_res_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum().reset_index()
                    df_res_cat.columns = ['Categoria', 'Valor']
                    df_res_cat['%'] = (df_res_cat['Valor'] / m_despesa * 100) if m_despesa > 0 else 0
                    df_res_cat = df_res_cat.sort_values(by='Valor', ascending=False)
                    df_display = df_res_cat.copy()
                    df_display['Valor'] = df_display['Valor'].apply(lambda x: f"R$ {x:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
                    df_display['%'] = df_display['%'].apply(lambda x: f"{x:.1f}%")
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

        # --- SEÇÃO DE GRÁFICOS ---
        st.write("---")
        st.subheader("📈 Evolução Mensal")
        df_evol = df_filtrado.groupby(['Mes_Ano', c_tip])['V_Num'].sum().unstack().fillna(0).reset_index()
        if not df_evol.empty:
            fig_bar = go.Figure()
            if 'Receita' in df_evol.columns: fig_bar.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol['Receita'], name='Receita', marker_color='#28a745'))
            if 'Despesa' in df_evol.columns: fig_bar.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol['Despesa'], name='Despesa', marker_color='#dc3545'))
            fig_bar.update_layout(barmode='group', height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

        col_esq, col_dir = st.columns(2)
        with col_esq:
            st.subheader("🏦 Saldo por Banco")
            saldos_lista = []
            bancos_p = [banco_sel] if banco_sel != "Todos" else df_bancos_cad['Nome do Banco'].unique()
            for b in bancos_p:
                si = df_bancos_cad[df_bancos_cad['Nome do Banco'] == b]['Saldo Inicial'].apply(limpar_valor).sum()
                re = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & (df_base[c_tip] == 'Receita')]['V_Num'].sum()
                de = df_base[(df_base[c_bnc] == b) & (df_base[c_sta] != 'Pendente') & (df_base[c_tip] == 'Despesa')]['V_Num'].sum()
                saldos_lista.append({'Banco': b, 'Saldo': si + re - de})
            df_sb = pd.DataFrame(saldos_lista)
            if not df_sb.empty and df_sb['Saldo'].sum() != 0:
                fig_p = px.pie(df_sb, values='Saldo', names='Banco', hole=.4)
                fig_p.update_layout(height=300, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_p, use_container_width=True, key=f"pizza_{banco_sel}")

        with col_dir:
            st.subheader(f"📊 Metas vs Gasto ({mes_atual})")
            gasto_cat = df_mes[df_mes[c_tip] == 'Despesa'].groupby(c_cat)['V_Num'].sum()
            df_m = pd.DataFrame({'Meta': df_cats_cad.set_index('Nome')['Meta'], 'Real': gasto_cat}).fillna(0.0)
            df_m = df_m[(df_m['Meta'] > 0) | (df_m['Real'] > 0)]
            if not df_m.empty:
                fig_m = go.Figure()
                fig_m.add_trace(go.Bar(y=df_m.index, x=df_m['Meta'], name='Meta', orientation='h', marker_color='#D3D3D3'))
                fig_m.add_trace(go.Bar(y=df_m.index, x=df_m['Real'], name='Real', orientation='h', marker_color='#007bff'))
                fig_m.update_layout(barmode='group', height=300, legend=dict(orientation="h", y=1.2))
                st.plotly_chart(fig_m, use_container_width=True)

        st.write("---")
        st.subheader("📋 Lançamentos")
        st.dataframe(df_filtrado.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

    # --- FORMULÁRIO LATERAL ---
    with st.sidebar.form("f_novo"):
        st.write("### 🚀 Novo Lançamento")
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0)
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita"])
        f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
        f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]))
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        f_parc = st.number_input("Número de Parcelas", min_value=1, value=1)
        if st.form_submit_button("SALVAR"):
            ws = sh.get_worksheet(0)
            for i in range(f_parc):
                dt_p = f_dat + relativedelta(months=i)
                desc_p = f"{f_cat} ({i+1}/{f_parc})" if f_parc > 1 else f_cat
                ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_p, f_tip, f_bnc, f_sta])
            st.cache_data.clear(); st.rerun()

    # --- GERENCIAR (EDIÇÃO DE VALOR INCLUÍDA) ---
    st.sidebar.write("---")
    st.sidebar.write("### ⚙️ Gerenciar Lançamentos")
    if not df_base.empty:
        lista_edit = df_base.iloc[::-1].head(20) 
        opcoes = [f"{idx+2} | {row[c_dat]} | {row[c_cat]} | {row[c_val]}" for idx, row in lista_edit.iterrows()]
        item_sel = st.sidebar.selectbox("Selecione o item:", [""] + opcoes)
        if item_sel:
            linha_idx = int(item_sel.split(" | ")[0])
            valor_atual_str = item_sel.split(" | ")[3].replace('R$', '').strip()
            
            # Campo para novo valor
            novo_val = st.sidebar.number_input("Novo Valor:", value=limpar_valor(valor_atual_str))
            
            if st.sidebar.button("💾 Alterar Valor"):
                sh.get_worksheet(0).update_cell(linha_idx, 2, str(novo_val).replace('.', ','))
                st.cache_data.clear(); st.rerun()
                
            c1, c2 = st.sidebar.columns(2)
            if c1.button("🗑️ Excluir"):
                sh.get_worksheet(0).delete_rows(linha_idx)
                st.cache_data.clear(); st.rerun()
            if c2.button("✅ Quitar"):
                sh.get_worksheet(0).update_cell(linha_idx, 6, "Pago")
                st.cache_data.clear(); st.rerun()

elif aba == "🐾 Milo & Bolt":
    st.info("Aba em manutenção controlada.")
else:
    st.info("Aba em manutenção controlada.")
