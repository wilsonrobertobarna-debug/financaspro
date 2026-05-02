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

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.3")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES MAIS COMPACTOS
st.markdown("<style>[data-testid='stMetricValue'] {font-size: 0.95rem !important;}</style>", unsafe_allow_html=True)

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
    df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
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
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Internet","Vestuário","Moradia", "Saúde","Previdência","Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
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
            
            # Campos editáveis
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
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
        
        saldo_geral = df_m_limpo[df_m_limpo['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(get_valor_pendente(df_base)))
        
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
        df_saldo_dia = df_base[df_base['Status'] == 'Pago'].sort_values('DT').copy()
        if not df_saldo_dia.empty:
            df_saldo_dia['Valor_Com_Sinal'] = df_saldo_dia.apply(
                lambda x: x['V_Num'] if x['Tipo'] in ['Receita', 'Rendimento'] else -x['V_Num'], axis=1
            )
            df_saldo_dia = df_saldo_dia.groupby('Data')['Valor_Com_Sinal'].sum().reset_index()
            df_saldo_dia['Saldo_Acumulado'] = df_saldo_dia['Valor_Com_Sinal'].cumsum()
            
            fig_acum = px.line(df_saldo_dia, x='Data', y='Saldo_Acumulado', title="Progresso do Patrimônio Acumulado no Tempo", markers=True)
            fig_acum.update_layout(height=350)
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
        st.dataframe(df_v[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)

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
            
        st.dataframe(df_show[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)
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
    c_cons1, c_cons2, c_cons3 = st.columns(3)
    litros = c_cons1.number_input("Litros Abastecidos", value=0.0, step=0.5)
    distancia = c_cons2.number_input("Distância Percorrida (km)", value=0.0, step=10.0)
    
    if litros > 0 and distancia > 0:
        consumo = distancia / litros
        c_cons3.success(f"📊 Consumo Médio: {consumo:.2f} km/l")
        
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        st.dataframe(df_car[['ID', 'Data', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba:
    st.title("📄 WhatsApp")
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY")
    d_fim = c2.date_input("Fim", datetime.now(), format="DD/MM/YYYY")
    
    bancos = sorted(bancos_disponiveis)
    saldos_txt = ""
    total_b = 0
    
    for b in bancos:
        saldo = 0.0
        limite = 0.0
        
        if not df_bancos_info.empty:
            for _, row in df_bancos_info.iterrows():
                if str(row.iloc[0]).strip() == b:
                    if len(row) > 1:
                        try:
                            val_str = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                            if val_str:
                                saldo = float(val_str)
                        except:
                            saldo = 0.0
                            
                    if len(row) >= 3:
                        try:
                            lim_str = str(row.iloc[2]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                            if lim_str:
                                limite = float(lim_str)
                        except:
                            limite = 0.0
                    break
                    
        utilizado = df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
        
        # SÓ APLICA O CÁLCULO DE SALDO NOS BANCOS, CARTÕES PERMANECEM INALTERADOS
        if "cartão" not in b.lower():
            receitas_b = df_base[(df_base['Banco'] == b) & (df_base['Tipo'].isin(['Receita', 'Rendimento'])) & (df_base['Mes_Ano'] == mes_atual) & (df_base['Status'] == 'Pago')]['V_Num'].sum()
            despesas_b = df_base[(df_base['Banco'] == b) & (df_base['Tipo'] == 'Despesa') & (df_base['Mes_Ano'] == mes_atual) & (df_base['Status'] == 'Pago')]['V_Num'].sum()
            saldo = saldo + receitas_b - despesas_b
        
        if "cartão" in b.lower():
            if limite > 0:
                disponivel = limite - utilizado
            else:
                disponivel = saldo - utilizado
            saldos_txt += f"💳 {b}: Saldo: {m_fmt(saldo)} | Utilizado: {m_fmt(utilizado)} | A utilizar: {m_fmt(disponivel)}\n"
        else:
            saldos_txt += f"🏦 {b}: Saldo: {m_fmt(saldo)}\n"
            
        if "cartão" not in b.lower():
            total_b += saldo
            
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    
    if not df_per.empty:
        df_per_limpo = df_per[(df_per['Categoria'] != 'Transferência') & (df_per['Status'] == 'Pago')]
        r_v = df_per_limpo[df_per_limpo['Tipo'] == 'Receita']['V_Num'].sum()
        d_v = df_per_limpo[df_per_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        rend_v = df_per_limpo[df_per_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()
        pend_v = get_valor_pendente(df_base)
    else:
        r_v = 0
        d_v = 0
        rend_v = 0
        pend_v = 0
        
    relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n========================================\nREC: {m_fmt(r_v)}\nDES: {m_fmt(d_v)}\nREND: {m_fmt(rend_v)}\nPEND: {m_fmt(pend_v)}\nSOBRA: {m_fmt((r_v+rend_v)-d_v)}\n========================================\n\nSALDOS:\n{saldos_txt}\nTOTAL PATRIMÔNIO: {m_fmt(total_b)}"
    
    st.text_area("Copiar para Zap/E-mail", relat, height=400)
    zap_link = f"https://wa.me/?text={urllib.parse.quote(relat)}"
    st.markdown(f'[📲 Enviar para o WhatsApp]({zap_link})')

elif "📋" in aba:
    st.title("📋 Gerador de Relatório PDF")
    
    c1, c2, c3 = st.columns(3)
    b_ini = c1.date_input("Data Inicial", datetime.now() - relativedelta(months=1), format="DD/MM/YYYY", key="pdf_ini")
    b_fim = c2.date_input("Data Final", datetime.now(), format="DD/MM/YYYY", key="pdf_fim")
    b_bnc = c3.multiselect("Bancos", sorted(bancos_disponiveis), key="pdf_bnc")
    
    c4, c5 = st.columns([1, 2])
    b_sta = c4.multiselect("Status", ["Pago", "Pendente"], key="pdf_sta")
    b_desc = c5.text_input("Filtrar Descrição", key="pdf_desc")
    
    df_pdf = df_base.copy()
    df_pdf = df_pdf[(df_pdf['DT'].dt.date >= b_ini) & (df_pdf['DT'].dt.date <= b_fim)]
    if b_bnc: df_pdf = df_pdf[df_pdf['Banco'].isin(b_bnc)]
    if b_sta: df_pdf = df_pdf[df_pdf['Status'].isin(b_sta)]
    if b_desc: df_pdf = df_pdf[df_pdf['Descrição'].str.contains(b_desc, case=False, na=False)]
    
    st.write(f"**Lançamentos encontrados:** {len(df_pdf)}")
    st.dataframe(df_pdf[['Data', 'Descrição', 'Valor', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)
    
    if st.button("📄 GERAR PDF AGORA"):
        pdf = FPDF()
        pdf.add_page()
        
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(190, 10, "Relatório FinançasPro - Wilson", 0, 1, 'C')
        pdf.set_font("Arial", '', 10)
        pdf.cell(190, 10, f"Período: {b_ini.strftime('%d/%m/%Y')} a {b_fim.strftime('%d/%m/%Y')}", 0, 1, 'C')
        pdf.ln(5)
        
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(25, 8, "Data", 1, 0, 'C', 1)
        pdf.cell(75, 8, "Descricao", 1, 0, 'L', 1)
        pdf.cell(30, 8, "Valor", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Banco", 1, 0, 'C', 1)
        pdf.cell(30, 8, "Status", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 9)
        total_periodo = 0
        r_v, d_v, rend_v = 0, 0, 0
        
        df_per = df_base[(df_base['DT'].dt.date >= b_ini) & (df_base['DT'].dt.date <= b_fim)].copy()
        if not df_per.empty:
            df_per_limpo = df_per[(df_per['Categoria'] != 'Transferência') & (df_per['Status'] == 'Pago')]
            r_v = df_per_limpo[df_per_limpo['Tipo'] == 'Receita']['V_Num'].sum()
            d_v = df_per_limpo[df_per_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
            rend_v = df_per_limpo[df_per_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()

        totais_diarios = {}

        for _, row in df_pdf.iterrows():
            pdf.cell(25, 7, str(row['Data']), 1, 0, 'C')
            pdf.cell(75, 7, str(row['Descrição'])[:40], 1, 0, 'L')
            pdf.cell(30, 7, f"R$ {row['Valor']}", 1, 0, 'R')
            pdf.cell(30, 7, str(row['Banco']), 1, 0, 'C')
            pdf.cell(30, 7, str(row['Status']), 1, 1, 'C')
            total_periodo += row['V_Num']
            
            d_atual = row['Data']
            tipo = row['Tipo']
            v_num = row['V_Num']
            
            if d_atual not in totais_diarios:
                totais_diarios[d_atual] = {'Receita': 0.0, 'Despesa': 0.0, 'Rendimento': 0.0}
            
            if tipo in ['Receita', 'Rendimento']:
                totais_diarios[d_atual][tipo] += v_num
            elif tipo == 'Despesa':
                totais_diarios[d_atual]['Despesa'] += v_num
            
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "Resumo do Periodo", 0, 1, 'L')
        pdf.set_font("Arial", '', 9)
        pdf.cell(95, 5, f"Total Receitas: {m_fmt(r_v)}", 0, 0, 'L')
        pdf.cell(95, 5, f"Total Despesas: {m_fmt(d_v)}", 0, 1, 'L')
        pdf.cell(95, 5, f"Total Rendimentos: {m_fmt(rend_v)}", 0, 0, 'L')
        pdf.cell(95, 5, f"Saldo (Sobra): {m_fmt((r_v + rend_v) - d_v)}", 0, 1, 'L')
        
        pdf.ln(5)
        
        pdf.set_font("Arial", 'B', 10)
        pdf.cell(190, 6, "Saldo Dia a Dia", 0, 1, 'L')
        
        pdf.set_fill_color(220, 220, 220)
        pdf.set_font("Arial", 'B', 8)
        pdf.cell(30, 6, "Data", 1, 0, 'C', 1)
        pdf.cell(40, 6, "Receitas", 1, 0, 'C', 1)
        pdf.cell(40, 6, "Despesas", 1, 0, 'C', 1)
        pdf.cell(40, 6, "Rendimentos", 1, 0, 'C', 1)
        pdf.cell(40, 6, "Saldo do Dia", 1, 1, 'C', 1)
        
        pdf.set_font("Arial", '', 8)
        for data, valores in totais_diarios.items():
            saldo_dia = (valores['Receita'] + valores['Rendimento']) - valores['Despesa']
            pdf.cell(30, 5, str(data), 1, 0, 'C')
            pdf.cell(40, 5, m_fmt(valores['Receita']), 1, 0, 'R')
            pdf.cell(40, 5, m_fmt(valores['Despesa']), 1, 0, 'R')
            pdf.cell(40, 5, m_fmt(valores['Rendimento']), 1, 0, 'R')
            pdf.cell(40, 5, m_fmt(saldo_dia), 1, 1, 'R')
            
        pdf.ln(5)
        pdf.set_font("Arial", 'B', 11)
        pdf.cell(190, 8, f"Total dos Lancamentos: {m_fmt(total_periodo)}", 0, 1, 'R')
        
        pdf_output = pdf.output(dest='S').encode('latin-1', 'replace')
        st.download_button(label="📥 Baixar PDF", data=pdf_output, file_name=f"Relatorio_Wilson_{datetime.now().strftime('%d%m%y')}.pdf", mime="application/pdf")
