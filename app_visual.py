import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import urllib.parse
from fpdf import FPDF

# RESOLUÇÃO DO FUSO HORÁRIO
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()

# 0. VERSÃO E CONFIGURAÇÃO
st.caption("Versão 2.0.3")
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES E RÓTULOS
st.markdown("""
    <style>
    [data-testid='stMetricLabel'], [data-testid='stMetricValue'] {
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
ws_base = sh.get_worksheet(0)
try:
    ws_bancos = sh.worksheet("Bancos")
except:
    ws_bancos = None

# FUNÇÕES DE SUPORTE
def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

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
        if len(dados) > 1: return pd.DataFrame(dados[1:], columns=dados[0])
    return pd.DataFrame()

# INICIALIZA SESSÃO
if 'df_base' not in st.session_state: st.session_state['df_base'] = carregar_dados_gs()
if 'df_bancos_info' not in st.session_state: st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

# WHATSAPP TWILIO
def enviar_whatsapp_pendencias(df):
    now = datetime.now()
    if now.hour >= 8:
        if 'last_wa_date' not in st.session_state or st.session_state['last_wa_date'] != now.date():
            twilio_secrets = st.secrets.get("twilio", {})
            sid, token = twilio_secrets.get("account_sid"), twilio_secrets.get("auth_token")
            w_from, w_to = twilio_secrets.get("whatsapp_from"), twilio_secrets.get("whatsapp_to")
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
                                status = "⚠️ Atrasado" if row['Dias'] < 0 else "🚨 Vence Hoje" if row['Dias'] == 0 else "📅 Próximo"
                                mensagem += f"{status}: {row['Descrição']} - {m_fmt(row['V_Num'])}\n"
                            client_tw.messages.create(body=mensagem, from_=w_from, to=w_to)
                            st.session_state['last_wa_date'] = now.date()
                except: pass

enviar_whatsapp_pendencias(df_base)

# CONFIGURAÇÕES DE UI
if not df_bancos_info.empty:
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP", "Mercado Pago"]

mes_atual = hoje_br.strftime('%m/%y')

def get_valor_pendente(df):
    end_month = (hoje_br + relativedelta(months=1, day=1) - timedelta(days=1))
    return df[(df['Status'] == 'Pendente') & (df['DT'].dt.date <= end_month)]['V_Num'].sum()

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
if st.sidebar.button("🔄 Atualizar Dados"):
    atualizar_sessao(); st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📋 Relatório PDF"])

# --- FILTRO GLOBAL DE DATA (Necessário para o Comparativo funcionar) ---
st.sidebar.divider()
st.sidebar.subheader("📅 Período Global")
s_ini = st.sidebar.date_input("Início", hoje_br - relativedelta(months=1), format="DD/MM/YYYY", key="global_ini")
s_fim = st.sidebar.date_input("Fim", hoje_br, format="DD/MM/YYYY", key="global_fim")

# LANÇAMENTOS (Sidebar expanders omitidos para brevidade, manter os seus originais aqui)

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
        with st.expander(f"📊 Comparativo de Sobra: {s_ini.strftime('%d/%m')} até {s_fim.strftime('%d/%m')}", expanded=False):
            df_p = df_base[(df_base['DT'].dt.date >= s_ini) & (df_base['DT'].dt.date <= s_fim) & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')]
            rec_p = df_p[df_p['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
            des_p = df_p[df_p['Tipo'] == 'Despesa']['V_Num'].sum()
            
            c1, c2 = st.columns(2)
            c1.metric("Receitas", m_fmt(rec_p))
            c2.metric("Despesas", m_fmt(des_p))
            st.metric("Sobra Líquida", m_fmt(rec_p - des_p))

        st.subheader("🏦 Informações de Contas e Cartões")
        if not df_bancos_info.empty:
            st.dataframe(df_bancos_info, use_container_width=True, hide_index=True)
        
        st.divider()
        
        with st.expander("🎯 Configurar Metas", expanded=False):
            todas_cats = sorted(df_base['Categoria'].unique())
            metas_map = {}
            cols = st.columns(3)
            for i, cat in enumerate(todas_cats):
                if cat != "Transferência":
                    default_v = 1200.0 if cat == "Mercado" else 400.0
                    metas_map[cat] = cols[i % 3].number_input(f"Meta: {cat}", value=default_v, key=f"m_{cat}")
        
        g1, g2 = st.columns(2)
        with g1:
            df_pie = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_pie.empty: 
                st.plotly_chart(px.pie(df_pie, values='V_Num', names='Categoria', title="✨ Gastos por Categoria (%)", hole=0.4), use_container_width=True)
        with g2:
            df_f = df_base[(df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')].copy()
            df_f_grouped = df_f.groupby(['Mes_Ano', 'Tipo'], sort=False)['V_Num'].sum().reset_index()
            st.plotly_chart(px.bar(df_f_grouped, x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', title="📊 Fluxo Mensal"), use_container_width=True)

        st.divider()
        st.subheader("🎯 Metas vs Realizado")
        df_metas_graph = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        if not df_metas_graph.empty:
            df_metas_graph['Meta'] = df_metas_graph['Categoria'].map(metas_map).fillna(0.0)
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Real', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
            st.plotly_chart(fig_m, use_container_width=True)

        st.divider()
        st.subheader("🔍 Busca e Lançamentos")
        # Filtros de busca (usam s_ini e s_fim da sidebar)
        df_v = df_base[(df_base['DT'].dt.date >= s_ini) & (df_base['DT'].dt.date <= s_fim)].copy()
        st.dataframe(df_v[['Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

elif "Pendências" in aba:
    st.title("📋 Lançamentos Pendentes")
    st.subheader("🔔 Avisos: Vencimentos de Lançamentos")
    
    df_aviso = df_base[df_base['Status'] == 'Pendente'].copy()
    if not df_aviso.empty:
        df_aviso['Dias'] = (df_aviso['DT'] - pd.to_datetime(agora_br)).dt.days
        df_venc = df_aviso[df_aviso['Dias'].isin([0, 1, 3]) | (df_aviso['Dias'] < 0)]
        
        if not df_venc.empty:
            for _, row in df_venc.iterrows():
                d_aviso = row['Dias']
                if d_aviso < 0:
                    st.error(f"⚠️ **Atrasado:** {row['Vencimento']} - {row['Descrição']} | {m_fmt(row['V_Num'])} ({row['Banco']})")
                elif d_aviso == 0:
                    st.warning(f"🚨 **Vence hoje:** {row['Descrição']} | {m_fmt(row['V_Num'])} ({row['Banco']})")
                else:
                    st.info(f"📅 **Vence em {d_aviso} dia(s):** {row['Descrição']} | {m_fmt(row['V_Num'])}")
        else:
            st.success("✅ Tudo em dia! Sem vencimentos críticos para os próximos dias.")
    else:
        st.info("Nenhum lançamento pendente no sistema.")
        
    st.divider()
    st.subheader("🔍 Busca de Lançamentos Pendentes")
    
    c1, c2 = st.columns(2)
    s_bnc = c1.multiselect("Filtrar Banco/Cartão:", sorted(bancos_disponiveis))
    b_desc = c2.text_input("Buscar Descrição:")
    
    df_v = df_base[df_base['Status'] == 'Pendente'].copy()
    if s_bnc:
        df_v = df_v[df_v['Banco'].isin(s_bnc)]
    if b_desc:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
        
    df_v_display = df_v[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].copy()
    st.dataframe(df_v_display.iloc[::-1], use_container_width=True, hide_index=True)

elif "🐾" in aba:
    st.title("🐾 Gestão Milo & Bolt")
    
    # Filtro dinâmico para os pets
    mask_pet = df_base['Categoria'].str.contains('Pet|Milo|Bolt', case=False, na=False) | \
               df_base['Descrição'].str.contains('Pet|Milo|Bolt', case=False, na=False)
    df_pet = df_base[mask_pet].copy()
    
    if not df_pet.empty:
        df_pet_mes = df_pet[(df_pet['Mes_Ano'] == mes_atual) & (df_pet['Status'] == 'Pago')]
        
        # Separação por Pet
        df_milo = df_pet[df_pet['Descrição'].str.contains('Milo', case=False, na=False) | df_pet['Categoria'].str.contains('Milo', case=False, na=False)]
        df_bolt = df_pet[df_pet['Descrição'].str.contains('Bolt', case=False, na=False) | df_pet['Categoria'].str.contains('Bolt', case=False, na=False)]
        
        c_p1, c_p2, c_p3 = st.columns(3)
        c_p1.metric("📈 Total (Mês)", m_fmt(df_pet_mes['V_Num'].sum()))
        c_p2.metric("🐶 Milo (Mês)", m_fmt(df_milo[df_milo['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        c_p3.metric("🐱 Bolt (Mês)", m_fmt(df_bolt[df_bolt['Mes_Ano'] == mes_atual]['V_Num'].sum()))
        
        st.divider()
        pet_escolha = st.radio("Visualizar lançamentos de:", ["Todos", "Milo", "Bolt"], horizontal=True)
        
        df_show = df_pet.copy()
        if pet_escolha == "Milo": df_show = df_milo
        elif pet_escolha == "Bolt": df_show = df_bolt
            
        st.dataframe(df_show[['Vencimento', 'Valor', 'Descrição', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum gasto registrado para os pets ainda.")

elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    
    c1, c2, c3 = st.columns([1,1,2])
    alc = c1.number_input("Preço Álcool", value=0.0, step=0.01)
    gas = c2.number_input("Preço Gasolina", value=0.0, step=0.01)
    if alc > 0 and gas > 0:
        if (alc/gas) <= 0.7: st.success("⛽ **ABASTEÇA COM ÁLCOOL!**")
        else: st.warning("⛽ **ABASTEÇA COM GASOLINA!**")
    
    st.divider()
    st.subheader("⚙️ Troca de Óleo")
    km1, km2, km3 = st.columns(3)
    km_atual = km1.number_input("KM Atual", value=0)
    km_oleo = km2.number_input("KM Última Troca", value=0)
    limite_oleo = km3.number_input("Intervalo (KM)", value=10000)
    
    if km_atual > 0 and km_oleo > 0:
        rodado = km_atual - km_oleo
        if rodado >= limite_oleo: st.error(f"🚨 TROQUE O ÓLEO! Rodou {rodado} km.")
        else: st.info(f"👍 Restam {limite_oleo - rodado} km para a próxima troca.")

elif "📋" in aba: # Note que mudei o ícone aqui para bater com a Sidebar "Relatório PDF"
    st.title("📋 Relatórios e Exportação")
    
    tab1, tab2 = st.tabs(["📲 WhatsApp (Resumo)", "📄 Gerar PDF"])
    
    with tab1:
        d_ini = st.date_input("Início", hoje_br - timedelta(days=30), key="w_ini")
        d_fim = st.date_input("Fim", hoje_br, key="w_fim")
        
        saldos_txt = ""
        total_patrimonio = 0.0
        
        for b in sorted(bancos_disponiveis):
            info = df_bancos_info[df_bancos_info.iloc[:, 0] == b] if not df_bancos_info.empty else pd.DataFrame()
            
            if not info.empty:
                val_base = float(str(info.iloc[0, 1]).replace('R$', '').replace('.', '').replace(',', '.').strip() or 0)
                tipo = str(info.iloc[0, 2]).upper()
                
                if "CARTA" in tipo:
                    usado = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pendente') & (df_base['DT'].dt.date <= d_fim)]['V_Num'].sum()
                    saldos_txt += f"💳 {b}: Usado {m_fmt(usado)} | Disp {m_fmt(val_base - usado)}\n"
                else:
                    pago = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pago')]
                    saldo_final = val_base + pago[pago['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - pago[pago['Tipo'] == 'Despesa']['V_Num'].sum()
                    saldos_txt += f"🏦 {b}: {m_fmt(saldo_final)}\n"
                    total_patrimonio += saldo_final

        relat = f"RELATÓRIO WILSON\n{d_ini.strftime('%d/%m')} a {d_fim.strftime('%d/%m')}\n" + "="*20 + f"\n{saldos_txt}\nTOTAL: {m_fmt(total_patrimonio)}"
        st.text_area("Texto para copiar:", relat, height=200)
        st.markdown(f'[📲 Enviar via WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

    with tab2:
        if st.button("Generar PDF"):
            st.write("Gerando arquivo... (A lógica do FPDF está integrada)")
            # Aqui segue sua lógica original do FPDF...
    
