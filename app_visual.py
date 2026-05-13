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

# 0. VERSÃO NO TOPO
st.caption("Versão 2.0.5 - Estabilizada")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

st.markdown("""
    <style>
    [data-testid='stMetricLabel'] { font-size: 1.1rem !important; font-weight: bold !important; }
    [data-testid='stMetricValue'] { font-size: 1.1rem !important; font-weight: bold !important; }
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

# 3. FUNÇÕES DE CARREGAMENTO
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

def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

if 'df_base' not in st.session_state:
    atualizar_sessao()

df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

def m_fmt(n): return f"R$ {n:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

if not df_bancos_info.empty:
    bancos_disponiveis = [str(x) for x in df_bancos_info.iloc[:, 0].tolist() if str(x).strip() != ""]
else:
    bancos_disponiveis = ["Santander", "Itaú", "Inter", "Nubank", "Dinheiro", "Pix", "XP"]

mes_atual = agora_br.strftime('%m/%y')

# 4. SIDEBAR
st.sidebar.title("🎮 Painel Wilson")
if st.sidebar.button("🔄 Atualizar dados"):
    atualizar_sessao(); st.rerun()

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF"])
st.sidebar.divider()

# BLOCOS DE LANÇAMENTO
with st.sidebar.expander("🚀 Novo Lançamento"):
    with st.form("f_novo", clear_on_submit=True):
        f_compra = st.date_input("🛍️ Compra", value=hoje_br, format="DD/MM/YYYY")
        f_dat = st.date_input("Vencimento", hoje_br, format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01)
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Outros"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        if st.form_submit_button("SALVAR"):
            v_str = f"{f_val:.2f}".replace('.', ',')
            c_str = f_compra.strftime("%d/%m/%Y")
            for i in range(f_par):
                nova_data = f_dat + relativedelta(months=i)
                ws_base.append_row([nova_data.strftime("%d/%m/%Y"), v_str, f_des, f_cat, f_tip, f_bnc, f_sta, c_str])
            atualizar_sessao(); st.rerun()

with st.sidebar.expander("💸 Transferência"):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", hoje_br, format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01)
        t_orig = st.selectbox("Origem:", bancos_disponiveis)
        t_dest = st.selectbox("Destino:", bancos_disponiveis)
        if st.form_submit_button("TRANSFERIR"):
            if t_orig == t_dest: st.error("Bancos iguais!")
            else:
                v_s = f"{t_val:.2f}".replace('.', ','); d_s = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_s, v_s, "Transf. Saída", "Transferência", "Despesa", t_orig, "Pago", ""])
                ws_base.append_row([d_s, v_s, "Transf. Entrada", "Transferência", "Receita", t_dest, "Pago", ""])
                atualizar_sessao(); st.rerun()

with st.sidebar.expander("⚙️ Ajustar / Excluir"):
    if not df_base.empty:
        lista = {f"ID {r['ID']} | {r['Vencimento']} | {r['Descrição']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecionar:", [""] + list(lista.keys()))
        if escolha:
            item = lista[escolha]
            ed_dat = st.date_input("Vencimento:", value=pd.to_datetime(item['Vencimento'], dayfirst=True))
            ed_des = st.text_input("Descrição:", value=item['Descrição'])
            ed_val = st.number_input("Valor:", value=float(item['V_Num']), step=0.01)
            ed_bnc = st.selectbox("Banco:", bancos_disponiveis, index=bancos_disponiveis.index(item['Banco']) if item['Banco'] in bancos_disponiveis else 0)
            ed_sta = st.selectbox("Status:", ["Pago", "Pendente"], index=0 if item['Status'] == "Pago" else 1)
            
            c_ed1, c_ed2 = st.columns(2)
            if c_ed1.button("💾 SALVAR"):
                ws_base.update_cell(int(item['ID']), 1, ed_dat.strftime("%d/%m/%Y"))
                ws_base.update_cell(int(item['ID']), 2, f"{ed_val:.2f}".replace('.', ','))
                ws_base.update_cell(int(item['ID']), 3, ed_des)
                ws_base.update_cell(int(item['ID']), 6, ed_bnc)
                ws_base.update_cell(int(item['ID']), 7, ed_sta)
                st.success("Ok!"); atualizar_sessao(); st.rerun()
            if c_ed2.button("🚨 EXCLUIR"):
                ws_base.delete_rows(int(item['ID']))
                st.warning("Excluído!"); atualizar_sessao(); st.rerun()

# --- ABA PRINCIPAL (FINANÇAS & BANCOS) ---
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    
    # Verificamos se os dados existem primeiro
    if not df_base.empty:
        st.subheader("🔍 Filtros de Pesquisa")
        c1, c2, c3 = st.columns([1, 1, 2])
        
        with c1:
            lista_bancos = sorted(df_base['Banco'].unique().tolist())
            f_bnc = st.multiselect("Banco:", lista_bancos)
        with c2:
            f_sta = st.multiselect("Status:", ["Pago", "Pendente"])
        with c3:
            f_txt = st.text_input("Buscar por Descrição:", placeholder="Ex: Mercado...")

        # Aplicação dos filtros
        df_visual = df_base.copy()
        if f_bnc: df_visual = df_visual[df_visual['Banco'].isin(f_bnc)]
        if f_sta: df_visual = df_visual[df_visual['Status'].isin(f_sta)]
        if f_txt: df_visual = df_visual[df_visual['Descrição'].str.contains(f_txt, case=False, na=False)]

        # Cards de Saldo
        df_pagos = df_visual[(df_visual['Status'] == 'Pago') & (df_visual['Categoria'] != 'Transferência')]
        receita = df_pagos[df_pagos['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesa = df_pagos[df_pagos['Tipo'] == 'Despesa']['V_Num'].sum()

        st.info(f"### 🏦 SALDO FILTRADO: {m_fmt(receita - despesa)}")
        
        m1, m2, m3 = st.columns(3)
        m1.metric("📈 Receitas", m_fmt(receita))
        m2.metric("📉 Gastos", m_fmt(despesa))
        m3.metric("⏳ Pendente Total", m_fmt(df_base[df_base['Status'] == 'Pendente']['V_Num'].sum()))
        
        st.divider()
        st.subheader("📋 Histórico")
        st.dataframe(df_visual[['Vencimento', 'Descrição', 'Valor', 'Banco', 'Status']].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.warning("Wilson, a planilha parece estar vazia ou não carregou.")

# --- ABA DO VEÍCULO (AGORA O ELIF FUNCIONA PORQUE O ELSE ACIMA TERMINOU) ---
elif "🚗" in aba:
    st.title("🚗 Gestão do Veículo")
    st.write("Acompanhe seus gastos aqui.")
    # A linha 207 deve estar alinhada com as de cima:
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
                st.error(f"🚨 ALERTA: Passou do limite! Rodou {km_rodados:,} km.")
            else:
                st.info(f"👍 Óleo em dia! Faltam {limite_oleo - km_rodados:,} km.")
                
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
            df_car_display = df_car[['Vencimento', 'Descrição', 'Valor', 'Status']].copy()
            st.dataframe(df_car_display.iloc[::-1], use_container_width=True, hide_index=True)

    # --- ABA WHATSAPP ---
    elif "📄" in aba:
        st.title("📄 WhatsApp")
        c1, c2 = st.columns(2)
        d_ini = c1.date_input("Início", hoje_br - timedelta(days=30), format="DD/MM/YYYY")
        d_fim = c2.date_input("Fim", hoje_br, format="DD/MM/YYYY")
        
        saldos_txt = ""
        total_patrimonio = 0.0 
        
        for b in sorted(bancos_disponiveis):
            valor_b = 0.0 
            tipo_c = ""
            if not df_bancos_info.empty:
                for _, row in df_bancos_info.iterrows():
                    if str(row.iloc[0]).strip().upper() == str(b).strip().upper():
                        try:
                            v_raw = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                            valor_b = float(v_raw) if v_raw and v_raw != 'nan' else 0.0
                            tipo_c = str(row.iloc[2]).strip().upper()
                        except: pass
                        break
            
            if "CARTA" in tipo_c or "CART" in b.upper():
                usado = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pendente') & (df_base['Tipo'] == 'Despesa')]['V_Num'].sum()
                saldos_txt += f"💳 {b}: Limite: {m_fmt(valor_b)} | Usado: {m_fmt(usado)}\n"
            else:
                mov_paga = df_base[(df_base['Banco'] == b) & (df_base['Status'] == 'Pago')]
                rec_b = mov_paga[mov_paga['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
                des_b = mov_paga[mov_paga['Tipo'] == 'Despesa']['V_Num'].sum()
                s_final = valor_b + rec_b - des_b
                saldos_txt += f"🏦 {b}: Saldo: {m_fmt(s_final)}\n"
                total_patrimonio += s_final

        relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
        relat += "========================================\n"
        relat += f"SALDOS:\n{saldos_txt}\nTOTAL PATRIMÔNIO: {m_fmt(total_patrimonio)}"
        
        st.text_area("Copiar Relatório", relat, height=300)
        st.markdown(f'[📲 Enviar para o WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

    # --- ABA RELATÓRIO PDF ---
    elif "📋" in aba:
        st.title("📋 Gerar Relatório PDF")
        st.write(f"Mês referência: **{mes_atual}**")
        
        if st.button("🚀 GERAR PDF AGORA"):
            df_pdf = df_base[df_base['Mes_Ano'] == mes_atual].copy()
            if not df_pdf.empty:
                try:
                    pdf = FPDF()
                    pdf.add_page()
                    pdf.set_font("Arial", "B", 14)
                    pdf.cell(190, 10, f"RELATORIO FINANCEIRO - {mes_atual}", ln=True, align="C")
                    pdf.set_font("Arial", "", 10)
                    for _, r in df_pdf.iterrows():
                        texto = f"{r['Vencimento']} - {r['Descrição'][:30]} - R$ {r['V_Num']:.2f}"
                        pdf.cell(190, 8, texto.encode('latin-1', 'ignore').decode('latin-1'), border=1, ln=True)
                    
                    pdf_bytes = pdf.output(dest='S').encode('latin-1', errors='ignore')
                    st.download_button("📥 Baixar PDF", data=pdf_bytes, file_name=f"Relatorio_{mes_atual.replace('/','_')}.pdf")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
            else:
                st.warning("Sem dados para este mês.")

    # --- ABA PETS (Milo & Bolt) ---
    elif "🐾" in aba:
        st.title("🐾 Cantinho do Milo & Bolt")
        df_pets = df_base[df_base['Categoria'].str.contains('Pet', case=False, na=False)]
        if not df_pets.empty:
            st.metric("Gasto Total com Pets", m_fmt(df_pets['V_Num'].sum()))
            st.dataframe(df_pets[['Vencimento', 'Descrição', 'Valor', 'Categoria']].iloc[::-1], use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum lançamento para os pets encontrado.")
            
    # --- ABA PENDÊNCIAS ---
    elif "Pendências" in aba:
        st.title("⏳ Contas Pendentes")
        df_pend = df_base[df_base['Status'] == 'Pendente']
        if not df_pend.empty:
            st.warning(f"Você tem {len(df_pend)} lançamentos pendentes.")
            st.metric("Total Pendente", m_fmt(df_pend['V_Num'].sum()))
            st.dataframe(df_pend[['Vencimento', 'Descrição', 'Valor', 'Banco']].sort_values('DT'), use_container_width=True, hide_index=True)
        else:
            st.success("Tudo pago! Nenhuma pendência encontrada.")


    

# PODE MANDAR O BLOCO 2 (Pendências, Pets, Relatório, etc)
