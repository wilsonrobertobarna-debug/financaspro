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
st.caption("Versão 2.0.4")

# 1. CONFIGURAÇÃO
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")

# ESTILO PARA VALORES E RÓTULOS (VISUAL LIMPO)
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

if 'df_base' not in st.session_state: atualizar_sessao()

def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

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

# BLOCOS DE LANÇAMENTO NA SIDEBAR
with st.sidebar.expander("🚀 Novo Lançamento", expanded=False):
    with st.form("f_novo", clear_on_submit=True):
        f_compra = st.date_input("🛍️ Data da Compra", value=hoje_br, format="DD/MM/YYYY")
        f_dat = st.date_input("Vencimento", hoje_br, format="DD/MM/YYYY")
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
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

with st.sidebar.expander("💸 Transferência", expanded=False):
    with st.form("f_transf", clear_on_submit=True):
        t_dat = st.date_input("Data", hoje_br, format="DD/MM/YYYY")
        t_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        t_orig = st.selectbox("Origem (Sai):", bancos_disponiveis)
        t_dest = st.selectbox("Destino (Entra):", bancos_disponiveis)
        if st.form_submit_button("TRANSFERIR"):
            if t_orig == t_dest: st.error("Bancos iguais!")
            else:
                v_s = f"{t_val:.2f}".replace('.', ','); d_s = t_dat.strftime("%d/%m/%Y")
                ws_base.append_row([d_s, v_s, "Transferência Saída", "Transferência", "Despesa", t_orig, "Pago", ""])
                ws_base.append_row([d_s, v_s, "Transferência Entrada", "Transferência", "Receita", t_dest, "Pago", ""])
                atualizar_sessao(); st.rerun()

with st.sidebar.expander("⚙️ Ajustar / Excluir Lançamento", expanded=False):
    if not df_base.empty:
        # Mostra os últimos 40 lançamentos para facilitar a busca
        lista = {f"ID {r['ID']} | {r['Vencimento']} | R$ {r['V_Num']:.2f} | {r['Descrição']}": r for _, r in df_base.tail(40).iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione o lançamento:", [""] + list(lista.keys()))
        
        if escolha:
            item = lista[escolha]
            
            # Campos para edição
            with st.container():
                # Converte a data string para objeto date do python
                dt_atual = pd.to_datetime(item['Vencimento'], dayfirst=True)
                
                ed_dat = st.date_input("Alterar Vencimento:", value=dt_atual, format="DD/MM/YYYY")
                ed_des = st.text_input("Alterar Descrição:", value=item['Descrição'])
                ed_val = st.number_input("Alterar Valor:", value=float(item['V_Num']), step=0.01, format="%.2f")
                
                # Busca o índice do banco atual na lista para já vir selecionado
                try:
                    idx_banco = bancos_disponiveis.index(item['Banco'])
                except:
                    idx_banco = 0
                ed_bnc = st.selectbox("Alterar Banco:", bancos_disponiveis, index=idx_banco)
                
                # Seleção de Status
                st_idx = 0 if item['Status'] == "Pago" else 1
                ed_sta = st.selectbox("Alterar Status:", ["Pago", "Pendente"], index=st_idx)
                
                col_ed1, col_ed2 = st.columns(2)
                
                if col_ed1.button("💾 ATUALIZAR TUDO"):
                    v_str = f"{ed_val:.2f}".replace('.', ',')
                    d_str = ed_dat.strftime("%d/%m/%Y")
                    linha = int(item['ID'])
                    
                    # Atualiza cada célula na planilha (Colunas: 1=Data, 2=Valor, 3=Desc, 6=Banco, 7=Status)
                    ws_base.update_cell(linha, 1, d_s)
                    ws_base.update_cell(linha, 2, v_str)
                    ws_base.update_cell(linha, 3, ed_des)
                    ws_base.update_cell(linha, 6, ed_bnc)
                    ws_base.update_cell(linha, 7, ed_sta)
                    
                    st.success("Lançamento atualizado!")
                    atualizar_sessao()
                    st.rerun()
                
                if col_ed2.button("🚨 EXCLUIR"):
                    ws_base.delete_rows(int(item['ID']))
                    st.warning("Lançamento excluído!")
                    atualizar_sessao()
                    st.rerun()

# 5. TELAS PRINCIPAIS
if "💰" in aba:
    st.title("🛡️ FinançasPro Wilson")
    if not df_base.empty:
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_pago = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
        
        receita = df_m_pago[df_m_pago['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        despesa = df_m_pago[df_m_pago['Tipo'] == 'Despesa']['V_Num'].sum()
        
        st.info(f"### 🏦 SALDO DO MÊS: {m_fmt(receita - despesa)}")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receitas", m_fmt(receita))
        m2.metric("📉 Gastos", m_fmt(despesa))
        m3.metric("⏳ Pendente", m_fmt(df_base[(df_base['Status'] == 'Pendente')]['V_Num'].sum()))
        
        st.divider()
        st.subheader("🔍 Histórico de Lançamentos")
        st.dataframe(df_base.iloc[::-1], use_container_width=True, hide_index=True)

elif "Pendências" in aba:
    st.title("📋 Lançamentos Pendentes")
    df_p = df_base[df_base['Status'] == 'Pendente'].copy()
    if not df_p.empty:
        df_p['Dias'] = (df_p['DT'] - pd.to_datetime(hoje_br)).dt.days
        for _, r in df_p.iterrows():
            cor = "🚨" if r['Dias'] <= 1 else "⚠️"
            st.warning(f"{cor} **{r['Vencimento']}** - {r['Descrição']} ({m_fmt(r['V_Num'])})")
    else:
        st.success("Tudo em dia!")
        
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
    
    for b in sorted(bancos_disponiveis):
        valor_b = 0.0      
        tipo_c = ""
        dia_venc_e = 10   
        
        if not df_bancos_info.empty:
            for _, row in df_bancos_info.iterrows():
                if str(row.iloc[0]).strip().upper() == str(b).strip().upper():
                    try:
                        v_raw = str(row.iloc[1]).replace('R$', '').replace('.', '').replace(',', '.').strip()
                        valor_b = float(v_raw) if v_raw and v_raw != 'nan' else 0.0
                        tipo_c = str(row.iloc[2]).strip().upper()
                        if len(row) >= 5:
                            ven_raw = str(row.iloc[4]).replace('R$', '').strip()
                            dia_venc_e = int(float(ven_raw)) if ven_raw and ven_raw != 'nan' else 10
                    except: pass
                    break
        
        if "CARTA" in tipo_c or "CART" in b.upper():
            limite_cartao = valor_b
            df_cart_base = df_base[(df_base['Banco'] == b) & 
                                   (df_base['Tipo'].str.upper() == 'DESPESA') & 
                                   (df_base['Status'].str.upper() == 'PENDENTE')].copy()
            df_cart_base['DT_ONLY'] = pd.to_datetime(df_cart_base['DT']).dt.date
            usado = df_cart_base[df_cart_base['DT_ONLY'] <= d_fim]['V_Num'].sum()
            dispo = limite_cartao - usado
            saldos_txt += f"💳 {b}: Limite: {m_fmt(limite_cartao)} | Usado: {m_fmt(usado)} | Disp: {m_fmt(dispo)} (Venc: {dia_venc_e})\n"
        else:
            saldo_inicial = valor_b
            mov_paga = df_base[(df_base['Banco'] == b) & (df_base['Status'].str.upper() == 'PAGO')]
            rec_b = mov_paga[mov_paga['Tipo'].str.upper().str.contains('RECEITA|REND', na=False)]['V_Num'].sum()
            des_b = mov_paga[mov_paga['Tipo'].str.upper() == 'DESPESA']['V_Num'].sum()
            s_final = saldo_inicial + rec_b - des_b
            icone = "💰" if "INVEST" in tipo_c else "🏦"
            saldos_txt += f"{icone} {b}: Saldo: {m_fmt(s_final)}\n"
            total_patrimonio += s_final

    df_base['DT_ONLY'] = pd.to_datetime(df_base['DT']).dt.date
    df_per = df_base[(df_base['DT_ONLY'] >= d_ini) & (df_base['DT_ONLY'] <= d_fim)].copy()

    if not df_per.empty:
        df_per['T_UP'] = df_per['Tipo'].astype(str).str.upper().str.strip()
        df_per['C_UP'] = df_per['Categoria'].astype(str).str.upper().str.strip()
        mask_rend = (df_per['T_UP'].str.contains('REND', na=False)) | (df_per['C_UP'].str.contains('REND', na=False))
        rend_v = df_per[mask_rend & (df_per['Status'] == 'Pago')]['V_Num'].sum()
        rec_v = df_per[(df_per['T_UP'] == 'RECEITA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        des_v = df_per[(df_per['T_UP'] == 'DESPESA') & (df_per['Status'] == 'Pago') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
        sobra = rec_v - des_v
    else:
        rec_v = des_v = rend_v = sobra = 0.0

    relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
    relat += f"========================================\n"
    relat += f"REC: {m_fmt(rec_v)} | REND: {m_fmt(rend_v)} (Info)\n"
    relat += f"DES: {m_fmt(des_v)} | SOBRA: {m_fmt(sobra)}\n"
    relat += f"========================================\n\n"
    relat += f"SALDOS:\n{saldos_txt}\nTOTAL PATRIMÔNIO: {m_fmt(total_patrimonio)}"
    
    st.text_area("Copiar Relatório", relat, height=300)
    st.markdown(f'[📲 Enviar para o WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

elif "Relatório PDF" in aba:
    st.title("📋 Gerar Relatório Mensal (PDF)")
    st.write("Clique no botão abaixo para gerar o PDF dos lançamentos do mês atual.")

    if not df_base.empty:
        # Filtra os dados do mês atual para o PDF
        df_pdf = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        
        if st.button("Gerar PDF"):
            try:
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", "B", 16)
                pdf.cell(190, 10, f"RELATORIO FINANCEIRO - {mes_atual}", ln=True, align="C")
                pdf.ln(10)

                # Cabeçalho da Tabela
                pdf.set_font("Arial", "B", 10)
                pdf.cell(30, 8, "Vencimento", 1)
                pdf.cell(80, 8, "Descricao", 1)
                pdf.cell(40, 8, "Valor", 1)
                pdf.cell(40, 8, "Status", 1)
                pdf.ln()

                # Linhas da Tabela
                pdf.set_font("Arial", "", 10)
                # Ordenar por data para o relatório ficar bonito
                df_pdf = df_pdf.sort_values(by='DT')
                
                for _, row in df_pdf.iterrows():
                    pdf.cell(30, 7, str(row['Vencimento']), 1)
                    # Corta a descrição se for muito longa para não vazar a tabela
                    desc = str(row['Descrição'])[:35]
                    pdf.cell(80, 7, desc, 1)
                    pdf.cell(40, 7, f"R$ {row['V_Num']:.2f}".replace('.', ','), 1)
                    pdf.cell(40, 7, str(row['Status']), 1)
                    pdf.ln()

                # Gera o arquivo em memória
                pdf_output = pdf.output(dest='S')
                if isinstance(pdf_output, str):
                    pdf_output = pdf_output.encode('latin-1', errors='ignore')
                
                st.download_button(
                    label="📥 Baixar Relatório PDF",
                    data=pdf_output,
                    file_name=f"Relatorio_{mes_atual.replace('/', '_')}.pdf",
                    mime="application/pdf"
                )
                st.success("PDF pronto para baixar!")
            except Exception as e:
                st.error(f"Erro ao gerar o PDF: {e}")
    else:
        st.warning("Não há dados para gerar o relatório.")
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
