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
import streamlit.components.v1 as components


# Configuração da página
st.set_page_config(
    page_title="Painel Wilson",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS GLOBAL: Joga para o topo e elimina espaçamentos excessivos de uma vez
st.markdown("""
<style>
    /* Oculta o menu lateral padrão */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Respiro ideal no topo */
    .block-container {
        padding-top: 2.2rem !important;
    }
    
    /* Aproxima bem o menu da linha divisória */
    div.stSelectbox {
        margin-bottom: -1.5rem !important;
    }
    hr {
        margin-top: 0.2rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* CONGELA O TOPO (Painel Wilson, menu e linha) */
    /* Fixa o cabeçalho principal do Streamlit no topo da página */
    header[data-testid="stHeader"] {
        background: transparent;
    }
    
    /* Cria uma barra flutuante fixa com fundo sólido para o seu menu e título */
    .st-emotion-cache-18ni7ap, [data-testid="stVerticalBlock"]:has(> div > div > label:contains("Navegue pelo sistema")) {
        position: sticky;
        top: 0px;
        z-index: 99999;
        background-color: var(--background-color, #0e1117);
        padding-top: 10px;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allow_html=True)

# ========================================================
# 1. TELA DE LOGIN (COMPACTA E CENTRALIZADA)
# ========================================================
if 'login' not in st.session_state:
    st.session_state.login = False

if not st.session_state.login:
    _, col_login, _ = st.columns([1, 1.5, 1])
    
    with col_login:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("### 🔒 Acesso Seguro - Painel Wilson")
        senha = st.text_input("Digite sua senha:", type="password", key="senha_input")
        
        if st.button("🔓 Desbloquear", use_container_width=True):
            if senha == "Wilson123":
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Senha Incorreta.")
                
    st.stop()

# ========================================================
# 2. TOPO DO SISTEMA (FIXO NO TOPO / STICKY)
# ========================================================
# ========================================================
# 2. TOPO DO SISTEMA (FIXO NATIVO NO TOPO)
# ========================================================

st.markdown("""
<style>
    /* Oculta o menu lateral padrão */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Respiro ideal no topo da página */
    .block-container {
        padding-top: 1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# Cria um container fixo nativo para o topo
topo_container = st.container()

with topo_container:
    st.markdown("""
    <style>
        /* Trava o container nativo no topo da tela sem criar riscos pretos */
        [data-testid="stVerticalBlock"]:has(> div > div > label:contains("Navegue pelo sistema")) {
            position: sticky;
            top: 0px;
            z-index: 999999;
            background-color: var(--background-color, #0e1117);
            padding-top: 10px;
            padding-bottom: 5px;
        }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("## 🎮 Painel Wilson")

    if 'page' not in st.session_state:
        st.session_state.page = "💰 Finanças & Bancos"

    menu_itens = [
        "💰 Finanças & Bancos",
        "📋 Pendências",
        "🐾 Milo & Bolt",
        "🚗 Meu Veículo",
        "📄 WhatsApp",
        "📋 Relatório PDF",
        "📊 Análises & Configurações"
    ]

    nova_pagina = st.selectbox("Navegue pelo sistema:", menu_itens, index=menu_itens.index(st.session_state.page))

    if nova_pagina != st.session_state.page:
        st.session_state.page = nova_pagina
        st.rerun()

    st.markdown("---")
# ========================================================
# 3. CONTEÚDO DAS PÁGINAS
# ========================================================
if st.session_state.page == "💰 Finanças & Bancos":
    pass

elif st.session_state.page == "📋 Pendências":
    pass

elif st.session_state.page == "🐾 Milo & Bolt":
    pass

elif st.session_state.page == "🚗 Meu Veículo":
    pass

elif st.session_state.page == "📄 WhatsApp":
    pass

elif st.session_state.page == "📋 Relatório PDF":
    pass

elif st.session_state.page == "📊 Análises & Configurações":
    pass

if not st.session_state.login:
    # Criamos 3 colunas: esquerda e direita são vazias, o centro é a caixa de login
    col1, col_centro, col2 = st.columns([1, 2, 1])
    
    with col_centro:
        st.markdown("<br><br><br>", unsafe_allow_html=True) # Espaçamento superior
        st.markdown("### 🔒 Acesso Seguro")
        senha = st.text_input("Digite sua senha:", type="password")
        
        if st.button("🔓 Desbloquear Sistema"):
            if senha == "Wilson123": # Troque aqui pela sua senha real
                st.session_state.login = True
                st.rerun()
            else:
                st.error("Senha incorreta, Wilson!")
        
        st.markdown("<br><br>", unsafe_allow_html=True)
    
    st.stop() # Bloqueia o carregamento do restante do código abaixo
   

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

st.set_page_config(
    page_title="FinançasPro",
    layout="wide",
    initial_sidebar_state="collapsed" # Isso fará a barra vir fechada por padrão
)

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
    st.cache_data.clear()
    st.rerun()

st.sidebar.divider()

if 'page' not in st.session_state:
    st.session_state.page = "💰 Finanças & Bancos"

menu_itens = [
    #"💰 Finanças & Bancos", 
    #"📋Pendências", 
    #"🐾 Milo & Bolt", 
    # "🚗 Meu Veículo",  <-- Colocando o # aqui dentro, o Python ignora só ele!
    #"📄 WhatsApp", 
    #"📋 Relatório PDF", 
    #"📊 Análises & Configurações"
]
    
for item in menu_itens:
    if st.sidebar.button(item, use_container_width=True):
        st.session_state.page = item
        st.rerun()
 
st.sidebar.divider()
aba = st.session_state.page



# BARRINHA 1: NOVO LANÇAMENTO
if "expander_lancamento_aberto" not in st.session_state:
    st.session_state.expander_lancamento_aberto = False

with st.sidebar.expander("🚀 Novo Lançamento", expanded=st.session_state.expander_lancamento_aberto):
    
    # 1. O Banco fica FORA do formulário para atualizar a tela na mesma hora que você troca
    f_bnc = st.selectbox("Banco", bancos_disponiveis, key="sb_banco_novo_lancamento")
    
    # Um respiro leve para desgrudar o Banco da Data da Compra
    st.markdown("")
    
    # Data da Compra
    f_compra = st.date_input("🛍️ Data da Compra", value=hoje_br, format="DD/MM/YYYY", key="dt_compra_novo_lancamento")
    
    # --- CÁLCULO INTELIGENTE DO VENCIMENTO ---
    vencimento_calculado = hoje_br
    eh_cartao = False
    dia_fech = 0
    dia_venc = 0
    
    if not df_bancos_info.empty and f_bnc:
        try:
            bancos_coluna_0 = df_bancos_info.iloc[:, 0].astype(str).str.strip()
            banco_alvo = str(f_bnc).strip()
            banco_row = df_bancos_info[bancos_coluna_0 == banco_alvo]
            
            if not banco_row.empty:
                tipo_conta = str(banco_row.iloc[0, 2]).strip().lower()
                
                if "cartão" in tipo_conta or "cartao" in tipo_conta:
                    eh_cartao = True
                    dia_fech = int(banco_row.iloc[0, 3])
                    dia_venc = int(banco_row.iloc[0, 4])
                    
                    ano_alvo = f_compra.year
                    mes_alvo = f_compra.month
                    
                    if f_compra.day >= dia_fech:
                        mes_alvo += 1
                        if mes_alvo > 12:
                            mes_alvo = 1
                            ano_alvo += 1
                            
                    import calendar
                    ultimo_dia_mes = calendar.monthrange(ano_alvo, mes_alvo)[1]
                    dia_real_venc = min(dia_venc, ultimo_dia_mes)
                    
                    vencimento_calculado = f_compra.replace(year=ano_alvo, month=mes_alvo, day=dia_real_venc)
        except Exception:
            eh_cartao = False

    # --- EXIBIÇÃO E DEFINIÇÃO DO VENCIMENTO ---
    st.markdown("")
    if eh_cartao:
        st.markdown(f"📅 **Vencimento (Cartão - Fech: {dia_fech} / Venc: {dia_venc}):** `{vencimento_calculado.strftime('%d/%m/%Y')}`")
        t_dat = vencimento_calculado
    else:
        t_dat = st.date_input("📅 Data de Vencimento", value=hoje_br, format="DD/MM/YYYY", key="dt_vencimento_banco_comum")

    # Um respiro antes de entrar no formulário principal
    st.markdown("")

      # 2. Agora entra o formulário com o restante dos campos e o botão Salvar
    with st.form("f_novo", clear_on_submit=True):
        f_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f", key="val_novo_lancamento")
        f_par = st.number_input("Parcelas", min_value=1, value=1, key="par_novo_lancamento")
        f_desc = st.text_input("📝 Descrição", key="desc_novo_lancamento")
        
        # --- BENEFICIÁRIO COM AUTOCOMPLETAR DA COLUNA J ---
        #beneficiarios_unicos = []
        #if not df_base.empty and 'Beneficiário' in df_base.columns:
        #    beneficiarios_unicos = sorted([str(x).strip() for x in df_base['Beneficiário'].dropna().unique() if str(x).strip() != ''])

        # --- BENEFICIÁRIO COM AUTOCOMPLETAR DA COLUNA J (FILTRADO E ÚNICO) ---
        beneficiarios_unicos = []
        if not df_base.empty and 'Beneficiário' in df_base.columns:
            nomes_brutos = df_base['Beneficiário'].dropna().astype(str)
            
            # Dicionário para chavear em minúsculo (evita duplicadas) mas guardar o nome original formatado
            unicos_dict = {}
            for n in nomes_brutos:
                n_limpo = n.strip()
                if n_limpo and n_limpo.lower() != 'nan':
                    chave = n_limpo.lower()
                    if chave not in unicos_dict:
                        unicos_dict[chave] = n_limpo
                        
            beneficiarios_unicos = sorted(list(unicos_dict.values()))
        
        # Cria uma lista onde a primeira opção é vazia/digitar novo, seguida do histórico
        opcoes_beneficiario = [""] + beneficiarios_unicos
        f_bnfc = st.selectbox("👤 Beneficiário (Histórico)", options=opcoes_beneficiario, key="sb_bnfc_novo_lancamento")
        
        # Caso queira digitar um beneficiário totalmente novo que não está na lista
        f_bnfc_novo = st.text_input("Ou digite um novo Beneficiário:", key="bnfc_novo_texto")
        
        # Define qual beneficiário valerá (prioriza o texto livre se preenchido, senão pega o do selectbox)
        beneficiario_final = f_bnfc_novo.strip() if f_bnfc_novo.strip() else f_bnfc
        # ------------------------------------------------
        
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"], key="tip_novo_lancamento")
        
        # Um respiro leve para desgrudar o tipo da categoria
        st.markdown("")
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água","Assinatura","Rendimento","Aplicação", "Vale Alimentação", "Restaurante","Celular","Anuidade","Seguro", "Internet","Vestuário","Salário","Reembolso","Moradia", "Saúde","Taxas","Depósito","Plano Assistencial","Transporte","Previdência","Outros", "Pet: Milo", "Pet: Bolt", "Milo & Bolt", "Veículo", "Combustível", "Manutenção"], key="cat_novo_lancamento") 
        
        # Um respiro leve para desgrudar a categoria do status
        st.markdown("")
        f_sta = st.selectbox("Status", ["Pago", "Pendente"], key="sta_novo_lancamento")
        
        # Mais um respiro antes do botão para ele descolar do status
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.form_submit_button("Salvar Lançamento"):
            todos_dados = ws_base.get_all_records()
            
            if todos_dados:
                import pandas as pd
                df_temp = pd.DataFrame(todos_dados)
                if 'ID' in df_temp.columns and not df_temp['ID'].isna().all():
                    proximo_id = int(df_temp['ID'].max()) + 1
                else:
                    proximo_id = 1
            else:
                proximo_id = 1

            v_str = f"{f_val:.2f}".replace('.', ',')
            f_compra_str = f_compra.strftime("%d/%m/%Y")
            
            for i in range(f_par):
                nova_data = t_dat + relativedelta(months=i)
                
                if f_par > 1:
                    desc_com_parcela = f"{f_desc.strip()} {i+1}/{f_par}"
                else:
                    desc_com_parcela = f_desc.strip()
                
                ws_base.append_row([
                    nova_data.strftime("%d/%m/%Y"),
                    v_str,
                    desc_com_parcela,
                    f_cat,
                    f_tip,
                    f_bnc,
                    f_sta,
                    f_compra_str,
                    proximo_id + i,
                    beneficiario_final  # Salva certinho na coluna J
                ])
            
            st.toast(f"✅ Lançamento {proximo_id} salvo!", icon="💰")
            atualizar_sessao()
            st.rerun()
            
            
       # --- BARRINHA 2: TRANSFERÊNCIA ---
    with st.sidebar.expander("💸 Transferência", expanded=False):
        with st.form("f_transf", clear_on_submit=True):
            t_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            t_val = st.number_input("Valor", min_value=0.0, step=0.01, format="%.2f")
            t_orig = st.selectbox("Origem (Sai):", bancos_disponiveis)
            
            st.markdown("")
            t_dest = st.selectbox("Destino (Entra):", bancos_disponiveis)
            
            st.markdown("")
            t_desc = st.text_input("Nota")
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("TRANSFERIR"):
                if t_orig == t_dest: 
                    st.error("Escolha bancos diferentes!")
                else:
                    # 1. Calcula o próximo ID de forma segura
                    todos_dados = ws_base.get_all_records()
                    if todos_dados:
                        import pandas as pd
                        df_temp = pd.DataFrame(todos_dados)
                        if 'ID' in df_temp.columns and not df_temp['ID'].isna().all():
                            proximo_id = int(df_temp['ID'].max()) + 1
                        else:
                            proximo_id = 1
                    else:
                        proximo_id = 1
                    
                    v_str = f"{t_val:.2f}".replace('.', ',')
                    d_str = t_dat.strftime("%d/%m/%Y")
                    
                    # Descrição unificada para identificar o par da transferência facilmente
                    desc_transf = f"TR: {t_desc}".strip() if t_desc else "TR: Transferência entre contas"
                    
                    # 2. Salva as duas pontas na planilha com IDs sequenciais (Origem e Destino)
                    ws_base.append_row([d_str, v_str, desc_transf, "Transferência", "Despesa", t_orig, "Pago", d_str, proximo_id, ""])
                    ws_base.append_row([d_str, v_str, desc_transf, "Transferência", "Receita", t_dest, "Pago", d_str, proximo_id + 1, ""])
                    
                    st.toast("✅ Transferência sincronizada nas duas pontas!", icon="💰")
                    atualizar_sessao()
                    st.rerun()

           
    # --- BARRINHA 3: AJUSTE / EXCLUSÃO ---

with st.sidebar.expander("⚙️ Ajustar Lançamento", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} ! {r['Vencimento']} ! {r['Descrição']} ! R$ {r['Valor']}": r for _, r in df_base.iloc[::-1].iterrows()}
        escolha = st.selectbox("Selecione para Alterar/Excluir:", [""] + list(lista_edit.keys()), key="selectbox_ajuste")
             
        if escolha:
            item = lista_edit[escolha]
            data_atual_dt = datetime.strptime(item['Vencimento'], "%d/%m/%Y")
            
            # Respiro leve para desgrudar o campo de seleção de cima
            st.markdown("")
            ed_dat = st.date_input("Alterar Vencimento:", value=data_atual_dt, format="DD/MM/YYYY")
            
            ed_val = st.number_input("Alterar Valor:", value=float(item['V_Num']), step=0.01, format="%.2f")
            ed_desc = st.text_input("Alterar Descrição:", value=item['Descrição'])
            
            st.markdown("")
            idx_b = bancos_disponiveis.index(item['Banco']) if item['Banco'] in bancos_disponiveis else 0
            ed_bnc = st.selectbox("Alterar Banco:", bancos_disponiveis, index=idx_b)
            
            st.markdown("")
            status_opcoes = ["Pago", "Pendente"]
            index_status = status_opcoes.index(item['Status']) if item['Status'] in status_opcoes else 0
            ed_sta = st.selectbox("Status:", status_opcoes, index=index_status)
            
            st.markdown("<br>", unsafe_allow_html=True)
            col_ed1, col_ed2 = st.columns(2)
            
            if col_ed1.button("💾 ATUALIZAR"):
                id_atual = int(float(item['ID']))
                
                # Se for Transferência, atualiza as duas pontas (origem e destino)
                if str(item['Categoria']).strip() == 'Transferência':
                    desc_antiga = str(item['Descrição'])
                    data_antiga = str(item['Vencimento'])
                    valor_antigo = float(item['V_Num'])
                    
                    # Varre a base para achar todas as linhas que formam essa transferência
                    for idx, row in df_base.iterrows():
                        if (str(row['Vencimento']) == data_antiga and 
                            abs(float(row['V_Num']) - valor_antigo) < 0.01 and 
                            str(row['Descrição']) == desc_antiga and 
                            str(row['Categoria']).strip() == 'Transferência'):
                            
                            linha_id = int(float(row['ID']))
                            ws_base.update_cell(linha_id, 1, ed_dat.strftime("%d/%m/%Y"))
                            ws_base.update_cell(linha_id, 2, f"{ed_val:.2f}".replace('.', ','))
                            ws_base.update_cell(linha_id, 3, ed_desc)
                            ws_base.update_cell(linha_id, 6, ed_bnc)
                            ws_base.update_cell(linha_id, 7, ed_sta)
                else:
                    # Lançamento normal (atualiza só a linha selecionada)
                    ws_base.update_cell(id_atual, 1, ed_dat.strftime("%d/%m/%Y"))
                    ws_base.update_cell(id_atual, 2, f"{ed_val:.2f}".replace('.', ','))
                    ws_base.update_cell(id_atual, 3, ed_desc)
                    ws_base.update_cell(id_atual, 6, ed_bnc)
                    ws_base.update_cell(id_atual, 7, ed_sta)
                
                st.toast("✅ Atualização sincronizada nas duas pontas!", icon="💰")
                if "selectbox_ajuste" in st.session_state:
                    del st.session_state["selectbox_ajuste"]
                atualizar_sessao()
                st.rerun()
                
            if col_ed2.button("🚨 EXCLUIR"):
                if item['Categoria'] == 'Transferência':
                    ids_para_excluir = []
                    for idx, row in df_base.iterrows():
                        mesma_data = (str(row['Vencimento']) == str(item['Vencimento']))
                        mesmo_valor = (abs(float(row['V_Num']) - float(item['V_Num'])) < 0.01)
                        mesma_desc = (str(row['Descrição']) == str(item['Descrição']))
                        eh_transf = (str(row['Categoria']).strip() == 'Transferência')
                        
                        if mesma_data and mesmo_valor and mesma_desc and eh_transf:
                            if 'ID' in row and pd.notna(row['ID']):
                                ids_para_excluir.append(int(float(row['ID'])))
                    
                    if ids_para_excluir:
                        for id_linha in sorted(list(set(ids_para_excluir)), reverse=True):
                            try:
                                ws_base.delete_rows(id_linha)
                            except:
                                pass
                    else:
                        ws_base.delete_rows(int(float(item['ID'])))
                else:
                    ws_base.delete_rows(int(float(item['ID'])))
                
                st.toast("✅ Transferência e contrapartida excluídas com sucesso!", icon="💰")
                if "selectbox_ajuste" in st.session_state:
                    del st.session_state["selectbox_ajuste"]
                atualizar_sessao()
                st.rerun()

# --- INÍCIO DA ABA: 💰 Finanças & Bancos (COM GRÁFICO DE METAS) ---
if "💰" in st.session_state.page:
    import plotly.graph_objects as go
    
    st.markdown("""<style>.block-container { padding-top: 0rem; padding-bottom: 0rem; }</style>""", unsafe_allow_html=True)
    st.subheader("🛡️ FinançasPro Wilson")

    # 1. BARRINHA DE MESES
    meses_abreviados = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual_hoje = datetime.now().strftime("%b")
    mes_atual = st.pills("Período:", meses_abreviados, selection_mode="single", default=mes_atual_hoje)
    
    if not df_base.empty:
        # 2. TRADUÇÃO DO FILTRO
        mes_map = {"Jan": "01", "Fev": "02", "Mar": "03", "Abr": "04", "Mai": "05", "Jun": "06", 
                   "Jul": "07", "Ago": "08", "Set": "09", "Out": "10", "Nov": "11", "Dez": "12"}
        filtro_mes = f"{mes_map[mes_atual]}/26"
        
        # Filtra os dados do mês
        df_m = df_base[df_base['Mes_Ano'] == filtro_mes].copy()
        df_m_limpo = df_m[(df_m['Categoria'] != 'Transferência') & (df_m['Status'] == 'Pago')]
        
        # 3. CÁLCULOS
        receita_total = df_m_limpo[df_m_limpo['Tipo'] == 'Receita']['V_Num'].sum()
        gasto_total = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa']['V_Num'].sum()
        rendimento = df_m_limpo[df_m_limpo['Tipo'] == 'Rendimento']['V_Num'].sum()
        pendente = df_m[df_m['Status'] == 'Pendente']['V_Num'].sum()
        saldo_geral = (receita_total + rendimento) - gasto_total

        # 4. EXIBIÇÃO DO SALDO
        # 4. EXIBIÇÃO DO SALDO
        cor_saldo = "#2ecc71" if saldo_geral >= 0 else "#e74c3c"
        st.markdown(f"""
            <div style="text-align: center; background-color: #f8f9fb; padding: 15px; border-radius: 10px; border-left: 5px solid {cor_saldo};">
                <p style="margin: 0; font-size: 1rem; color: #666; font-weight: bold;">SALDO DISPONÍVEL</p>
                <h1 style="margin: 0; color: {cor_saldo}; font-size: 2.5rem;">R$ {saldo_geral:,.2f}</h1>
            </div>
        """, unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📈 Receita", f"R$ {receita_total:,.2f}")
        c2.metric("📉 Gasto", f"R$ {gasto_total:,.2f}")
        c3.metric("💰 Rendimento", f"R$ {rendimento:,.2f}")
        c4.metric("⏳ Pendente", f"R$ {pendente:,.2f}")
        st.divider()

        # 5. GRÁFICOS DE APOIO (Pizza e Fluxo)
        g1, g2 = st.columns(2)
        with g1:
            st.write("### 🍕 Gastos por Categoria")
            df_p = df_m_limpo[df_m_limpo['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum().reset_index()
            if not df_p.empty:
                st.plotly_chart(px.pie(df_p, values='V_Num', names='Categoria', hole=0.4), use_container_width=True)

        
        with g2:
          
            st.write("### 📊 Fluxo Mensal (3 Meses)")
            
            # Cálculo dos 3 meses a partir do mês selecionado
            idx = meses_abreviados.index(mes_atual)
            meses_para_exibir = [meses_abreviados[max(0, idx-2)], meses_abreviados[max(0, idx-1)], meses_abreviados[idx]]
            filtro_lista = [f"{mes_map[m]}/26" for m in meses_para_exibir]
            
            # Filtra a base completa pelos meses selecionados
            df_fluxo = df_base[df_base['Mes_Ano'].isin(filtro_lista)].copy()
            
            # 🔒 EXCLUI AS TRANSFERÊNCIAS (Olhando pelo campo Categoria ou Descrição onde diz transferência)
            if not df_fluxo.empty:
                if 'Categoria' in df_fluxo.columns:
                    # Remove se a categoria contiver "transferência" (ignorando maiúsculas/minúsculas)
                    df_fluxo = df_fluxo[~df_fluxo['Categoria'].astype(str).str.lower().str.contains('transferência', na=False)]
            
            # Prepara os dados para o gráfico
            df_f = df_fluxo.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().reset_index()
            
            if not df_f.empty:
                # Gráfico com cores fixas e layout limpo
                fig_fluxo = px.bar(
                    df_f, 
                    x='Mes_Ano', 
                    y='V_Num', 
                    color='Tipo', 
                    barmode='group',
                    color_discrete_map={
                        'Receita': '#2ecc71', 
                        'Despesa': '#e74c3c', 
                        'Rendimento': '#3498db'
                    },
                    text_auto='.2s' # Adiciona o valor em cima da barra
                )
                fig_fluxo.update_layout(
                    height=350, 
                    margin=dict(t=30, b=10, l=0, r=0),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_fluxo, use_container_width=True)
            else:
                st.info("Aguardando dados para o período...")
                

# 6. NOVO: GRÁFICO DE METAS (Vamos usar o df_m direto para testar)
        st.subheader("🎯 Metas vs Realizado (Despesas)")
        
        # Teste: use df_m em vez de df_m_limpo
        df_metas_graph = df_m[(df_m['Tipo'] == 'Despesa') & (df_m['Categoria'] != 'Transferência')].groupby('Categoria')['V_Num'].sum().reset_index()
        
        if not df_metas_graph.empty:
            df_metas_graph['Meta'] = df_metas_graph['Categoria'].apply(lambda cat: st.session_state.get(f"m_{cat}", 0.0))
            
            fig_m = go.Figure()
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['V_Num'], name='Realizado', marker_color='#e74c3c'))
            fig_m.add_trace(go.Bar(x=df_metas_graph['Categoria'], y=df_metas_graph['Meta'], name='Meta Estipulada', marker_color='#2ecc71', opacity=0.4))
            
            fig_m.update_layout(barmode='group', height=350, margin=dict(t=30, b=10, l=0, r=0))
            st.plotly_chart(fig_m, use_container_width=True)
        else:
            st.info(f"O gráfico está vazio. Verifique se existem lançamentos do tipo 'Despesa' em {mes_atual}.")

                                        # --- COMPARATIVO MENSAL EFICIENTE (AJUSTADO PARA O SEU CÓDIGO) ---
        st.subheader("🔄 Comparativo: Mês Anterior vs. Mês Atual")
        
        # 1. Obter o número do mês atual a partir da sua seleção
        # O seu 'mes_map' já tem a relação, vamos usar isso:
        mes_map = {"Jan": 1, "Fev": 2, "Mar": 3, "Abr": 4, "Mai": 5, "Jun": 6, 
                   "Jul": 7, "Ago": 8, "Set": 9, "Out": 10, "Nov": 11, "Dez": 12}
        
        mes_atual_num = mes_map[mes_atual]
        mes_anterior_num = mes_atual_num - 1 if mes_atual_num > 1 else 12
        
        # 2. Preparar os dados (convertendo a coluna de vencimento para data)

        df_comp = df_base.copy()
        
        # --- BLOCO DE SEGURANÇA PARA DATAS ---
        df_comp['Vencimento'] = pd.to_datetime(df_comp['Vencimento'], dayfirst=True, errors='coerce')
        
        # Correção aqui: era .co e agora é .copy()
        df_comp = df_comp[df_comp['Vencimento'].dt.month.isin([mes_anterior_num, mes_atual_num])].copy()
        
       # 4. Tabela dinâmica
        df_pivot = df_comp[df_comp['Tipo'] == 'Despesa'].pivot_table(
            index='Categoria', 
            columns=df_comp['Vencimento'].dt.month, 
            values='V_Num', 
            aggfunc='sum'
        ).fillna(0)
        
        # 5. Renomeia as colunas
        colunas_renomeadas = {mes_anterior_num: "Mês Anterior", mes_atual_num: "Mês Atual"}
        df_pivot = df_pivot.rename(columns=colunas_renomeadas)
        
        # 6. Cálculo da variação
        if "Mês Anterior" in df_pivot.columns and "Mês Atual" in df_pivot.columns:
            df_pivot['Variação (%)'] = ((df_pivot["Mês Atual"] - df_pivot["Mês Anterior"]) / df_pivot["Mês Anterior"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)

        # --- DEFINIÇÃO DA FORMATAÇÃO (Para resolver o NameError) ---
        formatacao = {
            "Mês Anterior": "{:.2f}",
            "Mês Atual": "{:.2f}",
            "Variação (%)": "{:.2f}%"
        }

        # Agora o st.dataframe vai encontrar a variável formatacao
        st.dataframe(df_pivot.style.format(formatacao), use_container_width=True)
        # Aplicamos o estilo (o .style.format aplica o que definimos no dicionário)
        
        # --- FILTRO DE ALERTA: PENDÊNCIAS DO MÊS ---
        st.subheader("🔔 Monitor de Pendências do Período")
        
        # Filtra apenas o que está pendente E pertence ao mês selecionado
        # Usamos 'filtro_mes' que você já definiu no seu código anterior!
        df_pendente_mes = df_base[(df_base['Status'] == 'Pendente') & (df_base['Mes_Ano'] == filtro_mes)]
        
        if not df_pendente_mes.empty:
            st.warning(f"⚠️ Atenção: Você tem {len(df_pendente_mes)} lançamento(s) pendente(s) em {mes_atual}/26!")
            
            # Exibe as pendências do mês
            st.dataframe(df_pendente_mes[['Vencimento', 'Descrição','Banco','Valor', 'Categoria']], use_container_width=True)
        else:
            st.success(f"✅ Tudo limpo! Nenhuma pendência para {mes_atual}/26.")
        
        
            # --- AQUI COMEÇA O WILSONBOT ---
        st.subheader("🤖 Consultor WilsonBot")
        
        # Analisa o mês atual
        df_atual = df_m # Usamos o seu df filtrado que já está pronto
        filtro_exclusao = (df_atual['Tipo'] == 'Despesa') & (~df_atual['Categoria'].isin(['Transferência']))
        total_gasto = df_atual[filtro_exclusao]['V_Num'].sum()
        
        # Analisa a média dos últimos 3 meses
        # Nota: Ajustei para filtrar só Despesas na média também, para ficar mais preciso
        df_despesas_totais = df_base[df_base['Tipo'] == 'Despesa']
        meses_passados = df_despesas_totais.groupby('Mes_Ano')['V_Num'].sum().tail(3).mean()

        if total_gasto > meses_passados:
            st.warning(f"⚠️ **Atenção, Wilson!** Seus gastos este mês estão R$ {(total_gasto - meses_passados):,.2f} acima da sua média dos últimos 3 meses.")
        else:
            st.success("✅ **Parabéns!** Seus gastos estão controlados e abaixo da sua média recente.")

        
        # Identifica o maior vilão (Excluindo Transferências e Ajustes)
        # Filtramos 'Despesa' E que a categoria NÃO ESTEJA na lista de exclusão
        categorias_para_ignorar = ['Transferência', 'Ajuste']
        
        df_filtrado = df_atual[(df_atual['Tipo'] == 'Despesa') & (~df_atual['Categoria'].isin(categorias_para_ignorar))]
        
        df_vilao = df_filtrado.groupby('Categoria')['V_Num'].sum()
        
        if not df_vilao.empty:
            maior_gasto = df_vilao.idxmax()
            valor_maior = df_vilao.max()
            st.info(f"💡 **Dica de Ouro:** Sua categoria de maior gasto este mês é '{maior_gasto}', totalizando R$ {valor_maior:,.2f}. Considere revisar esses custos para o próximo mês!")
        else:
            st.info("💡 **Dica de Ouro:** Tudo certo! Não foram detectadas despesas recorrentes além de transferências internas.")

            
# 7. TABELA FINAL
        st.subheader("🔍 Lançamentos do Mês")
        
        if not df_m_limpo.empty:
            df_exibicao = df_m_limpo.copy()
            
            # Ordena pelo ID do maior para o menor para o mais recente ficar sempre no topo
            if 'ID' in df_exibicao.columns:
                df_exibicao = df_exibicao.sort_values(by='ID', ascending=False)
            
            # AJUSTE DE MENTOR: 
            # Se você sente que a diferença é de 2, mudamos aqui.
            ajuste = 2 
            df_exibicao['Seq.'] = range(len(df_exibicao), 0, -1) # Mantém a sequência decrescente bonitinha
            
            st.dataframe(df_exibicao[['Seq.', 'Vencimento', 'Descrição', 'Valor', 'Categoria', 'Banco', 'Status']], 
                         use_container_width=True, 
                         hide_index=True)
        else:
            st.warning("Base de dados vazia.")


elif "Pendências" in aba:
    st.title("📋 Lançamentos Pendentes")
        
    # --- FILTROS UNIFICADOS ---
    c1, c2, c3 = st.columns(3)
    filtro_banco = c1.multiselect("Filtrar Banco/Cartão:", sorted(bancos_disponiveis), key="banco_pend")
    busca_desc = c2.text_input("Buscar Descrição:", key="desc_pend")
    periodo = c3.date_input("Período:", (datetime.now().replace(day=1), datetime.now()), format="DD/MM/YYYY", key="data_pend")

    # --- PROCESSAMENTO ---
    df_v = df_base[df_base['Status'].astype(str).str.strip().str.lower() == 'pendente'].copy()
    df_v['Data_Formatada'] = pd.to_datetime(df_v['Vencimento'], dayfirst=True, errors='coerce')
    df_v = df_v.dropna(subset=['Data_Formatada'])

    if filtro_banco:
        df_v = df_v[df_v['Banco'].isin(filtro_banco)]
    if busca_desc:
        df_v = df_v[df_v['Descrição'].str.contains(busca_desc, case=False, na=False)]
        
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_v = df_v[(df_v['Data_Formatada'].dt.date >= periodo[0]) & (df_v['Data_Formatada'].dt.date <= periodo[1])]

        # --- EXIBIÇÃO ---
        st.write(f"### Lançamentos Encontrados: {len(df_v)}")
        df_display = df_v[['ID', 'Vencimento', 'Banco', 'Descrição', 'Valor', 'Categoria']].copy()
        df_display['Valor'] = df_v['V_Num'].apply(m_fmt)
        st.dataframe(df_display.iloc[::-1], use_container_width=True, hide_index=True)

        # --- BOTÃO DE BAIXA ---
        if not df_v.empty:
            nova_data = st.date_input("Data de pagamento para baixa:", datetime.now(), key="data_baixa_pend")
            if st.button("✅ BAIXAR SELECIONADOS", key="btn_baixa_final"):
                headers = ws_base.row_values(1)
                idx_status = headers.index('Status') + 1
                idx_venc = [i for i, h in enumerate(headers) if 'VENC' in h.upper() or 'DATA' in h.upper()][0] + 1
                
                sucessos = 0
                for idx_df, row in df_v.iterrows():
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
    
  # 1. Filtros
    c1, c2, c3 = st.columns(3)
    s_bnc = c1.multiselect("Filtrar Banco/Cartão:", sorted(bancos_disponiveis), key="banco_aviso")
    b_desc = c2.text_input("Buscar Descrição:", key="busca_desc_aviso")
    # Calendário forçado no padrão BR
    periodo = c3.date_input("Período:", (datetime.now().replace(day=1), datetime.now()), format="DD/MM/YYYY", key="data_aviso")

    # 2. Processamento (Filtro inicial de Pendentes)
    df_v = df_base[df_base['Status'] == 'Pendente'].copy()
    
    # Conversão única e segura usando apenas 'Vencimento'
    df_v['Data_Formatada'] = pd.to_datetime(df_v['Vencimento'], dayfirst=True, errors='coerce')
    df_v = df_v.dropna(subset=['Data_Formatada'])
    
    # 3. Aplicar Filtro de Banco e Descrição
    if s_bnc:
        df_v = df_v[df_v['Banco'].isin(s_bnc)]
    if b_desc:
        df_v = df_v[df_v['Descrição'].str.contains(b_desc, case=False, na=False)]
    
    # 4. Filtro de Data único e direto
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_v = df_v[
            (df_v['Data_Formatada'].dt.date >= periodo[0]) & 
            (df_v['Data_Formatada'].dt.date <= periodo[1])
        ]
        
    # 5. Exibição
    st.write(f"Total de itens encontrados: {len(df_v)}")
    
    # Garante que as colunas existem antes de exibir
    colunas_exibicao = ['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Categoria', 'Banco', 'Status']
    df_v_display = df_v[colunas_exibicao].copy()
    
    # Formatação do Valor
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
    st.info("💡 **Atenção:** Digite a quantidade em **Litros** e a distância em **Quilômetros**.")
    
    c_cons1, c_cons2, c_cons3 = st.columns(3)
    litros = c_cons1.number_input("Litros Abastecidos", value=0.0, step=0.5, format="%.1f")
    distancia = c_cons2.number_input("Distância Percorrida (km)", value=0, step=10, format="%d")
    
    # Validação segura: só calcula se ambos forem maiores que zero
    if litros > 0:
        consumo = distancia / litros
        c_cons3.metric(label="Consumo Médio", value=f"{consumo:.2f} km/l")
    else:
        c_cons3.warning("Aguardando dados...")
        
    st.divider()
    df_car = df_base[df_base['Categoria'].str.contains('Veículo|Combustível|Manutenção', case=False, na=False)]
    if not df_car.empty:
        df_car_display = df_car[['ID', 'Vencimento', 'Tipo', 'Valor', 'Descrição', 'Status', 'Banco']].copy()
        df_car_display['Valor'] = df_car['V_Num'].apply(m_fmt)
        st.dataframe(df_car_display.iloc[::-1], use_container_width=True, hide_index=True)

elif "📄" in aba:
    st.title("📄 WhatsApp")
    
    # Trava a data de início no primeiro dia do mês atual
    primeiro_dia_mes = hoje_br.replace(day=1)
    
    c1, c2 = st.columns(2)
    d_ini = c1.date_input("Início", primeiro_dia_mes, format="DD/MM/YYYY", key="zap_d1")
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
            mask = (df_base['Banco'] == b) & \
           (df_base['Status'].str.upper() == 'PENDENTE') & \
           (pd.to_datetime(df_base['Vencimento'], errors='coerce', dayfirst=True).dt.date <= d_fim)

            usado = df_base.loc[mask, 'V_Num'].sum()
            #usado = df_cart_base[df_cart_base['DT_ONLY'] <= d_fim]['V_Num'].sum()
            
            dispo = limite_cartao - usado
            
            #saldos_txt += f"💳 {b}: Limite: {m_fmt(limite_cartao)} | Usado: {m_fmt(usado)} | Disp: {m_fmt(dispo)} (Venc: {dia_venc_e})\n"
            usado_fmt = f"{m_fmt(usado)} 🔴" if usado > 0 else m_fmt(0)
            saldos_txt += f"💳 {b}: Limite: {m_fmt(limite_cartao)} | Usado: {usado_fmt} | Disp: {m_fmt(dispo)} (Venc: {dia_venc_e})\n"
        
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

# 2. RESUMO DO RELATÓRIO (Rendimento, Sobra e Pendentes)
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

        # Valor pendente total do período (despesas comuns + faturas/cartões pendentes no mês)
        val_pendente = df_per[(df_per['T_UP'] == 'DESPESA') & (df_per['Status'].str.upper() == 'PENDENTE') & (~df_per['C_UP'].str.contains('TRANS', na=False))]['V_Num'].sum()
    else:
        rec_v = des_v = rend_v = sobra = val_pendente = 0.0

    # 3. TEXTO FINAL (Sem a linha separada de cartão, apenas o Pendente consolidado)
    relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
    relat += f"========================================\n"
    relat += f"REC: {m_fmt(rec_v)} | REND: {m_fmt(rend_v)} (Info)\n"
    relat += f"DES: {m_fmt(des_v)} | SOBRA: {m_fmt(sobra)}\n"
    relat += f"⏳ Pendente de Pagamento: {m_fmt(val_pendente)}\n"
    relat += f"========================================\n\n"
    relat += f"SALDOS:\n{saldos_txt}\nTOTAL PATRIMÔNIO: {m_fmt(total_patrimonio)}"
    
    st.text_area("Copiar Relatório", relat, height=300)
    st.markdown(f'[📲 Enviar para o WhatsApp](https://wa.me/?text={urllib.parse.quote(relat)})')

if aba == "📋 Relatório PDF":
    st.markdown("### 📋 Emissão de Relatório Financeiro")

    # -------------------------------------------------------------------------
    # 1. FILTROS DA TELA (Com chaves exclusivas e espaçamentos blindados)
    # -------------------------------------------------------------------------
    col_rel1, col_rel2 = st.columns(2)
    with col_rel1:
        opcoes_banco_rel = ["Todos"] + list(bancos_disponiveis)
        banco_relatorio = st.selectbox("Filtrar Banco:", opcoes_banco_rel, key="sb_rel_banco")
        
    with col_rel2:
        hoje_atual = datetime.now()
        primeiro_dia_mes = hoje_atual.replace(day=1)
        if hoje_atual.month == 12:
            ultimo_dia_mes = hoje_atual.replace(year=hoje_atual.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            ultimo_dia_mes = hoje_atual.replace(month=hoje_atual.month + 1, day=1) - timedelta(days=1)

        periodo_pdf = st.date_input("Período do Relatório:", [primeiro_dia_mes, ultimo_dia_mes], format="DD/MM/YYYY", key="dt_rel_periodo")

    # Espaço respiro para a próxima linha não grudar
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

    col_rel3, col_rel4, col_rel5 = st.columns(3)
    with col_rel3:
            busca_desc = st.text_input("🔍 Pesquisar por Descrição:", "", key="txt_rel_desc").strip()
            
    with col_rel4:
        # Puxa os beneficiários únicos da coluna correspondente para formar a lista
        beneficiarios_unicos = []
        df_temp = df_base if 'df_base' in locals() else df_report
        
        # Identifica a coluna de beneficiário de forma segura
        col_ben = next((c for c in df_temp.columns if 'BENEFICIÁRIO' in c.upper() or 'BENEFICIARIO' in c.upper()), None)
        if col_ben and not df_temp.empty:
            nomes_brutos = df_temp[col_ben].dropna().astype(str)
            unicos_dict = {}
            for n in nomes_brutos:
                n_limpo = n.strip()
                if n_limpo and n_limpo.lower() != 'nan':
                    chave = n_limpo.lower()
                    if chave not in unicos_dict:
                        unicos_dict[chave] = n_limpo
            beneficiarios_unicos = sorted(list(unicos_dict.values()))

        opcoes_benef = ["Todos"] + beneficiarios_unicos
        
        busca_benef_select = st.selectbox("👤 Filtrar Beneficiário:", options=opcoes_benef, key="sb_beneficiario_rel")
        busca_benef = "" if busca_benef_select == "Todos" else busca_benef_select
        
    with col_rel5:
            busca_status = st.selectbox("📌 Filtrar Status:", ["Todos", "Pago", "Pendente"], key="sb_rel_status")

    # Espaço respiro antes dos filtros de Categoria e Tipo
    st.markdown("<div style='height: 5px;'></div>", unsafe_allow_html=True)

    col_rel6, col_rel7 = st.columns(2)
    with col_rel6:
        categorias_disponiveis = sorted(df_base['Categoria'].dropna().unique()) if 'Categoria' in df_base.columns else []
        opcoes_cat_rel = ["Todas"] + list(categorias_disponiveis)
        busca_categoria = st.selectbox("📂 Filtrar Categoria:", opcoes_cat_rel, key="sb_rel_categoria")

    with col_rel7:
        tipos_disponiveis = sorted(df_base['Tipo'].dropna().unique()) if 'Tipo' in df_base.columns else []
        opcoes_tipo_rel = ["Todos"] + list(tipos_disponiveis)
        busca_tipo = st.selectbox("🏷️ Filtrar Tipo:", opcoes_tipo_rel, key="sb_rel_tipo")

    st.markdown("---")

    # Botão para processar e gerar o documento / visualizar
    if st.button("📄 Gerar PDF", key="btn_gerar_pdf"):
        try:
            if isinstance(periodo_pdf, (list, tuple)):
                if len(periodo_pdf) == 2:
                    b_ini, b_fim = periodo_pdf[0], periodo_pdf[1]
                else:
                    b_ini = b_fim = periodo_pdf[0]
            else:
                b_ini = b_fim = periodo_pdf

            # ========================================================
            # INICIALIZAÇÃO DO PDF
            # ========================================================
            from fpdf import FPDF
            pdf = FPDF(orientation='P', unit='mm', format='A4')
            pdf.set_margins(left=8, top=10, right=8)
            pdf.add_page()

            # ========================================================
            # CAPTURA E FILTRAGEM COMPLETA DOS DADOS (PDF)
            # ========================================================
            df_report = df_base.copy()

            col_banco_df = next((c for c in df_report.columns if c.upper() in ['BANCO', 'CONTA']), None)
            col_data_df = next((c for c in df_report.columns if c.upper() in ['VENCIMENTO', 'DATA', 'DT']), None)
            col_desc_df = next((c for c in df_report.columns if c.upper() in ['DESCRIÇÃO', 'DESCRICAO', 'NOTA']), None)
            col_status_df = next((c for c in df_report.columns if c.upper() in ['STATUS']), None)
            col_compra_df = next((c for c in df_report.columns if c.upper() in ['COMPRA', 'DATA COMPRA', 'DT COMPRA']), None)

            banco_nome = "Todos os Bancos"
            if banco_relatorio != "Todos" and col_banco_df:
                banco_nome = banco_relatorio

            eh_cartao_geral = "CARTAO" in str(banco_nome).upper() or "CARTÃO" in str(banco_nome).upper()

            if eh_cartao_geral and col_data_df:
                col_filtro_ativo = col_data_df
            else:
                col_filtro_ativo = col_data_df if col_data_df else df_report.columns[0]

            df_report['DT_FILTRO'] = pd.to_datetime(df_report[col_filtro_ativo], format="%d/%m/%Y", errors='coerce')

            t_ini = pd.to_datetime(b_ini)
            t_fim = pd.to_datetime(b_fim)

            # Aplica os filtros
            df_report = df_report[(df_report['DT_FILTRO'] >= t_ini) & (df_report['DT_FILTRO'] <= t_fim)]

            if banco_relatorio != "Todos" and col_banco_df:
                df_report = df_report[df_report[col_banco_df].str.upper().str.strip() == str(banco_nome).upper()]

            if busca_desc and col_desc_df:
                df_report = df_report[df_report[col_desc_df].astype(str).str.contains(busca_desc, case=False, na=False)]

            if busca_benef:
                col_benef_nome = df_report.columns[9]  # Coluna J
                df_report = df_report[df_report[col_benef_nome].astype(str).str.contains(busca_benef, case=False, na=False)]

            if busca_status != "Todos" and col_status_df:
                df_report = df_report[df_report[col_status_df].str.upper().str.strip() == str(busca_status).upper()]

            # Filtro de Categoria
            if busca_categoria != "Todas" and 'Categoria' in df_report.columns:
                df_report = df_report[df_report['Categoria'].str.upper().str.strip() == str(busca_categoria).upper()]

            # Filtro de Tipo
            if 'busca_tipo' in locals() and busca_tipo != "Todos" and 'Tipo' in df_report.columns:
                df_report = df_report[df_report['Tipo'].str.upper().str.strip() == str(busca_tipo).upper()]

            # ========================================================
            # ORDENAÇÃO INTELIGENTE
            # ========================================================
            if banco_relatorio == "Todos":
                def pega_data_ordenacao(row):
                    b_linha = str(row.get(col_banco_df, '')).upper()
                    if ("CARTAO" in b_linha or "CARTÃO" in b_linha) and col_compra_df:
                        return row.get(col_compra_df, row.get(col_data_df))
                    else:
                        return row.get(col_data_df)
                
                df_report['DT_ORDEM_TEMP'] = df_report.apply(pega_data_ordenacao, axis=1)
                df_report['DT_ORDEM'] = pd.to_datetime(df_report['DT_ORDEM_TEMP'], format="%d/%m/%Y", errors='coerce')
            else:
                if eh_cartao_geral and col_compra_df:
                    df_report['DT_ORDEM'] = pd.to_datetime(df_report[col_compra_df], format="%d/%m/%Y", errors='coerce')
                else:
                    df_report['DT_ORDEM'] = pd.to_datetime(df_report[col_filtro_ativo], format="%d/%m/%Y", errors='coerce')

            df_report = df_report.sort_values(by='DT_ORDEM')

            # ========================================================
            # 3. BUSCA DO SALDO DE ABERTURA - MATEMÁTICA REAL COMBINADA
            # ========================================================
            base_inicial = 0.0
            
            if eh_cartao_geral:
                base_inicial = 0.0
            else:
                try:
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

                    df_historico = df_base.copy()
                    col_data_h = next((c for c in df_historico.columns if c.upper() in ['VENCIMENTO', 'DATA', 'DT']), None)
                    col_banco_h = next((c for c in df_historico.columns if c.upper() in ['BANCO', 'CONTA']), None)
                    
                    if col_data_h:
                        df_historico['DT_HIST'] = pd.to_datetime(df_historico[col_data_h], format="%d/%m/%Y", errors='coerce')
                    else:
                        df_historico['DT_HIST'] = pd.to_datetime(df_historico.index, errors='coerce')
                        
                    if banco_nome != "Todos os Bancos" and col_banco_h:
                        df_historico = df_historico[df_historico[col_banco_h].str.upper().str.strip() == str(banco_nome).upper()]
                    
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
                    
                    base_inicial = saldo_sistema_abril + saldo_acumulado_passado
                except:
                    base_inicial = 0.0

            saldo_anterior = base_inicial 

            # ========================================================
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
            # 5. MONTAGEM DO CABEÇALHO DO PDF
            # ========================================================
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
            
            val_benef = str(locals().get('busca_benef', 'Todos')).strip()
            if val_benef and val_benef.upper() != "TODOS" and val_benef != "---":
                pdf.set_font("Arial", 'B', 10)
                pdf.cell(200, 6, txt=f"BENEFICIARIO: {val_benef.upper()}", ln=1, align="L")
            
            pdf.ln(2)
            pdf.set_font("Arial", '', 10)
            p_inicio = pd.to_datetime(b_ini).strftime('%d/%m/%Y')
            p_fim = pd.to_datetime(b_fim).strftime('%d/%m/%Y')
            
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(200, 6, txt=f"BANCO / CARTAO: {str(banco_nome).upper()}", ln=1, align="L")
        
            if eh_cartao_geral:
                dt_fim_obj = pd.to_datetime(b_fim)
                dia_venc = "20"
                try:
                    for var_name, var_val in list(locals().items()) + list(globals().items()):
                        if isinstance(var_val, pd.DataFrame) and 'Nome do Banco' in var_val.columns and 'Dia de Vencimento' in var_val.columns:
                            banco_busca = str(banco_nome).upper().strip()
                            match = var_val[var_val['Nome do Banco'].astype(str).str.upper().str.strip() == banco_busca]
                            if match.empty:
                                match = var_val[var_val['Nome do Banco'].astype(str).str.upper().str.contains(banco_busca, na=False)]
                            if not match.empty:
                                val_venc = match['Dia de Vencimento'].values[0]
                                if pd.notna(val_venc):
                                    dia_venc = str(int(float(val_venc))).zfill(2)
                                    break
                except Exception:
                    pass

                data_vencimento_fatura = f"{dia_venc}/{dt_fim_obj.strftime('%m/%Y')}"
                pdf.cell(200, 6, txt=f"FATURA COM VENCIMENTO EM: {data_vencimento_fatura}", ln=1, align="L")
            else:
                pdf.cell(200, 6, txt=f"PERIODO DO RELATORIO: {p_inicio} ate {p_fim}", ln=1, align="L")
            
            txt_saldo_ini = f"R$ {saldo_anterior:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
            pdf.cell(200, 6, txt=f"SALDO ANTERIOR / ABERTURA: {txt_saldo_ini}", ln=1, align="L")
            pdf.ln(5)
            
            # --- TÍTULO DA COLUNA DINÂMICO ---
            nome_coluna_data_pdf = "Dt Compra" if eh_cartao_geral else "Dt Venc/Pag"

            pdf.set_font("Arial", 'B', 9)
            pdf.cell(22, 7, nome_coluna_data_pdf, 1)
            pdf.cell(18, 7, "Tipo", 1)
            pdf.cell(33, 7, "Categoria", 1)
            pdf.cell(45, 7, "Descricao", 1)
            pdf.cell(25, 7, "Valor", 1)
            pdf.cell(32, 7, "Saldo Acum.", 1)
            pdf.cell(25, 7, "Status", 1)
            pdf.ln()

            # ========================================================
            # 6. LOOP DE IMPRESSÃO DAS LINHAS NO PDF (MOSTRA DATA DA COMPRA)
            # ========================================================
            if not df_report.empty:
                desc_col_temp = 'Descrição' if 'Descrição' in df_report.columns else 'Descricao'
                if desc_col_temp in df_report.columns:
                    df_report['_chave_desc'] = df_report[desc_col_temp].astype(str).str.strip().str.upper()
                    df_report['_parc_atual'] = df_report.groupby('_chave_desc').cumcount() + 1
                    df_report['_parc_total'] = df_report.groupby('_chave_desc')['_chave_desc'].transform('count')
                else:
                    df_report['_parc_atual'] = 1
                    df_report['_parc_total'] = 1
            
            pdf.set_font("Arial", '', 9)
            for index, row in df_report.iterrows():
                # Para cartão, força exibir a Data da Compra na linha da tabela
                b_linha_atual = str(row.get(col_banco_df, '')).upper()
                is_cartao_linha = "CARTAO" in b_linha_atual or "CARTÃO" in b_linha_atual
                
                if is_cartao_linha and col_compra_df:
                    data_str = str(row.get(col_compra_df, '---'))
                else:
                    data_str = str(row.get(col_data_df, '---'))
                
                tipo_str = str(row.get('Tipo', '---')).strip()
                cat_val = str(row.get('Categoria', 'Geral'))[:16]
                
                desc_base = str(row.get('Descrição', row.get('Descricao', 'Sem nome'))).strip()
                p_atual = row.get('_parc_atual', 1)
                p_total = row.get('_parc_total', 1)
                
                if int(p_total) > 1:
                    desc_val = f"{desc_base} {int(p_atual)}/{int(p_total)}"[:24]
                else:
                    desc_val = desc_base[:24]

                valor_val = pd.to_numeric(row.get('V_Num', row.get('Valor', 0)), errors='coerce')
                if pd.isna(valor_val): valor_val = 0.0
                saldo_val = row.get('Saldo_Acum', 0.0)
                status_val = str(row.get('Status', '-'))
                
                # --- VALORES NEGATIVOS DESTACADOS EM VERMELHO COM SINAL ---
                if "DESPESA" in tipo_str.upper() or "GASTO" in tipo_str.upper() or valor_val < 0:
                    texto_valor = f"- R$ {abs(valor_val):,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (255, 0, 0) # Vermelho
                else:
                    texto_valor = f"R$ {valor_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (0, 0, 0)

                texto_saldo = f"R$ {saldo_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                cor_saldo = (255, 0, 0) if saldo_val < 0 else (0, 0, 0)

                pdf.cell(22, 6, data_str, 1)
                pdf.cell(18, 6, tipo_str, 1)
                pdf.cell(33, 6, cat_val, 1)
                pdf.cell(45, 6, desc_val, 1)
                
                pdf.set_text_color(*cor_valor)
                pdf.cell(25, 6, texto_valor, 1)
                
                pdf.set_text_color(*cor_saldo)
                pdf.cell(32, 6, texto_saldo, 1)
                
                pdf.set_text_color(0, 0, 0)
                pdf.cell(25, 6, status_val, 1)
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
    # 7. EXIBIÇÃO DA TABELA NA TELA COM OS MESMOS FILTROS (VISUAL LIMPO)
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

   
    # Aplica Beneficiário na tela (Coluna J)

    # Aplica Beneficiário na tela
    if busca_benef:
        if 'df_tela' in locals() and len(df_tela.columns) > 9:
            col_benef_nome = df_tela.columns[9]
            df_tela = df_tela[df_tela[col_benef_nome].astype(str).str.contains(busca_benef, case=False, na=False)]

    # Aplica Status na tela
    if busca_status != "Todos" and col_status_df:
        df_tela = df_tela[df_tela[col_status_df].str.upper().str.strip() == str(busca_status).upper()]

    # Aplica Categoria na tela
    if 'busca_categoria' in locals() and busca_categoria != "Todas" and 'Categoria' in df_tela.columns:
        df_tela = df_tela[df_tela['Categoria'].str.upper().str.strip() == str(busca_categoria).upper()]

    # Aplica Tipo na tela
    if 'busca_tipo' in locals() and busca_tipo != "Todos" and 'Tipo' in df_tela.columns:
        df_tela = df_tela[df_tela['Tipo'].str.upper().str.strip() == str(busca_tipo).upper()]

    # --- FAXINA RIGOROSA ---
    colunas_proibidas = ['ID', 'V_Num', 'DT', 'DT_FILTRO', 'mesA', 'MESA', 'id', 'vnum', 'dt', 'mesa']
    
    colunas_visiveis = [
        c for c in df_tela.columns 
        if c not in colunas_proibidas and not c.upper().startswith('DT_')
    ]
    
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
    
    # Certifique-se de que o df_base não está vazio
    if not df_base.empty:
        # CONVERSÃO ESSENCIAL: Garante que DT seja data e V_Num seja número
        df_base['DT'] = pd.to_datetime(df_base['DT'], format='%d/%m/%Y', errors='coerce')
        df_base['V_Num'] = pd.to_numeric(df_base['V_Num'], errors='coerce').fillna(0)
        
        # Filtra apenas o que está PAGO e ordena cronologicamente
        df_saldo_dia = df_base[df_base['Status'] == 'Pago'].sort_values('DT').copy()
        
        if not df_saldo_dia.empty:
            # Aplica o sinal positivo para receitas e negativo para despesas
            df_saldo_dia['Valor_Com_Sinal'] = df_saldo_dia.apply(
                lambda x: x['V_Num'] if x['Tipo'] in ['Receita', 'Rendimento'] else -x['V_Num'], axis=1
            )
            
            # Agrupa por data real (DT)
            df_saldo_dia = df_saldo_dia.groupby('DT')['Valor_Com_Sinal'].sum().reset_index()
            
            # Calcula o Saldo Acumulado (soma cumulativa)
            df_saldo_dia['Saldo_Acumulado'] = df_saldo_dia['Valor_Com_Sinal'].cumsum()
            
            # Cria o gráfico
            import plotly.express as px
            fig_acum = px.line(
                df_saldo_dia, 
                x='DT', 
                y='Saldo_Acumulado', 
                title="Progresso do Patrimônio Acumulado no Tempo", 
                markers=True
            )
            
            # Ajusta layout para melhor leitura
            fig_acum.update_layout(height=350, margin=dict(l=20, r=20, t=50, b=20))
            fig_acum.update_xaxes(title="Data", tickformat="%d/%m/%Y")
            fig_acum.update_yaxes(title="Saldo (R$)")
            
            st.plotly_chart(fig_acum, use_container_width=True)
        else:
            st.info("Não há lançamentos marcados como 'Pago' para exibir o gráfico.")
    else:
        st.warning("A base de dados está vazia.")

    st.divider()

    # 2. COMPARATIVO: MÊS ATUAL VS MÊS ANTERIOR
    # Tratamento de segurança para evitar erro de dados vazios ou corrompidos
    df_pagos = df_base[df_base['Status'] == 'Pago'].copy()
    df_pagos = df_pagos[df_pagos['Mes_Ano'].notna()]
    meses_unicos = sorted(df_pagos['Mes_Ano'].astype(str).unique())

    # Pegamos os dois últimos meses da lista
    if len(meses_unicos) >= 2:
        mes_ant = meses_unicos[-2]
        mes_atual = meses_unicos[-1]
    elif len(meses_unicos) == 1:
        mes_ant = None
        mes_atual = meses_unicos[0]
    else:
        mes_ant, mes_atual = None, None

    with st.expander(f"📊 Comparativo de Sobra Mensal ({mes_ant or 'N/A'} vs. {mes_atual or 'Atual'})", expanded=False):
        if mes_atual:
  
            # Filtra os dados dinamicamente
            df_m1 = df_base[(df_base['Mes_Ano'] == mes_ant) & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')] if mes_ant else None
            df_m2 = df_base[(df_base['Mes_Ano'] == mes_atual) & (df_base['Categoria'] != 'Transferência') & (df_base['Status'] == 'Pago')]
            
            # Função para calcular sobra
            def calcular_sobra(df):
                if df is None or df.empty: return 0.0
                rec = df[df['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
                desp = df[df['Tipo'] == 'Despesa']['V_Num'].sum()
                return rec - desp

            sobra_m1 = calcular_sobra(df_m1)
            sobra_m2 = calcular_sobra(df_m2)
            
            var_valor = sobra_m2 - sobra_m1
            var_pct = ((sobra_m2 - sobra_m1) / abs(sobra_m1) * 100) if sobra_m1 != 0 else 0.0
            
            c_c1, c_c2, c_c3 = st.columns(3)
            c_c1.metric(f"Sobra de {mes_ant or '---'}", m_fmt(sobra_m1))
            c_c2.metric(f"Sobra de {mes_atual}", m_fmt(sobra_m2))
            c_c3.metric("Variação Líquida", m_fmt(var_valor), delta=f"{var_pct:.1f}%")
        else:
            st.write("Sem dados suficientes para o comparativo.")

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
