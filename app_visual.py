import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from fpdf import FPDF
import urllib.parse

# Definições iniciais de data
agora_br = datetime.now() - timedelta(hours=3)
hoje_br = agora_br.date()

# FUNÇÃO AJUSTADA: Nome correto e acesso global ao 'sh'
def atualizar_meta_sheets(nome):
    global sh 
    novo_valor = st.session_state[f"m_{nome}"]
    
    try:
        ws_meta = sh.worksheet("Meta")
        celula = ws_meta.find(nome)
        
        if celula:
            # 1. A "Paulada": Apaga a memória antiga usando o parâmetro 'nome' correto
            if f"m_{nome}" in st.session_state:
                del st.session_state[f"m_{nome}"]
            
            # 2. Atualiza na planilha
            ws_meta.update_cell(celula.row, 2, novo_valor)
            
            # 3. Força a atualização do DataFrame de controle (para o gráfico ler o valor novo)
            if 'df_metas_config' in st.session_state:
                st.session_state['df_metas_config'].loc[st.session_state['df_metas_config']['Nome da Meta'] == nome, 'Valor Alvo'] = novo_valor
            
            # 4. Recarrega (O toast vai rodar logo após o rerun se você tirar o rerun daqui, 
            # ou você pode usar o toast antes do rerun)
            st.rerun() 
            
    except Exception as e:
        st.error(f"Erro ao salvar no Sheets: {e}")

# 1. CONFIGURAÇÃO INICIAL
st.set_page_config(page_title="FinançasPro Wilson", layout="wide")
st.caption("Versão 2.0.3")

# 2. CONEXÃO (LIGA O MOTOR)
@st.cache_resource
def conectar():
    creds_dict = st.secrets.get("connections", {}).get("gsheets")
    if not creds_dict:
        st.error("⚠️ Wilson, verifique os Secrets!"); st.stop()
    try:
        pk = str(creds_dict["private_key"]).replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_dict["type"], "project_id": creds_dict["project_id"],
            "private_key_id": creds_dict.get("private_key_id"), "private_key": pk,
            "client_email": creds_dict["client_email"], "token_uri": creds_dict["token_uri"],
        }
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]))
    except Exception as e:
        st.error(f"Erro na conexão: {e}"); st.stop()

client = conectar()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. BLOCO DE CARREGAMENTO (Sincroniza Sheets com Session State)
if 'metas_iniciadas' not in st.session_state:
    # Esta linha abaixo está recuada (indentada) para dentro do IF
    try:
        df_metas = pd.DataFrame(sh.worksheet("Meta").get_all_records())
        for index, row in df_metas.iterrows():
            nome = row['Nome da Meta']
            valor_raw = row['Valor Alvo']
            try:
                valor = float(valor_raw) if str(valor_raw).strip() != '' else 0.0
            except:
                valor = 0.0
            st.session_state[f"m_{nome}"] = valor
        st.session_state['metas_iniciadas'] = True
    except Exception as e:
        st.error(f"Erro na planilha: {e}")
# 4. ESTILIZAÇÃO
st.markdown("""
    <style>
    [data-testid='stMetricLabel'], [data-testid='stMetricValue'] {
        font-size: 1.1rem !important; font-weight: bold !important;
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
    
    # Cria o DataFrame
    df = pd.DataFrame(dados[1:], columns=dados[0])
    
    # Tenta usar o ID que já existe na planilha
    if 'ID' in df.columns:
        # Se a coluna 'ID' existir, ele mantém a da planilha
        pass 
    else:
        # Se a coluna não existir, ele gera o ID sequencial e avisa
        df['ID'] = range(2, len(df) + 2)
        st.warning("Aviso: Coluna 'ID' não encontrada na planilha. ID gerado automaticamente.")
    
    # Processamento de valores
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

# --- RELATÓRIO BANCÁRIO (OCULTO NA TELA INICIAL) ---
with st.expander("📊 Clique aqui para ver o Relatório Bancário Completo"):
    df = carregar_dados_gs()
    df_bancos = carregar_bancos_manual_gs()
    
    # 1. Ajuste de Datas
    df['DT'] = pd.to_datetime(df['DT'], errors='coerce')
    hoje = pd.Timestamp.today().normalize()
    
    # 2. Garantir que V_Num seja numérico
    df['V_Num'] = pd.to_numeric(df['V_Num'], errors='coerce').fillna(0)
    
    if not df_bancos.empty:
        qtd_colunas = 4
        
        def formatar_moeda(valor):
            try:
                return f"R$ {float(valor):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            except:
                return "R$ 0,00"

        for i in range(0, len(df_bancos), qtd_colunas):
            cols = st.columns(qtd_colunas)
            linha = df_bancos.iloc[i:i + qtd_colunas]
            
            for j, (index, row) in enumerate(linha.iterrows()):
                with cols[j]:
                    nome_banco = row['Nome do Banco']
                    saldo_inicial = float(str(row['Saldo Inicial']).replace('.', '').replace(',', '.'))
                    
                    # 3. Filtrar transações deste banco até hoje
                    filtro = (df['Banco'] == nome_banco) & (df['DT'] <= hoje)
                    df_banco_atual = df[filtro]
                    
                    # 4. Cálculo inteligente: 
                    # Soma tudo se for 'Receita' ou 'Transferência' (entrada)
                    # Subtrai se for 'Despesa'
                    # Verifique na sua planilha se o nome na coluna 'Tipo' é exatamente 'Despesa'
                    entradas = df_banco_atual[df_banco_atual['Tipo'] != 'Despesa']['V_Num'].sum()
                    saidas = df_banco_atual[df_banco_atual['Tipo'] == 'Despesa']['V_Num'].sum()
                    
                    saldo_atual = saldo_inicial + entradas - saidas
                    
                    st.metric(label=nome_banco, value=formatar_moeda(saldo_atual))
# INICIALIZA O CACHE NA SESSÃO
if 'df_base' not in st.session_state:
    st.session_state['df_base'] = carregar_dados_gs()
if 'df_bancos_info' not in st.session_state:
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

# 2. Agora criamos as variáveis locais para usar nas barras
df_base = st.session_state['df_base']
df_bancos_info = st.session_state['df_bancos_info']

# FUNÇÃO PARA ATUALIZAR O ESTADO
def atualizar_sessao():
    st.session_state['df_base'] = carregar_dados_gs()
    st.session_state['df_bancos_info'] = carregar_bancos_manual_gs()

# A "MÉCÂNICA" DE SEGURANÇA:
# Se o programa acabou de abrir e não tem nada na memória, ele carrega.
# Se já tem algo na memória (mesmo que você tenha fechado e aberto), 
# ele NÃO limpa, ele mantém o que está lá até que você aperte o botão de atualizar.
if 'df_base' not in st.session_state:
    atualizar_sessao()

# Agora, as variáveis sempre terão o conteúdo que foi carregado
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

aba = st.sidebar.radio("Navegação:", ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF", "📊 Análises & Configurações"])

st.sidebar.divider()

# BARRINHA 1: NOVO LANÇAMENTO
# Inicializa a variável de estado para controlar a abertura se ela não existir
if "expander_lancamento_aberto" not in st.session_state:
    st.session_state.expander_lancamento_aberto = False

with st.sidebar.expander("🚀 Novo Lançamento", expanded=st.session_state.expander_lancamento_aberto):
    with st.form("f_novo", clear_on_submit=True):
        # Usando a variável hoje_br que já corrige o fuso horário
        f_compra = st.date_input("🛍️ Data da Compra", value=hoje_br, format="DD/MM/YYYY")
        t_dat = st.date_input("Vencimento", datetime.now(), format="DD/MM/YYYY")
        
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
        f_par = st.number_input("Parcelas", min_value=1, value=1)
        f_des = st.text_input("Descrição / Beneficiário")
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água","Assinatura","Rendimento","Aplicação","Restaurante","Celular","Anuidade","Seguro", "Internet","Vestuário","Salário","Reembolso","Moradia", "Saúde","Taxas","Depósito","Plano Assistencial","Transporte","Previdência","Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        # Garante que a variável exista para evitar o NameError
        f_venc_cartao = None 

        # ... (após todos os st.selectbox e inputs do formulário)

        if st.form_submit_button("Salvar Lançamento"):
            # 1. Formatações necessárias
            v_str = f"{f_val:.2f}".replace('.', ',')
            t_dat_str = t_dat.strftime("%d/%m/%Y")
            f_compra_str = f_compra.strftime("%d/%m/%Y")
            
            # 2. Loop usando 't_dat' (a variável correta do seu formulário)
            for i in range(f_par):
                nova_data = t_dat + relativedelta(months=i)
                
                ws_base.append_row([
                    nova_data.strftime("%d/%m/%Y"), # Coluna A: Vencimento
                    v_str,                          # Coluna B: Valor
                    f_des,                          # Coluna C: Descrição
                    f_cat,                          # Coluna D: Categoria
                    f_tip,                          # Coluna E: Tipo
                    f_bnc,                          # Coluna F: Banco
                    f_sta,                          # Coluna G: Status
                    f_compra_str                    # Coluna H: Data da Compra
                ])
            
            # 3. Finalização
            st.toast("✅ Lançamento salvo com sucesso!", icon="💰")
            atualizar_sessao()
            st.rerun()

# Se o usuário mudar de aba ou clicar em outra coisa fora do formulário, o expander fecha amigavelmente
if aba != "💰 Finanças & Bancos":
    st.session_state.expander_lancamento_aberto = False
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
                
# 1. PRIMEIRO: A MÁQUINA (Declare os valores no topo para o Python não se perder)
receita_total = 7626.23  # Exemplo do seu valor real
gasto_total = 3434.45
rendimento = 0.19
pendente = 6932.67
# 5. TELAS PRINCIPAIS
if "💰" in aba:
    # 1. ESTILO (CSS) - Isso aqui "puxa" tudo para cima antes de desenhar o título
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 0rem; /* Zera o espaço no topo */
                    padding-bottom: 0rem;
                }
        </style>
        """, unsafe_allow_html=True)
    
    st.subheader("🛡️ FinançasPro Wilson")
    # --- COLE AQUI (INÍCIO DA BARRINHA) ---
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    
    # Isso cria a barra horizontal de meses
    st.pills("Período:", meses, selection_mode="single", default="Mai")

    # --- 1. O SALDO GERAL (REI DA TELA) ---
    # Usamos uma fonte maior e centralizada para ele ser "mais notado"
    saldo_geral = receita_total - gasto_total
    cor_saldo = "#2ecc71" if saldo_geral >= 0 else "#e74c3c" # Verde se positivo, Vermelho se negativo
    
    st.markdown(f"""
        <div style="text-align: center; background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid {cor_saldo};">
            <p style="margin: 0; font-size: 1rem; color: #666; font-weight: bold;">SALDO DISPONÍVEL</p>
            <h1 style="margin: 0; color: {cor_saldo}; font-size: 2.5rem;">R$ {saldo_geral:,.2f}</h1>
        </div>
    """.replace(",", "X").replace(".", ",").replace("X", "."), unsafe_allow_html=True)

    st.write("") # Espaço de respiro

    # --- 2. OS CARDS DE APOIO (MENORES) ---
    # Aqui os valores ficam organizados em colunas, ocupando menos espaço vertical
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("📈 Receita", f"R$ {receita_total:,.2f}")
    with c2:
        st.metric("📉 Gasto", f"R$ {gasto_total:,.2f}")
    with c3:
        st.metric("💰 Rendimento", f"R$ {rendimento:,.2f}")
    with c4:
        st.metric("⏳ Pendente", f"R$ {pendente:,.2f}")
# ----------------------------------------------

if "💰" in aba:
    # ... seu código do CSS e Título ...
    
    saldo_geral = receita_total - gasto_total # Agora ele não trava mais!

    

    st.divider()

    g1, g2 = st.columns(2)
    with g1:
        st.write("### 🍕 Gastos por Categoria")
        # Colocando o '#' para ignorar o erro de dados por enquanto:
        # df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
        # if not df_p.empty: 
        #     st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', title="✨ Gastos por Categoria (%)", hole=0.4), use_container_width=True, config={'staticPlot': True})
        st.info("Aguardando conexão com os dados...")

    with g2:
        st.write("### 📊 Fluxo de Caixa")
        # Fazendo o mesmo aqui para o fluxo:
        # df_f = df_base[(df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')].copy()
        # df_f = df_f.sort_values('DT')
        # df_f_grouped = df_f.groupby(['Mes_Ano', 'Tipo'], sort=False)['V_Num'].sum().reset_index()
        # if not df_f_grouped.empty: 
        #     st.plotly_chart(px.bar(df_f_grouped, x='Mes_Ano', y='V_Num', color='Tipo', barmode='group', color_discrete_map={'Receita':'#2ecc71','Despesa':'#e74c3c','Rendimento':'#27ae60'}, title="📊 Fluxo de Caixa Mensal"), use_container_width=True, config={'staticPlot': True})
        st.info("Aguardando conexão com os dados...")
       
    if not df_base.empty:
        # AQUI VOCÊ CRIA A VARIÁVEL
        df_m = df_base[df_base['Mes_Ano'] == mes_atual].copy()
        df_m_limpo = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
        
        # Cálculo do saldo
        saldo_geral = df_m_limpo[df_m_limpo['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum() - df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        st.info(f"### 🏦 SALDO GERAL ATUAL: {m_fmt(saldo_geral)}")
        
        st.divider()

        # --- RESUMO DOS MESES (DENTRO DO MESMO BLOCO) ---
        with st.expander("📊 RESUMO DOS MESES", expanded=False):
            m1, m2, m3 = st.columns(3)
            # Agora o m1 vai encontrar o df_m_limpo porque estão no mesmo "quarto"
            m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
            m2.metric("📉 Despesa", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
            m3.metric("⚖️ Balanço", m_fmt(saldo_geral))

        # --- INDICADORES DO MÊS ---
               
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("📈 Receita", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()))
        m2.metric("📉 Gasto", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()))
        m3.metric("💰 Rendimento", m_fmt(df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()))
        m4.metric("⏳ Pendente", m_fmt(get_valor_pendente(df_base)))
              
      
               
    if 'df_m_limpo' in locals() or 'df_m_limpo' in globals():
    
        # Só faz a conta se a variável existir
        if df_m_limpo is not None and not df_m_limpo.empty:
        
            st.subheader("🎯 Metas vs Realizado")
            df_metas_graph = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            
        if not df_metas_graph.empty:
            # 1. GARANTIR QUE A COLUNA META EXISTE
            if 'Meta' not in df_metas_graph.columns:
                df_metas_graph['Meta'] = 0.0
            
            # 2. PREENCHER COM A LÓGICA DO SESSION_STATE
            def buscar_meta(cat):
                return st.session_state.get(f"m_{cat}", 0.0)
            
            df_metas_graph['Meta'] = df_metas_graph['Categoria'].apply(buscar_meta)

            # 3. AGORA SIM, DESENHA O GRÁFICO
            # Coloque isso logo antes da linha: fig_m = go.Figure()
            st.write("Dados no session_state para Mercado:", st.session_state.get("m_Mercado", "NÃO ENCONTRADO"))
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Real', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta', marker_color='#2ecc71', opacity=0.4))
            
            fig_m.update_layout(barmode='group', height=350)
            st.plotly_chart(fig_m, use_container_width=True, config={'staticPlot': True})
            st.divider()
        else:
            # Este else pertence ao 'if not df_metas_graph.empty'
            st.info("Nenhuma despesa encontrada para esta categoria.")
        
        # O resto do código continua aqui fora, alinhado com o 'if' principal
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
    
    # 1. Filtros
    col_b, col_d = st.columns(2)
    with col_b:
        filtro_banco = st.multiselect("Filtrar Banco/Cartão:", df_base['Banco'].unique(), key="banco_pend")
    with col_d:
        busca_desc = st.text_input("Buscar Descrição:", key="desc_pend")

    periodo = st.date_input("Filtrar por Período:", (hoje.replace(day=1), hoje + timedelta(days=30)), key="data_pend")

   # 2. Processamento e Filtros (Ordem Correta)
    df_filtrado = df_base.copy()
    
    # 1. Filtro de Status (garante que apenas Pendentes apareçam)
    df_filtrado['Status_Limpo'] = df_filtrado['Status'].astype(str).str.strip().str.lower()
    df_filtrado = df_filtrado[df_filtrado['Status_Limpo'] == 'pendente'].copy()
    
    # 2. Filtro de Banco (se selecionado, filtra agora)
    if filtro_banco:
        df_filtrado = df_filtrado[df_filtrado['Banco'].isin(filtro_banco)]
        
    # 3. Conversão de Data e Filtro de Período
    col_data = 'Vencimento' 
    if col_data in df_filtrado.columns:
        df_filtrado['Data_Formatada'] = pd.to_datetime(df_filtrado[col_data], errors='coerce')
        
        # Filtra o período se uma tupla válida for selecionada
        if isinstance(periodo, tuple) and len(periodo) == 2:
            df_filtrado = df_filtrado[
                (df_filtrado['Data_Formatada'].dt.date >= periodo[0]) & 
                (df_filtrado['Data_Formatada'].dt.date <= periodo[1])
            ]
            
    # 4. Filtro de Descrição (Por último, para refinar)
    if busca_desc:
        df_filtrado = df_filtrado[df_filtrado['Descrição'].str.contains(busca_desc, case=False, na=False)]
    
    st.write(f"### Lançamentos Encontrados: {len(df_filtrado)}")    
    colunas_visiveis = ['Vencimento', 'Banco', 'Descrição', 'Valor']
    cols_existentes = [c for c in colunas_visiveis if c in df_filtrado.columns]
    
    # Exibe a tabela
    st.dataframe(df_filtrado[cols_existentes], use_container_width=True, hide_index=True)

    # 4. Botão de Baixa (Funcionalidade de Baixa)
    if not df_filtrado.empty:
        nova_data = st.date_input("Data de pagamento para baixa:", datetime.now(), key="data_baixa_pend")
        if st.button("✅ BAIXAR SELECIONADOS", key="btn_baixa_final"):
            sucessos = 0
            headers = ws_base.row_values(1)
            idx_status = headers.index('Status') + 1
            # Ajuste dinâmico para a coluna de Vencimento/Data
            idx_venc = [i for i, h in enumerate(headers) if 'VENC' in h.upper() or 'DATA' in h.upper()][0] + 1
            
            for idx_df, row in df_filtrado.iterrows():
                linha_sheets = int(idx_df) + 2
                ws_base.update_cell(linha_sheets, idx_status, "Pago")
                ws_base.update_cell(linha_sheets, idx_venc, nova_data.strftime("%d/%m/%Y"))
                sucessos += 1
            
            st.toast(f"✅ {sucessos} itens baixados!", icon="💰")
            atualizar_sessao()
            st.rerun()
    else:
        st.info("Nenhum lançamento encontrado neste período.")
    st.divider()
    st.subheader("🔔 Avisos: Vencimentos Próximos")
       # ... (aqui você mantém a lógica original dos alertas de vencimento se desejar) ...
        
    
    c1, c2, c3 = st.columns(3) # Aumentei para 3 colunas para caber o filtro de data
    s_bnc = c1.multiselect("Filtrar Banco/Cartão:", sorted(bancos_disponiveis))
    b_desc = c2.text_input("Buscar Descrição:", key="busca_desc_pendencias")
    periodo = c3.date_input("Período:", (datetime.now().replace(day=1), datetime.now())) # Filtro de data novo

    df_v = df_base[df_base['Status'] == 'Pendente'].copy()
    
    # Garantir que a coluna de data esteja no formato correto para o filtro
    df_v['DT_Obj'] = pd.to_datetime(df_v['DT'], errors='coerce') 
    
    if s_bnc:
        df_v = df_v[df_v['Banco'].isin(s_bnc)]
    if b_desc:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
    
    # Aplicação do filtro de data
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_v = df_v[(df_v['DT_Obj'].dt.date >= periodo[0]) & (df_v['DT_Obj'].dt.date <= periodo[1])]
        
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

if aba == "📋 Relatório PDF":
    st.markdown("### 📋 Emissão de Relatório Financeiro")
    
    # -------------------------------------------------------------------------
    # LINHA 1 DE FILTROS: BANCO E PERÍODO (Estrutura original mantida intacta)
    # -------------------------------------------------------------------------
    col_rel1, col_rel2 = st.columns(2)
    with col_rel1:
        opcoes_banco_rel = ["Todos"] + list(bancos_disponiveis)
        banco_relatorio = st.selectbox("Filtrar Banco:", opcoes_banco_rel)
        
    with col_rel2:
        data_padrao_ini = datetime(2026, 4, 20)
        data_padrao_fim = datetime(2026, 5, 20)
        periodo_pdf = st.date_input("Período do Relatório:", [data_padrao_ini, data_padrao_fim], format="DD/MM/YYYY")

    # -------------------------------------------------------------------------
    # LINHA 2 DE FILTROS: DESCRIÇÃO E STATUS 
    # -------------------------------------------------------------------------
    col_rel3, col_rel4 = st.columns(2)
    with col_rel3:
        busca_desc = st.text_input("🔍 Pesquisar por Descrição / Beneficiário:", "").strip()
        
    with col_rel4:
        busca_status = st.selectbox("📌 Filtrar Status:", ["Todos", "Pago", "Pendente"])

    st.markdown("---")

    # Botão para processar e gerar o documento
    if st.button("📄 Gerar PDF"):
        try:
            if isinstance(periodo_pdf, (list, tuple)):
                if len(periodo_pdf) == 2:
                    b_ini, b_fim = periodo_pdf[0], periodo_pdf[1]
                else:
                    b_ini = b_fim = periodo_pdf[0]
            else:
                b_ini = b_fim = periodo_pdf

            # ========================================================
            # 1. INICIALIZAÇÃO DO PDF
            # ========================================================
            from fpdf import FPDF
            pdf = FPDF()
            pdf.add_page()

            # ========================================================
            # 2. CAPTURA E FILTRAGEM COMPLETA DOS DADOS (PDF)
            # ========================================================
            df_report = df_base.copy()

            col_banco_df = next((c for c in df_report.columns if c.upper() in ['BANCO', 'CONTA']), None)
            col_data_df = next((c for c in df_report.columns if c.upper() in ['VENCIMENTO', 'DATA', 'DT']), None)
            col_desc_df = next((c for c in df_report.columns if c.upper() in ['DESCRIÇÃO', 'DESCRICAO', 'NOTA']), None)
            col_status_df = next((c for c in df_report.columns if c.upper() in ['STATUS']), None)

            # Tratamento e filtro de Data
            if col_data_df:
                df_report['DT_FILTRO'] = pd.to_datetime(df_report[col_data_df], format="%d/%m/%Y", errors='coerce')
            else:
                df_report['DT_FILTRO'] = pd.to_datetime(df_report.index, errors='coerce')

            t_ini = pd.to_datetime(b_ini)
            t_fim = pd.to_datetime(b_fim)

            # Guardamos uma cópia completa para calcular o saldo retroativo do Banco antes de filtrar o período final
            df_retroativo = df_report.copy()

            # Aplica os filtros na tabela que vai de fato para o PDF
            df_report = df_report[(df_report['DT_FILTRO'] >= t_ini) & (df_report['DT_FILTRO'] <= t_fim)]

            banco_nome = "Todos os Bancos"
            if banco_relatorio != "Todos" and col_banco_df:
                banco_nome = banco_relatorio
                df_report = df_report[df_report[col_banco_df].str.upper().str.strip() == str(banco_nome).upper()]

            if busca_desc and col_desc_df:
                df_report = df_report[df_report[col_desc_df].astype(str).str.contains(busca_desc, case=False, na=False)]

            if busca_status != "Todos" and col_status_df:
                df_report = df_report[df_report[col_status_df].str.upper().str.strip() == str(busca_status).upper()]

            df_report = df_report.sort_values(by='DT_FILTRO')

# ========================================================
            # 3. BUSCA DO SALDO DE ABERTURA - MATEMÁTICA REAL COMBINADA
            # ========================================================
            base_inicial = 0.0
            
            # REGRA 1: Se for Cartão de Crédito, o saldo inicial DEVE vir zerado
            if "CARTAO" in str(banco_nome).upper() or "CARTÃO" in str(banco_nome).upper():
                base_inicial = 0.0
            else:
                # REGRA 2: Banco - Pega o Saldo Inicial do Sistema e aplica as movimentações até o dia 17
                try:
                    # 3.1 Primeiro, buscamos o Saldo Inicial de Cadastro (Aquele de Abril, ex: R$ 17,07)
                    saldo_sistema_abril = 0.0
                    try:
                        ws_bancos = sh.worksheet("Bancos")
                        dados_bancos = ws_bancos.get_all_values()
                        df_bancos_cad = pd.DataFrame(dados_bancos[1:], columns=dados_bancos[0])
                        
                        col_banco_cad = [c for c in df_bancos_cad.columns if 'BANCO' in c.upper()][0]
                        col_saldo_cad = [c for c in df_bancos_cad.columns if 'SALDO' in c.upper()][0]
                        
                        if banco_nome != "Todos os Bancos":
                            linha_banco = df_bancos_cad[df_bancos_cad[col_banco_cad].str.upper().str.strip() == banco_nome.upper()]
                            if not linha_banco.empty:
                                val_cru = str(linha_banco.iloc[0][col_saldo_cad]).strip()
                                import re
                                val_limpo = re.sub(r'[^\d.,-]', '', val_cru)
                                if '.' in val_limpo and ',' in val_limpo:
                                    val_limpo = val_limpo.replace('.', '').replace(',', '.')
                                elif ',' in val_limpo:
                                    val_limpo = val_limpo.replace(',', '.')
                                saldo_sistema_abril = float(val_limpo)
                    except:
                        saldo_sistema_abril = 0.0

                    # 3.2 Agora, calculamos a movimentação que aconteceu desde o começo até o dia 17/05
                    df_historico = df_base.copy()
                    col_data_h = next((c for c in df_historico.columns if c.upper() in ['VENCIMENTO', 'DATA', 'DT']), None)
                    col_banco_h = next((c for c in df_historico.columns if c.upper() in ['BANCO', 'CONTA']), None)
                    
                    if col_data_h:
                        df_historico['DT_HIST'] = pd.to_datetime(df_historico[col_data_h], format="%d/%m/%Y", errors='coerce')
                    else:
                        df_historico['DT_HIST'] = pd.to_datetime(df_historico.index, errors='coerce')
                        
                    if banco_nome != "Todos os Bancos" and col_banco_h:
                        df_historico = df_historico[df_historico[col_banco_h].str.upper().str.strip() == str(banco_nome).upper()]
                    
                    # Filtra tudo o que aconteceu estritamente ANTES do dia de início do relatório (antes do dia 18)
                    df_antes_do_periodo = df_historico[df_historico['DT_HIST'] < t_ini]
                    
                    saldo_acumulado_passado = 0.0
                    for _, r_pass in df_antes_do_periodo.iterrows():
                        val_p_cru = r_pass.get('V_Num', r_pass.get('Valor', 0))
                        
                        if isinstance(val_p_cru, str):
                            import re
                            val_p_limpo = re.sub(r'[^\d.,-]', '', val_p_cru).strip()
                            if '.' in val_p_limpo and ',' in val_p_limpo:
                                val_p_limpo = val_p_limpo.replace('.', '').replace(',', '.')
                            elif ',' in val_p_limpo:
                                val_p_limpo = val_p_limpo.replace(',', '.')
                            val_p = pd.to_numeric(val_p_limpo, errors='coerce')
                        else:
                            val_p = pd.to_numeric(val_p_cru, errors='coerce')
                            
                        if pd.isna(val_p): val_p = 0.0
                        
                        tipo_p = str(r_pass.get('Tipo', '')).upper().strip()
                        if "DESPESA" in tipo_p or "GASTO" in tipo_p:
                            saldo_acumulado_passado -= val_p
                        else:
                            saldo_acumulado_passado += val_p
                    
                    # O saldo inicial real no dia 18 é o saldo base do sistema + as movimentações do passado!
                    base_inicial = saldo_sistema_abril + saldo_acumulado_passado
                except:
                    base_inicial = 0.0

            saldo_anterior = base_inicial

            saldo_anterior = base_inicial            # ========================================================
            # 4. CÁLCULO DOS LANÇAMENTOS E SALDO ACUMULADO
            # ========================================================
            corrente = saldo_anterior 
            saldos_lista = []

            for _, r in df_report.iterrows():
                val = pd.to_numeric(r.get('V_Num', r.get('Valor', 0)), errors='coerce')
                if pd.isna(val): val = 0
                
                tipo_check = str(r.get('Tipo', '')).upper().strip()
                if "DESPESA" in tipo_check or "GASTO" in tipo_check:
                    corrente -= val
                else:
                    corrente += val
                saldos_lista.append(corrente)
            
            df_report['Saldo_Acum'] = saldos_lista

            # ========================================================
            # 5. MONTAGEM DO CABEÇALHO DO PDF (Mantido padrão limpo)
            # ========================================================
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
            pdf.ln(2)
            
            pdf.set_font("Arial", '', 10)
            p_inicio = b_ini.strftime('%d/%m/%Y')
            p_fim = b_fim.strftime('%d/%m/%Y')
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 6, txt=f"BANCO SELECIONADO: {str(banco_nome).upper()}", ln=1, align="L")
            pdf.cell(200, 6, txt=f"PERIODO DO RELATORIO: {p_inicio} ate {p_fim}", ln=1, align="L")
            
            txt_saldo_ini = f"R$ {saldo_anterior:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            pdf.cell(200, 6, txt=f"SALDO ANTERIOR / ABERTURA: {txt_saldo_ini}", ln=1, align="L")
            pdf.ln(5)

            # Cabeçalho da Tabela
            pdf.set_font("Arial", 'B', 9)
            pdf.cell(20, 7, "Data", 1)
            pdf.cell(18, 7, "Tipo", 1)
            pdf.cell(35, 7, "Categoria", 1)
            pdf.cell(45, 7, "Descricao", 1)
            pdf.cell(25, 7, "Valor", 1)
            pdf.cell(32, 7, "Saldo Acum.", 1)
            pdf.cell(20, 7, "Status", 1)
            pdf.ln()

            # ========================================================
            # 6. LOOP DE IMPRESSÃO DAS LINHAS NO PDF
            # ========================================================
            pdf.set_font("Arial", '', 9)
            for index, row in df_report.iterrows():
                data_str = row['DT_FILTRO'].strftime('%d/%m/%Y') if not pd.isna(row['DT_FILTRO']) else str(row.get(col_data_df, '---'))
                
                tipo_str = str(row.get('Tipo', '---')).strip()
                cat_val = str(row.get('Categoria', 'Geral'))[:18]
                desc_val = str(row.get('Descrição', row.get('Descricao', 'Sem nome')))[:24]
                valor_val = pd.to_numeric(row.get('V_Num', row.get('Valor', 0)), errors='coerce')
                if pd.isna(valor_val): valor_val = 0.0
                saldo_val = row.get('Saldo_Acum', 0.0)
                status_val = str(row.get('Status', '-'))

                if "DESPESA" in tipo_str.upper() or "GASTO" in tipo_str.upper():
                    texto_valor = f"- R$ {valor_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (255, 0, 0)
                else:
                    texto_valor = f"R$ {valor_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (0, 0, 0)

                texto_saldo = f"R$ {saldo_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                cor_saldo = (255, 0, 0) if saldo_val < 0 else (0, 0, 0)

                pdf.cell(20, 6, data_str, 1)
                pdf.cell(18, 6, tipo_str, 1)
                pdf.cell(35, 6, cat_val, 1)
                pdf.cell(45, 6, desc_val, 1)
                
                pdf.set_text_color(*cor_valor)
                pdf.cell(25, 6, texto_valor, 1)
                
                pdf.set_text_color(*cor_saldo)
                pdf.cell(32, 6, texto_saldo, 1)
                
                pdf.set_text_color(0, 0, 0)
                pdf.cell(20, 6, status_val, 1)
                pdf.ln()

            pdf_output = pdf.output(dest='S')
            if isinstance(pdf_output, str):
                pdf_output = pdf_output.encode('latin-1')
                
            st.download_button(
                label="📥 Baixar PDF",
                data=pdf_output,
                file_name="relatorio_financaspro.pdf",
                mime="application/pdf"
            )
            st.success(f"PDF pronto! Relatório atualizado.")

        except Exception as e:
            st.error(f"Erro ao gerar o PDF: {e}")

    # =========================================================================
    # 7. EXIBIÇÃO DA TABELA NA TELA COM OS MESMOS 4 FILTROS (VISUAL LIMPO)
    # =========================================================================
    st.markdown("### 🔍 Lançamentos Filtrados")

    df_tela = df_base.copy()
    
    col_data_df = next((c for c in df_tela.columns if c.upper() in ['VENCIMENTO', 'DATA', 'DT']), None)
    col_banco_df = next((c for c in df_tela.columns if c.upper() in ['BANCO', 'CONTA']), None)
    col_desc_df = next((c for c in df_tela.columns if c.upper() in ['DESCRIÇÃO', 'DESCRICAO', 'NOTA']), None)
    col_status_df = next((c for c in df_tela.columns if c.upper() in ['STATUS']), None)

    # Aplica Data na tela
    if col_data_df:
        df_tela['DT_FILTRO'] = pd.to_datetime(df_tela[col_data_df], format="%d/%m/%Y", errors='coerce')
        if isinstance(periodo_pdf, (list, tuple)) and len(periodo_pdf) == 2:
            df_tela = df_tela[(df_tela['DT_FILTRO'] >= pd.to_datetime(periodo_pdf[0])) & 
                               (df_tela['DT_FILTRO'] <= pd.to_datetime(periodo_pdf[1]))]

    # Aplica Banco na tela
    if banco_relatorio != "Todos" and col_banco_df:
        df_tela = df_tela[df_tela[col_banco_df].str.upper().str.strip() == str(banco_relatorio).upper()]

    # Aplica Descrição na tela
    if busca_desc and col_desc_df:
        df_tela = df_tela[df_tela[col_desc_df].astype(str).str.contains(busca_desc, case=False, na=False)]

    # Aplica Status na tela
    if busca_status != "Todos" and col_status_df:
        df_tela = df_tela[df_tela[col_status_df].str.upper().str.strip() == str(busca_status).upper()]

    # Faxina das colunas internas para manter o visual limpo
    colunas_para_esconder = ['ID', 'V_Num', 'DT', 'DT_FILTRO', 'mesA', 'MESA', 'id', 'vnum', 'dt', 'mesa']
    colunas_visiveis = [c for c in df_tela.columns if c not in colunas_para_esconder]
    df_tela_limpo = df_tela[colunas_visiveis]

    # Exibe os dados
    if not df_tela_limpo.empty:
        st.dataframe(df_tela_limpo, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado para os filtros aplicados.")
# =========================================================================
# NOVA ABA: 📊 ANÁLISES & CONFIGURAÇÕES (Criada no final do arquivo)
# =========================================================================
# ATENÇÃO: Essa linha abaixo tem que começar encostada no canto esquerdo!
if aba == "📊 Análises & Configurações":
    st.markdown("## 📊 Painel de Análises & Configurações")
    
    # 1. GRÁFICO: EVOLUÇÃO DO SALDO ACUMULADO
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

    # 2. COMPARATIVO: MARÇO VS ABRIL
    with st.expander("📊 Comparativo de Sobra Mensal (Março vs. Abril)", expanded=True):
        df_mar = df_base[(df_base['Mes_Ano'] == '03/26') & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')]
        df_abr = df_base[(df_base['Mes_Ano'] == '04/26') & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')]
        
        rec_mar = df_mar[df_mar['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        desp_mar = df_mar[df_mar['Tipo'] == 'Despesa']['V_Num'].sum()
        sobra_mar = rec_mar - desp_mar
        
        rec_abr = df_abr[df_abr['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        desp_abr = df_abr[df_abr['Tipo'] == 'Despesa']['V_Num'].sum()
        sobra_abr = rec_abr - desp_abr
        
        var_valor = sobra_abr - sobra_mar
        var_pct = ((sobra_abr - sobra_mar) / abs(sobra_mar) * 100) if sobra_mar != 0 else 0.0
        
        c_c1, c_c2, c_c3 = st.columns(3)
        c_c1.metric("Sobra de Março", m_fmt(sobra_mar))
        c_c2.metric("Sobra de Abril", m_fmt(sobra_abr))
        c_c3.metric("Variação Líquida", m_fmt(var_valor), delta=f"{var_pct:.1f}%")

    st.divider()

    # 3. DATAFRAME: BANCOS E CARTÕES
    st.subheader("🏦 Informações de Contas e Cartões")
    if not df_bancos_info.empty:
        st.dataframe(df_bancos_info, use_container_width=True, hide_index=True)
    else:
        st.info("ℹ️ Preencha a aba 'Bancos' no Google Sheets para visualizar os dados.")
        
    st.divider()
    
   # 4. FORMULÁRIO: CONFIGURAR METAS
    with st.expander("🎯 Configurar Metas", expanded=False):
        # 1. Garante que os dados estão carregados
        if 'df_metas_config' not in st.session_state:
            try:
                st.session_state['df_metas_config'] = pd.DataFrame(sh.worksheet("Meta").get_all_records())
            except:
                st.session_state['df_metas_config'] = pd.DataFrame(columns=['Nome da Meta', 'Valor Alvo'])
        
        df_metas = st.session_state['df_metas_config']
        cols = st.columns(3) # Cria 3 colunas para os campos não ficarem um embaixo do outro
        
        # 2. Cria os campos de input automaticamente para cada meta da planilha
     
        for index, row in df_metas.iterrows():
            nome = row['Nome da Meta']
            valor_raw = row.get('Valor Alvo', 0)
        
            try:
                if isinstance(valor_raw, str):
                    valor_raw = valor_raw.replace('R$', '').replace('.', '').replace(',', '.')
                valor_alvo = float(valor_raw) if str(valor_raw).strip() != '' else 0.0
            except:
                valor_alvo = 0.0 

            # AQUI ESTÁ A MÁGICA: O input agora está conectado ao 'on_change'
            cols[index % 3].number_input(
                f"Meta: {nome}", 
                value=float(st.session_state.get(f"m_{nome}", valor_alvo)), 
                key=f"m_{nome}",
                on_change=atualizar_meta_sheets, 
                args=(nome,) 
            )
