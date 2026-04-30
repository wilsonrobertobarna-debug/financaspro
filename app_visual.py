import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF 

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES MAIS COMPACTOS E ALINHAMENTO À DIREITA DAS TABELAS
st.markdown(
    """
    <style>
    [data-testid='stMetricValue'] {font-size: 0.95rem !important;}
    [data-testid="stDataFrame"] td, [data-testid="stDataFrame"] th {
        text-align: right !important;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# 0. VERSÃO NO TOPO
st.caption("Version 2.0.10")

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
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# IDENTIFICAÇÃO DAS ABAS
ws_base = sh.get_worksheet(0)
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# FUNÇÕES DE CARREGAMENTO DIRETO
def carregar_dados_gs():
    dados = ws_base.get_all_values()
    if len(dados) <= 1: return pd.DataFrame()
    df = pd.DataFrame(dados[1:], columns=dados[0])
    
    # Limpa linhas em branco que estão na planilha para não gerar registros nulos
    df = df[df.iloc[:, 0].astype(str).str.strip() != ''].copy()
    if df.empty: return pd.DataFrame()
    
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_manual_gs():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 1:
            df_b = pd.DataFrame(dados[1:], columns=dados[0])
            df_b = df_b[df_b.iloc[:, 0].astype(str).str.strip() != ''].copy()
            return df_b
    return pd.DataFrame()

# INICIALIZA O CACHE NA SESSÃO
if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados_gs()
if 'df_bancos_info' not in st.session_state:
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

# FUNÇÃO PARA ATUALIZAR O ESTADO
def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

# CARREGA OS BANCOS DINAMICAMENTE DA PLANILHA OU USA OS PADRÕES
if not df_bancos_info.empty:
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"]

mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# 4. SIDEBAR - NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")

# Botão de atualização manual
if st.sidebar.button("🔄 Atualizar dados do Sheets"):
    atualizar_sessao()
    st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF"])

st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet", "Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta])
            atualizar_sessao()
            st.rerun()

# BARRINHA 2: TRANSFERÊNCIA
with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        t_orig = st.selectbox("Origem (Sai):", bancos_disponiveis)
        t_dest = st.selectbox("Destino (Entra):", bancos_disponiveis)
        t_desc = st.text_input("Nota")
        if st.form_submit_button("TRANSFERIR"):
            if t_orig == t_dest: st.error("Escolha bancos diferentes!")
            else:
                v_str = f"{t_val:.2f}".replace('.', ',')
                d_str = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago"])
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago"])
                atualizar_sessao()
                st.rerun()

# BARRINHA 3: AJUSTE / EXCLUSÃO
with st.sidebar.expander("⚙️ Ajustar Lançamento", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} ! {r['Data']} ! {r['Descrição']} ! R$ {r['Valor']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione para Alterar/Excluir:", [""] + list(lista_edit.keys()))
        if escolha:
            item = lista_edit[escolha]
            data_atual_dt = datetime.strptime(item['Data'], "%d/%m/%Y")
            ed_dat = st.date_input("Alterar Data:", value=data_atual_dt, format="DD/MM/YYYY")
            
            ed_val = st.number_input("Alterar Valor:", value=float(item['V_Num']), step=0.01, format="%.2f")
            ed_desc = st.text_input("Alterar Descrição:", value=item['Descrição'])
            
            idx_b = bancos_disponiveis.index(item['Banco']) if item['Banco'] in bancos_disponiveis else 0
            ed_bnc = st.selectbox("Alterar Banco:", bancos_disponiveis, index=idx_b)
            
            status_opcoes = ["Pago", "Pendente"]
            index_status = status_opcoes.index(item['Status']) if item['Status'] in status_opcoes else 0
            ed_sta = st.selectbox("Status:", status_opcoes, index=index_status)
            
            col_ed1, col_ed2 = st.columns(2)
            if col_ed1.button("💾 ATUALIZAR"):
                v_str = f"{ed_val:.2f}".replace('.', ',')
                ws_base.update_cell(int(item['ID']), 1, ed_dat.strftime("%d/%m/%Y"))
                ws_base.update_cell(int(item['ID']), 2, v_str)
                ws_base.update_cell(int(item['ID']), 3, ed_desc)
                ws_base.update_cell(int(item['ID']), 6, ed_bnc)
                ws_base.update_cell(int(item['ID']), 7, ed_sta)
                atualizar_sessao()
                st.rerun()
            if col_ed2.button("🚨 EXCLUIR"):
                ws_base.delete_rows(int(item['ID']))
                atualizar_sessao()
                st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        saldo_geral = df_base[df_base['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_base[df_base['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        
        st.subheader("💡 Resumo de Economia")
        
        mes_anterior = (datetime.now() - relativedelta(months=1)).strftime('%m/%y')
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[df_m['Categoria'] != 'Transferência']
        
        r_v = df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        rend_v = df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()
        sobra_atual = (r_v + rend_v) - d_v
        
        df_ant = df_base[df_base['Mes_Ano'] == mes_anterior].copy()
        if not df_ant.empty:
            df_ant_limpo = df_ant[df_ant['Categoria'] != 'Transferência']
            r_ant = df_ant_limpo[df_ant_limpo['Tipo'] == 'Receita']['V_Num'].sum()
            d_ant = df_ant_limpo[df_ant_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
            rend_ant = df_ant_limpo[df_ant_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()
            sobra_anterior = (r_ant + rend_ant) - d_ant
        else:
            sobra_anterior = 0.0
            
        dif_eco = sobra_atual - sobra_anterior
        
        col_eco1, col_eco2 = st.columns(2)
        col_eco1.metric("💰 Sobra deste Mês", m_fmt(sobra_atual))
        col_eco2.metric("📉 Comparação com Mês Anterior", m_fmt(dif_eco), delta=m_fmt(dif_eco), help="Sobra do mês atual comparada com a sobra do mês passado")
        
        st.divider()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        
        st.subheader("🏦 Informações de Contas e Cartões")
        if not df_bancos_info.empty:
            st.dataframe(df_bancos_info, use_container_width=True, hide_index=True)
        else:
            st.info("ℹ️ Preencha a aba 'Bancos' no Google Sheets para visualizar os dados.")
        
        st.divider()
        
        with st.expander("🎯 Configurar Metas"):
            todas_cats = sorted(df_base['Categoria'].unique())
            metas_map = {}
            cols = st.columns(3)
            for i, cat in enumerate(todas_cats):
                if cat != "Transferência":
                    default_v = 1200.0 if cat == "Mercado" else 400.0
                    metas_map[cat] = cols[i % 3].number_input(f"Meta: {cat}", value=default_v, key=f"m_{cat}")
        
        g1, g2 = st.columns(2)
        with g1:
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty: st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="✨ Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_m_limpo.groupby('Tipo')['V_Num'].sum().reset_index()
            if not df_f.empty: st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="📊 Fluxo de Caixa"), use_container_width=True)
        
        st.divider()
        st.subheader("📈 Evolução do Saldo Acumulado")
        
        df_saldo_dia = df_base.dropna(subset=['DT']).sort_values('DT').copy()
        if not df_saldo_dia.empty:
            df_saldo_dia['Valor_Com_Sinal'] = df_saldo_dia.apply(
                lambda x: x['V_Num'] if x['Tipo'] in ['Receita', 'Rendimento'] else -x['V_Num'], axis=1
            )
            df_grouped = df_saldo_dia.groupby('DT', as_index=False)['Valor_Com_Sinal'].sum()
            
            full_date_range = pd.date_range(start=df_grouped['DT'].min(), end=df_grouped['DT'].max(), freq='D')
            df_full = pd.DataFrame({'DT': full_date_range})
            
            df_full = df_full.merge(df_grouped, on='DT', how='left').fillna({'Valor_Com_Sinal': 0.0})
            df_full = df_full.sort_values('DT')
            
            df_full['Saldo_Acumulado'] = df_full['Valor_Com_Sinal'].cumsum()
            
            fig_acum = px.line(df_full, x='DT', y='Saldo_Acumulado', title="Progresso do Patrimônio Acumulado no Tempo", markers=True)
            fig_acum.update_layout(height=350, xaxis_title="Data", yaxis_title="Saldo Acumulado (R$)")
            st.plotly_chart(fig_acum, use_container_width=True)
            
        st.divider()
        st.subheader("🎯 Metas vs Realizado")
        df_metas_graph = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_metas_graph.empty:
            df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map).fillna(0.0)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Real', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
            fig_m.update_layout(barmode='group', height=350); st.plotly_chart(fig_m, use_container_width=True)
        
        st.divider()
        st.subheader("🔍 Busca e Lançamentos")
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Filtrar Banco:", sorted(bancos_disponiveis))
        s_sta = c2.multiselect("Filtrar Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Buscar Beneficiário:")
        
        df_v = df_base.copy()
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
        df_v_view = df_v[['ID', 'Data', 'Tipo', 'V_Num', 'Descrição', 'Categoria',
