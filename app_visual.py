import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import urllib.parse

# RESOLUÇÃO DO FUSO HORÁRIO (Sem precisar de biblioteca extra)
# O servidor do Streamlit é 3 horas adiantado. Tiramos 3 horas para ser Brasília.
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()
agora = datetime.now() - timedelta(hours=3)
hoje = agora.date()
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.3")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES E RÓTULOS DOS METRICS
st.markdown("""
    <style>
    [data-testid='stMetricLabel'] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    [data-testid='stMetricValue'] {
        font-size: 1.1rem !important;
        font-weight: bold !important;
    }
    </style>
""", unsafe_allow_html=True)

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
    df['ID'] = range(2, len(df) + 2)
    def p_float(v):
        try: return float(str(v).replace('R$', '').replace('.', '').replace(',', '.').strip())
        except: return 0.0
    df['V_Num'] = df['Valor'].apply(p_float)
    df['DT'] = pd.to_datetime(df['Vencimento'], dayfirst=True, errors='coerce')   
    df['Mes_Ano'] = df['DT'].dt.strftime('%m/%y')
    return df

def carregar_bancos_manual_gs():
    if ws_bancos:
        dados = ws_bancos.get_all_values()
        if len(dados) > 1:
            return pd.DataFrame(dados[1:], columns=dados[0])
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

# INTEGRAÇÃO DE AVISOS NO WHATSAPP VIA TWILIO
def enviar_whatsapp_pendencias(df):
    now = datetime.now()
    if now.hour >= 8:
        if 'last_wa_date' not in st.session_state or st.session_state['last_wa_date'] != now.date():
            twilio_secrets = st.secrets.get("twilio", {})
            sid = twilio_secrets.get("account_sid")
            token = twilio_secrets.get("auth_token")
            w_from = twilio_secrets.get("whatsapp_from")
            w_to = twilio_secrets.get("whatsapp_to")
            
            if sid and token and w_from and w_to:
                try:
                    from twilio.rest import Client
                    client_tw = Client(sid, token)
                    df_aviso = df[df['Status'] == 'Pendente'].copy()
                    if not df_aviso.empty:
                        df_aviso['Dias'] = (df_aviso['DT'] - pd.to_datetime(now)).dt.days
                        df_venc = df_aviso[df_aviso['Dias'].isin([0, 1, 3]) | (df_aviso['Dias'] < 0)].copy()
                        if not df_venc.empty:
                            mensagem = "🔔 *Aviso de Pendências - FinançasPro*\n\n"
                            for _, row in df_venc.iterrows():
                                if row['Dias'] < 0:
                                    mensagem += f"⚠️ Lançamento Atrasado: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 0:
                                    mensagem += f"⚠️ Vence Hoje: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 1:
                                    mensagem += f"🚨 Vence Amanhã: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                                elif row['Dias'] == 3:
                                    mensagem += f"⚠️ Vence em 3 dias: {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})\n"
                            
                            client_tw.messages.create(body=mensagem, from_=w_from, to=w_to)
                            st.session_state['last_wa_date'] = now.date()
                except Exception as e:
                    pass

enviar_whatsapp_pendencias(df_base)

# CARREGA OS BANCOS DINAMICAMENTE DA PLANILHA OU USA OS PADRÕES
if not df_bancos_info.empty:
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago", "PicPay", "PagBank", "CEF"]

mes_atual = datetime.now().strftime('%m/%y')

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

# FUNÇÃO PARA OBTER O VALOR PENDENTE ATUAL
def get_valor_pendente(df):
    now = datetime.now()
    end_of_month = datetime(now.year, now.month, 1) + relativedelta(months=1, days=-1)
    df_p = df[(df['Status'] == 'Pendente') & (df['DT'].dt.date <= end_of_month.date())]
    return df_p['V_Num'].sum()

# 4. SIDEBAR - NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")

if st.sidebar.button("🔄 Atualizar dados do Sheets"):
    atualizar_sessao()
    st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF"])

st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_compra = st.date_input("🛍️ Data da Compra", value=datetime.now(), format="DD/MM/YYYY")
        f_dat = st.date_input("Vencimento", datetime.now(), format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água","Assinatura","Seguro", "Internet","Vestuário","Salário","Reembolso","Moradia", "Saúde","Taxas","Depósito","Plano Assistencial","Transporte","Previdência","Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
            
        
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            venc_str = f_venc_cartao.strftime("%d/%m/%Y") if f_venc_cartao is not None else ""
            
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta, venc_str])
            
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
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago", ""])
                ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago", ""])
                atualizar_sessao()
                st.rerun()

# BARRINHA 3: AJUSTE / EXCLUSÃO
with st.sidebar.expander("⚙️ Ajustar Lançamento", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} ! {r['Vencimento']} ! {r['Descrição']} ! R$ {r['Valor']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione para Alterar/Excluir:", [""] + list(lista_edit.keys()))
        if escolha:
            item = lista_edit[escolha]
            data_atual_dt = datetime.strptime(item['Vencimento'], "%d/%m/%Y")
            ed_dat = st.date_input("Alterar Vencimento:", value=data_atual_dt, format="DD/MM/YYYY")
            
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
                if item['Categoria'] == 'Transferência':
                    desc = item['Descrição']
                    data = item['Data']
                    v_num = item['V_Num']
                    ids_para_excluir = []
                    for idx, row in df_base.iterrows():
                        if (row['Data'] == data and 
                            abs(row['V_Num'] - v_num) < 0.01 and 
                            row['Descrição'] == desc and 
                            row['Categoria'] == 'Transferência'):
                            ids_para_excluir.append(int(row['ID']))
                    ids_para_excluir = sorted(list(set(ids_para_excluir)), reverse=True)
                    for id_linha in ids_para_excluir:
                        ws_base.delete_rows(id_linha)
                else:
                    ws_base.delete_rows(int(item['ID']))
                atualizar_sessao()
                st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
        
        saldo_geral = df_m_limpo[df_m_limpo['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        
        st.divider()
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(get_valor_pendente(df_base)))
        
        st.divider()
        
        # --- 1. COMPARATIVO DE SOBRA DINÂMICO ---
# 'expanded=False' garante que a barra venha fechada como você quer
with st.expander(f"📊 Comparativo de Sobra: {s_ini.strftime('%d/%m')} até {s_fim.strftime('%d/%m')}", expanded=False):
    
    # Filtramos os dados com base nas datas 's_ini' e 's_fim' que você já tem no código
    df_periodo = df_base[(df_base['DT'].dt.date >= s_ini) & (df_base['DT'].dt.date <= s_fim) & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')]
    
    # Cálculos dinâmicos baseados na sua seleção
    receitas_periodo = df_periodo[df_periodo['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
    despesas_periodo = df_periodo[df_periodo['Tipo'] == 'Despesa']['V_Num'].sum()
    sobra_atual = receitas_periodo - despesas_periodo
    
    # Exibição das métricas
    c1, c2 = st.columns(2)
    c1.metric("Receitas no Período", m_fmt(receitas_periodo))
    c2.metric("Despesas no Período", m_fmt(despesas_periodo))
    
    st.divider()
    st.metric("Sobra Líquida Atual", m_fmt(sobra_atual))        
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
            if not df_p.empty: 
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="✨ Gastos por Categoria (%)", hole=0.4), use_container_width=True, config={'staticPlot': True})
        with g2:
            df_f = df_base[(df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')].copy()
            df_f = df_f.sort_values('DT')
            df_f_grouped = df_f.groupby(['Mes_Ano', 'Tipo'], sort=False)['V_Num'].sum().reset_index()
            if not df_f_grouped.empty: 
                st.plotly_chart(px.bar(df_f_grouped, x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="📊 Fluxo de Caixa Mensal"), use_container_width=True, config={'staticPlot': True})
        
        st.divider()
        st.subheader("📈 Evolução do Saldo Acumulado")
        df_saldo_dia = df_base[df_base['Status'] == 'Pago'].sort_values('DT').copy()
        if not df_saldo_dia.empty:
            df_saldo_dia['Valor_Com_Sinal'] = df_saldo_dia.apply(
                lambda x: x['V_Num'] if x['Tipo'] in ['Receita', 'Rendimento'] else -x['V_Num'], axis=1
            )
            df_saldo_dia = df_saldo_dia.groupby('Vencimento')['Valor_Com_Sinal'].sum().reset_index()
            df_saldo_dia['Saldo_Acumulado'] = df_saldo_dia['Valor_Com_Sinal'].cumsum()
            
            fig_acum = px.line(df_saldo_dia, x='Vencimento', y='Saldo_Acumulado', title="Progresso do Patrimônio Acumulado no Tempo", markers=True)
            fig_acum.update_layout(height=350)
            st.plotly_chart(fig_acum, use_container_width=True, config={'staticPlot': True})
        
        st.divider()
        st.subheader("🎯 Metas vs Realizado")
        df_metas_graph = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_metas_graph.empty:
            df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map).fillna(0.0)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Real', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
            fig_m.update_layout(barmode='group', height=350); st.plotly_chart(fig_m, use_container_width=True, config={'staticPlot': True})
        
        st.divider()
        st.subheader("🔍 Busca e Lançamentos")
        
        c_d1, c_d2 = st.columns(2)
        s_ini = c_d1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
        s_fim = c_d2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
        
        c1, c2, c3 = st.columns(3)
        s_bnc = c1.multiselect("Filtrar Banco:", sorted(bancos_disponiveis))
        s_sta = c2.multiselect("Filtrar Status:", ["Pago", "Pendente"])
        b_desc = c3.text_input("Buscar Beneficiário:")
        
        df_v = df_base.copy()
        df_v = df_v[df_v['DT'].notna()]
        df_v = df_v[(df_v['DT'].dt.date >= s_ini) & (df_v['DT'].dt.date <= s_fim)]
        if s_bnc: df_v = df_v[df_v['Banco'].isin(s_bnc)]
        if s_sta: df_v = df_v[df_v['Status'].isin(s_sta)]
        if b_desc: df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
        df_v_display = df_v[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].copy()
        df_v_display['Valor'] = df_v['V_Num'].apply(m_fmt)
        st.dataframe(df_v_display.iloc[::-1], use_container_width=True, hide_index=True)

elif "Pendências" in aba:
    st.title("📋 Lançamentos Pendentes")
    st.subheader("🔔 Avisos: Vencimentos de Lançamentos")
    df_aviso = df_base[df_base['Status'] == 'Pendente'].copy()
    if not df_aviso.empty:
        df_aviso['Dias'] = (df_aviso['DT'] - pd.to_datetime(datetime.now())).dt.days
        df_venc = df_aviso[df_aviso['Dias'].isin([0, 1, 3]) | (df_aviso['Dias'] < 0)]
        if not df_venc.empty:
            for _, row in df_venc.iterrows():
                d_aviso = row['Dias']
                if d_aviso < 0:
                    st.warning(f"⚠️ **Atrasado (Vencido):** {row['Vencimento']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})")
                elif d_aviso == 0:
                    st.warning(f"⚠️ **Vence hoje:** {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})")
                elif d_aviso == 1:
                    st.warning(f"🚨 **Vence amanhã:** {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})")
                elif d_aviso == 3:
                    st.warning(f"⚠️ **Vence em 3 dias:** {row['Data']} - {row['Descrição']} no valor de {m_fmt(row['V_Num'])} ({row['Banco']})")
        else:
            st.info("Nenhum lançamento a vencer hoje, amanhã ou em atraso.")
    else:
        st.info("Nenhum lançamento pendente.")
        
    st.divider()
    
    st.subheader("🔍 Busca de Lançamentos Pendentes")
    
    c1, c2 = st.columns(2)
    s_bnc = c1.multiselect("Filtrar Banco/Cartão:", sorted(bancos_disponiveis))
    b_desc = c2.text_input("Buscar Descrição:")
    
    df_v = df_base[df_base['Status'] == 'Pendente'].copy()
    df_v = df_v[df_v['DT'].notna()]
    if s_bnc:
        df_v = df_v[df_v['Banco'].isin(s_bnc)]
    if b_desc:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
    df_v_display = df_v[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].copy()
    df_v_display['Valor'] = df_v['V_Num'].apply(m_fmt)
    st.dataframe(df_v_display.iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    
    df_pet = df_base[df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False) | 
                     df_base['Descrição'].str.contains('Pet|Milo|Bolt', case=False, na=False)].copy()
    
    if not df_pet.empty:
        df_pet_mes = df_pet[(df_pet['Mes_Ano'] == mes_atual) & (df_pet['Status'] == 'Pago')]
        gasto_total_mes = df_pet_mes['V_Num'].sum()
        
        df_milo = df_pet[df_pet['Descrição'].str.contains('Milo', case=False, na=False) | 
                          df_pet['Categoria'].str.contains('Milo', case=False, na=False)]
        df_bolt = df_pet[df_pet['Descrição'].str.contains('Bolt', case=False, na=False) | 
                          df_pet['Categoria'].str.contains('Bolt', case=False, na=False)]
        
        m_milo = df_milo[(df_milo['Mes_Ano'] == mes_atual) & (df_milo['Status'] == 'Pago')]['V_Num'].sum()
        m_bolt = df_bolt[(df_bolt['Mes_Ano'] == mes_atual) & (df_bolt['Status'] == 'Pago')]['V_Num'].sum()
        
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.metric("📈 Gasto Total (Mês)", m_fmt(gasto_total_mes))
        c_p2.metric("🐶 Com o Milo (Mês)", m_fmt(m_milo))
        c_p3.metric("🐱 Com o Bolt (Mês)", m_fmt(m_bolt))
        
        st.divider()
        st.subheader("📋 Controle de Saúde e Ração")
        c_v1, c_v2 = st.columns(2)
        with c_v1:
            st.markdown("**💊 Vacinas, Vermífugos e Veterinário**")
            st.info("💡 *Dica: Ao lançar na descrição, coloque o nome do pet (ex: Vacina V10 Milo).*")
        with c_v2:
            st.markdown("**🛍️ Controle de Ração e PetShop**")
            st.info("💡 *Dica: Use a categoria 'Pet: Milo' ou 'Pet: Bolt' para facilitar a separação!*")
            
        st.divider()
        st.subheader("🔍 Lançamentos dos Meninos")
        
        c_f1, c_f2 = st.columns([1, 2])
        pet_escolha = c_f1.radio("Filtrar por Pet:", ["Todos", "Milo", "Bolt"], horizontal=True)
        
        df_show = df_pet.copy()
        if pet_escolha == "Milo":
            df_show = df_milo
        elif pet_escolha == "Bolt":
            df_show = df_bolt
            
        df_show_display = df_show[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Status']].copy()
        df_show_display['Valor'] = df_show['V_Num'].apply(m_fmt)
        st.dataframe(df_show_display.iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum lançamento encontrado para os meninos ainda. Faça um lançamento usando a categoria Pet!")

elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: c3.success("💡 RECOMENDAÇÃO: ABASTEÇA COM ÁLCOOL!")
        else: c3.warning("💡 RECOMENDAÇÃO: ABASTEÇA COM GASOLINA!")
    
    st.divider()
    
    st.subheader("⚙️ Controle de Troca de Óleo")
    km1, km2, km3 = st.columns(3)
    km_atual = km1.number_input("Quilometragem Atual (km)", value=0, step=500)
    km_oleo = km2.number_input("Km Última Troca de Óleo", value=0, step=500)
    limite_oleo = km3.number_input("Limite de Troca (km rodados)", value=10000, step=1000)
    
    if km_atual > 0 and km_oleo > 0:
        km_rodados = km_atual - km_oleo
        if km_rodados >= limite_oleo:
            st.error(f"🚨 ALERTA: Passou do limite para trocar o óleo! Rodou {km_rodados:,} km desde a última troca.")
        else:
            st.info(f"👍 Óleo em dia! Você rodou {km_rodados:,} km. Faltam {limite_oleo - km_rodados:,} km para a próxima troca.")
            
    st.divider()
    
    st.subheader("⛽ Cálculo de Consumo (Km/L)")
    st.info("💡 **Atenção:** Digite a quantidade de combustível em **Litros** (ex: 50.0) e a distância em **Quilômetros** (ex: 600.0), e não o valor monetário em R$.")
    
    c_cons1, c_cons2, c_cons3 = st.columns(3)
    litros = c_cons1.number_input("Litros Abastecidos", value=0.0, step=0.5)
    distancia = c_cons2.number_input("Distância Percorrida (km)", value=0.0, step=10.0)
    
    if litros > 0 and distancia > 0:
        consumo = distancia / litros
        c_cons3.success(f"📊 Consumo Médio: {consumo:.2f} km/l")
        
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        df_car_display = df_car[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].copy()
        df_car_display['Valor'] = df_car['V_Num'].apply(m_fmt)
        st.dataframe(df_car_display.iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba:
    st.title("📄 WhatsApp")
    
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", hoje_br - timedelta(days=30), format="DD/MM/YYYY", key="zap_d1")
    d_fim = c2.date_input("Fim", hoje_br, format="DD/MM/YYYY", key="zap_d2")
    
    saldos_txt = ""
    total_patrimonio = 0.0 
    
   # 1. LOOP PELOS BANCOS
    for b in sorted(bancos_disponiveis):
        valor_base_planilha = 0.0
        dia_fechamento = 1 # Valor padrão caso esteja vazio
        
        # Busca as informações na aba de Bancos
        if not df_bancos_info.empty:
            for _, row in df_bancos_info.iterrows():
                if str(row.iloc[0]).strip().upper() == str(b).strip().upper():
                    try:
                        # Coluna B: Valor (Saldo ou Limite)
                        v_raw = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        valor_base_planilha = float(v_raw) if v_raw and v_raw != 'nan' else 0.0
                        
                        # Coluna C: Dia de Fechamento (se existir)
                        if len(row) >= 3:
                            f_raw = str(row.iloc[2]).strip()
                            if f_raw and f_raw != 'nan':
                                dia_fechamento = int(float(f_raw))
                    except: pass
                    break
        
# 1. LOOP PELOS BANCOS (Ajustado para buscar PENDENTE no Cartão)
    for b in sorted(bancos_disponiveis):
        valor_b = 0.0      
        tipo_c = ""
        dia_fech_d = 1    
        dia_venc_e = 10   
        
        if not df_bancos_info.empty:
            for _, row in df_bancos_info.iterrows():
                if str(row.iloc[0]).strip().upper() == str(b).strip().upper():
                    try:
                        # B (1): Valor (Limite)
                        v_raw = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        valor_b = float(v_raw) if v_raw and v_raw != 'nan' else 0.0
                        
                        # C (2): Tipo
                        tipo_c = str(row.iloc[2]).strip().upper()
                        
                        # D (3): Fechamento
                        if len(row) >= 4:
                            f_raw = str(row.iloc[3]).replace('R$', '').strip()
                            dia_fech_d = int(float(f_raw)) if f_raw and f_raw != 'nan' else 1
                            
                        # E (4): Vencimento
                        if len(row) >= 5:
                            ven_raw = str(row.iloc[4]).replace('R$', '').strip()
                            dia_venc_e = int(float(ven_raw)) if ven_raw and ven_raw != 'nan' else 10
                    except: pass
                    break
        
     # --- LÓGICA DE CARTÃO (Soma Pendentes até a data Limite) ---
        if "CARTA" in tipo_c or "CART" in b.upper():
            limite_cartao = valor_b
            
            # Filtra a base: 
            # 1. Do banco específico
            # 2. Que seja Despesa
            # 3. Que esteja Pendente
            df_cart_base = df_base[(df_base['Banco'] == b) & 
                                   (df_base['Tipo'].str.upper() == 'DESPESA') & 
                                   (df_base['Status'].str.upper() == 'PENDENTE')].copy()
            
            # Garante que a coluna de data está em formato de data
            df_cart_base['DT_ONLY'] = pd.to_datetime(df_cart_base['DT']).dt.date
            
            # 🔥 O PULO DO GATO:
            # Soma tudo o que está pendente DESDE SEMPRE até a DATA FINAL (d_fim) selecionada.
            # Isso pega contas atrasadas e compras do mês, mas IGNORA parcelas futuras.
            usado = df_cart_base[df_cart_base['DT_ONLY'] <= d_fim]['V_Num'].sum()
            
            dispo = limite_cartao - usado
            
            saldos_txt += f"💳 {b}: Limite: {m_fmt(limite_cartao)} | Usado: {m_fmt(usado)} | Disp: {m_fmt(dispo)} (Venc: {dia_venc_e})\n"
        
        # --- LÓGICA DE CONTA / INVESTIMENTO ---
        else:
            saldo_inicial = valor_b
            # Para contas normais, mantemos apenas o que já foi 'Pago'
            mov_paga = df_base[(df_base['Banco'] == b) & (df_base['Status'].str.upper() == 'PAGO')]
            rec_b = mov_paga[mov_paga['Tipo'].str.upper().str.contains('RECEITA|REND', na=False)]['V_Num'].sum()
            des_b = mov_paga[mov_paga['Tipo'].str.upper() == 'DESPESA']['V_Num'].sum()
            s_final = saldo_inicial + rec_b - des_b
            
            icone = "💰" if "INVEST" in tipo_c else "🏦"
            saldos_txt += f"{icone} {b}: Saldo: {m_fmt(s_final)}\n"
            total_patrimonio += s_final

    # 2. RESUMO DO RELATÓRIO (Rendimento e Sobra)
    df_base['DT_ONLY'] = pd.to_datetime(df_base['DT']).dt.date
    df_per = df_base[(df_base['DT_ONLY'] >= d_ini) & (df_base['DT_ONLY'] <= d_fim)].copy()

    if not df_per.empty:
        df_per['T_UP'] = df_per['Tipo'].astype(str).str.upper().str.strip()
        df_per['C_UP'] = df_per['Categoria'].astype(str).str.upper().str.strip()
        
        # Procura REND na Categoria ou no Tipo
        mask_rend = (df_per['T_UP'].str.contains('REND', na=False)) | (df_per['C_UP'].str.contains('REND', na=False))
        rend_v = df_per[mask_rend & (df_per['Status'] == 'Pago')]['V_Num'].sum()
        
        rec_v = df_per[(df_per['T_UP'] == 'RECEITA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        des_v = df_per[(df_per['T_UP'] == 'DESPESA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        sobra = rec_v - des_v
    else:
        rec_v = des_v = rend_v = sobra = 0.0

    # 3. TEXTO FINAL
    relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
    relat += f"========================================\n"
    relat += f"REC: {m_fmt(rec_v)} | REND: {m_fmt(rend_v)} (Info)\n"
    relat += f"DES: {m_fmt(des_v)} | SOBRA: {m_fmt(sobra)}\n"
    relat += f"========================================\n\n"
    relat += f"SALDOS:\n{saldos_txt}\nTOTAL PATRIMÔNIO: {m_fmt(total_patrimonio)}"
    
    st.text_area("Copiar Relatório", relat, height=300)
    st.markdown(f'[📲 Enviar para o WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif "📋" in aba:
    st.title("📋 Gerador de Relatório PDF")
    
    c1, c2, c3 = st.columns(3)
    b_ini = c1.date_input("Data Inicial", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY", key="pdf_d1")
    b_fim = c2.date_input("Data Final", datetime.now(), format="DD/MM/YYYY", key="pdf_d2")
    
    st.divider()
    
    c_b1, c_b2, c_b3 = st.columns(3)
    s_bnc_rel = c_b1.multiselect("Filtrar por Banco:", sorted(bancos_disponiveis))
    s_sta_rel = c_b2.multiselect("Filtrar por Status:", ["Pago", "Pendente"])
    b_desc_rel = c_b3.text_input("Buscar por Descrição:")
    
    st.divider()
    
    df_v = df_base.copy()
    df_v = df_v[df_v['DT'].notna()]
    df_v = df_v[(df_v['DT'].dt.date >= b_ini) & (df_v['DT'].dt.date <= b_fim)]
    
    if s_bnc_rel:
        df_v = df_v[df_v['Banco'].isin(s_bnc_rel)]
    if s_sta_rel:
        df_v = df_v[df_v['Status'].isin(s_sta_rel)]
    if b_desc_rel:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc_rel, case=False, na=False)]
        
    st.subheader("Lançamentos Filtrados")
    df_v_display = df_v[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].copy()
    df_v_display['Valor'] = df_v['V_Num'].apply(m_fmt)
    st.dataframe(df_v_display.iloc[::-1], use_container_width=True, hide_index=True)
    
    st.divider()
    
    if st.button("📄 Gerar PDF"):
        if df_v.empty:
            st.warning("Nenhum lançamento selecionado para gerar o PDF.")
        else:
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", size=10)
                
                pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
                pdf.ln(2)
                pdf.cell(200, 10, txt=f"Periodo: {b_ini.strftime('%d/%m/%Y')} a {b_fim.strftime('%d/%m/%Y')}", ln=1, align="L")
                
                filtros_texto = []
                if s_bnc_rel: filtros_texto.append(f"Bancos: {', '.join(s_bnc_rel)}")
                if s_sta_rel: filtros_texto.append(f"Status: {', '.join(s_sta_rel)}")
                if b_desc_rel: filtros_texto.append(f"Descricao: {b_desc_rel}")
                
                texto_filtros = "Filtros: " + (" | ".join(filtros_texto) if filtros_texto else "Nenhum")
                pdf.cell(200, 10, txt=texto_filtros, ln=1, align="L")
                pdf.ln(2)
                
                df_v = df_v.sort_values(by='DT')
                df_v['Saldo_Acum'] = df_v['V_Num'].cumsum()
                
                pdf.cell(20, 8, "Data", 1)
                pdf.cell(25, 8, "Tipo", 1)
                pdf.cell(25, 8, "Valor", 1)
                pdf.cell(25, 8, "Saldo Acum.", 1)
                pdf.cell(75, 8, "Descricao", 1)
                pdf.cell(20, 8, "Status", 1)
                pdf.ln()
                
                for index, row in df_v.iterrows():
                    pdf.cell(20, 6, str(row['Data']), 1)
                    pdf.cell(25, 6, str(row['Tipo']), 1)
                    pdf.cell(25, 6, f"R$ {row['V_Num']:.2f}".replace('.', ','), 1)
                    pdf.cell(25, 6, f"R$ {row['Saldo_Acum']:.2f}".replace('.', ','), 1)
                    pdf.cell(75, 6, str(row['Descrição'])[:40], 1)
                    pdf.cell(20, 6, str(row['Status']), 1)
                    pdf.ln()
                
                pdf_output = pdf.output(dest='S')
                if isinstance(pdf_output, str):
                    pdf_output = pdf_output.encode('latin-1')
                    
                st.download_button(
                    label="📥 Baixar PDF",
                    data=pdf_output,
                    file_name="relatorio.pdf",
                    mime="application/pdf"
                )
                st.success("PDF gerado com sucesso!")
            except Exception as e:
                st.error(f"Erro ao gerar o PDF: {e}")
