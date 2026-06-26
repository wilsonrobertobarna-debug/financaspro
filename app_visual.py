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

# --- INICIALIZAÇÃO DE VARIÁVEIS (Para evitar o NameError) ---
if 'busca_desc' not in locals(): busca_desc = ""
if 'busca_beneficiario' not in locals(): busca_beneficiario = ""
if 'busca_status' not in locals(): busca_status = "Todos"
if 'busca_tipo' not in locals(): busca_tipo = "Todos"

# --- TELA DE PROTEÇÃO (LOGIN) ---
if 'login' not in st.session_state:
    st.session_state.login = False

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
    st.cache_data.clear() # <--- ADICIONE ESTA LINHA AQUI!
    st.rerun()

st.sidebar.divider()

# Inicializa a página se não existir
#if 'page' not in st.session_state:    
    
    # --- PAINEL MESTRE (DOIS EM UM) --- 
#with st.expander("📊 Clique aqui para ver o Painel e Relatório Bancário", expanded=False):
with st.expander("📊 Painel Financeiro", expanded=False):
    
        # 1. Painel Financeiro
        st.markdown("### 🏦 Painel Financeiro")
        entradas_totais = df_base[df_base['Tipo'].isin(['Receita', 'Rendimentos'])]['V_Num'].sum()
        saidas_totais = df_base[df_base['Tipo'].isin(['Despesa', 'Pendências'])]['V_Num'].sum()
        saldo_real = entradas_totais - saidas_totais
    
        c1, c2, c3 = st.columns(3)
        c1.metric("Entradas", f"R$ {entradas_totais:,.2f}")
        c2.metric("Saídas", f"R$ {saidas_totais:,.2f}")
        c3.metric("SALDO REAL", f"R$ {saldo_real:,.2f}", delta_color="inverse")
    
        st.divider() # Uma linha para separar

# --- AQUI COMEÇA O SEU CÓDIGO DAS ABAS ---
# Em vez de usar "if "Pendências" in aba:", use:
if st.session_state.get('page') == 'Pendências':
    st.title("📋 Lançamentos Pendentes")


# Define os itens do menu
menu_itens = ["💰 Finanças & Bancos", "Pendências", "🐾 Milo & Bolt", "🚗 Meu Veículo", "📄 WhatsApp", "📋 Relatório PDF", "📊 Análises & Configurações"]

# Cria os botões na sidebar com a função de fechar
# Seu loop de botões na sidebar agora fica assim:
for item in menu_itens:
    if st.sidebar.button(item, use_container_width=True):
        st.session_state.page = item
        st.rerun() # Removemos o fechar_sidebar() daqui    
 
st.sidebar.divider()

# --- BLOCO DE SEGURANÇA ---
if 'page' not in st.session_state:
    st.session_state['page'] = 'Home'  # Define o valor inicial se não existir

aba = st.session_state['page'] # Agora ele não vai mais dar erro, pois garantimos que existe

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
        f_des = st.text_input("Descrição")
        f_ben = st.text_input("Beneficiário") # Nova caixa dedicada
        f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
        f_cat = st.selectbox("Categoria", ["Mercado", "Aluguel", "Luz/Água","Assinatura","Rendimento","Aplicação","Restaurante","Celular","Anuidade","Seguro", "Internet","Vestuário","Salário","Reembolso","Moradia", "Saúde","Taxas","Depósito","Plano Assistencial","Transporte","Previdência","Outros", "Pet: Milo", "Pet: Bolt", "Veículo", "Combustível", "Manutenção"])
        f_bnc = st.selectbox("Banco", bancos_disponiveis)
        f_sta = st.selectbox("Status", ["Pago", "Pendente"])
        
        
        # Garante que a variável exista para evitar o NameError
        f_venc_cartao = None 

        # ... (após todos os st.selectbox e inputs do formulário)

        if st.form_submit_button("Salvar Lançamento"):
            # 1. BUSCAR O MAIOR ID DIRETO NA PLANILHA (Sem depender de variáveis externas)
            # Pegamos todos os valores da aba
            todos_dados = ws_base.get_all_records()
            
            if todos_dados:
                # Transformamos em um DataFrame temporário só para achar o maior ID
                import pandas as pd
                df_temp = pd.DataFrame(todos_dados)
                
                # Se a coluna ID existir, pegamos o maior + 1, senão começa em 1
                if 'ID' in df_temp.columns and not df_temp['ID'].isna().all():
                    proximo_id = int(df_temp['ID'].max()) + 1
                else:
                    proximo_id = 1
            else:
                proximo_id = 1

            # 2. Formatações
            v_str = f"{f_val:.2f}".replace('.', ',')
            t_dat_str = t_dat.strftime("%d/%m/%Y")
            f_compra_str = f_compra.strftime("%d/%m/%Y")
            
            # 3. Salvar as parcelas
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
                    f_compra_str,                   # Coluna H: Data da Compra
                    proximo_id + i,                 # Coluna I: ID (Agora sem pular coluna!)
                    f_ben                           # Coluna J: Beneficiário 
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
            t_dest = st.selectbox("Destino (Entra):", bancos_disponiveis)
            t_desc = st.text_input("Nota")
            if st.form_submit_button("TRANSFERIR"):
                if t_orig == t_dest: 
                    st.error("Escolha bancos diferentes!")
                else:
                    v_str = f"{t_val:.2f}".replace('.', ',')
                    d_str = t_dat.strftime("%d/%m/%Y")
                    ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Despesa", t_orig, "Pago", ""])
                    ws_base.append_row([d_str, v_str, f"TR: {t_desc}", "Transferência", "Receita", t_dest, "Pago", ""])
                    st.toast("✅ Transferencia realizada com sucesso!", icon="💰")
                    atualizar_sessao()
                    st.rerun()

               # --- BARRINHA 3: AJUSTE / EXCLUSÃO ---
with st.sidebar.expander("⚙️ Ajustar Lançamento", expanded=False):
    if not df_base.empty:
        lista_edit = {f"ID {r['ID']} ! {r['Vencimento']} ! {r['Descrição']} ! R$ {r['Valor']}": r for _, r in df_base.iloc[::-1].iterrows()}
        
        # Usamos uma key para o selectbox para podermos controlá-lo
        escolha = st.selectbox("Selecione para Alterar/Excluir:", [""] + list(lista_edit.keys()), key="selectbox_ajuste")
        
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
                st.toast("✅ Lançamento Atualizado!", icon="💰")
                
                # Zera o seletor antes de recarregar
                if "selectbox_ajuste" in st.session_state:
                    del st.session_state["selectbox_ajuste"]
                #st.session_state["selectbox_ajuste"] = ""
                atualizar_sessao()
                st.rerun()
                
            if col_ed2.button("🚨 EXCLUIR"):
                if item['Categoria'] == 'Transferência':
                    ids_para_excluir = []
                    for idx, row in df_base.iterrows():
                        mesma_data = (row['Vencimento'] == item['Vencimento'])
                        mesmo_valor = (abs(row['V_Num'] - item['V_Num']) < 0.01)
                        mesma_desc = (row['Descrição'] == item['Descrição'])
                        eh_transf = (row['Categoria'] == 'Transferência')
                        
                        if mesma_data and mesmo_valor and mesma_desc and eh_transf:
                            ids_para_excluir.append(int(row['ID']))
                    
                    for id_linha in sorted(list(set(ids_para_excluir)), reverse=True):
                        ws_base.delete_rows(id_linha)
                else:
                    ws_base.delete_rows(int(item['ID']))
                
                st.toast("✅ Exclusão realizada com sucesso!", icon="💰")
                # Zera o seletor antes de recarregar
                if "selectbox_ajuste" in st.session_state:
                    del st.session_state["selectbox_ajuste"]
                st.session_state["selectbox_ajuste"] = ""
                atualizar_sessao()
                st.rerun()

# --- INÍCIO DA ABA: 💰 Finanças & Bancos (COM GRÁFICO DE METAS) ---
if "💰" in st.session_state.page:
    import plotly.graph_objects as go # Garante que o gráfico de metas funcione
    
    st.markdown("""<style>.block-container { padding-top: 0rem; padding-bottom: 0rem; }</style>""", unsafe_allow_html=True)
    st.subheader("🛡️ FinançasPro Wilson")

    # 1. BARRINHA DE MESES
    meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
    mes_atual = st.pills("Período:", meses, selection_mode="single", default="Jun")

    if not df_base.empty:
        # 2. TRADUÇÃO DO FILTRO (Converte "Jun" para "06/26")
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
            st.write("### 📊 Fluxo Mensal")
            df_f = df_m_limpo.groupby(['Tipo'])['V_Num'].sum().reset_index()
            if not df_f.empty:
                st.plotly_chart(px.bar(df_f, x='Tipo', y='V_Num', color='Tipo'), use_container_width=True)
                

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
        df_comp['Vencimento'] = pd.to_datetime(df_comp['Vencimento'], dayfirst=True)
        
        # 3. Filtrar apenas os dois meses necessários
        df_comp = df_comp[df_comp['Vencimento'].dt.month.isin([mes_anterior_num, mes_atual_num])].copy()
        
        # 4. Tabela dinâmica
        df_pivot = df_comp[df_comp['Tipo'] == 'Despesa'].pivot_table(
            index='Categoria', 
            columns=df_comp['Vencimento'].dt.month, 
            values='V_Num', 
            aggfunc='sum'
        ).fillna(0)
        
        # Renomeia as colunas para o que aparece na tela
        colunas_renomeadas = {mes_anterior_num: "Mês Anterior", mes_atual_num: "Mês Atual"}
        df_pivot = df_pivot.rename(columns=colunas_renomeadas)
        
        # 5. Cálculo da variação (seguro)
        if "Mês Anterior" in df_pivot.columns and "Mês Atual" in df_pivot.columns:
            df_pivot['Variação (%)'] = ((df_pivot["Mês Atual"] - df_pivot["Mês Anterior"]) / df_pivot["Mês Anterior"] * 100).replace([float('inf'), -float('inf')], 0).fillna(0)
        
        # 6. Exibir
        #st.dataframe(df_pivot.style.format("{:.2f}"), use_container_width=True)


        # --- EXIBIÇÃO FORMATADA ---

        # Vamos criar um dicionário de formatação para aplicar estilos diferentes em colunas diferentes
        formatacao = {
            "Mês Anterior": "{:.2f}",
            "Mês Atual": "{:.2f}",
            "Variação (%)": "{:.2f}%"  # Adicionamos o símbolo de % aqui!
        }
        
        # Aplicamos o estilo (o .style.format aplica o que definimos no dicionário)
        st.dataframe(df_pivot.style.format(formatacao), use_container_width=True)
        
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
        # 7. TABELA FINAL
        st.subheader("🔍 Lançamentos do Mês")
        
        if not df_m_limpo.empty:
            df_exibicao = df_m_limpo.copy()
            
            # AJUSTE DE MENTOR: 
            # Se você sente que a diferença é de 2, mudamos aqui.
            # Se precisar ajustar para mais ou para menos, é só mudar este número '2'.
            ajuste = 2 
            df_exibicao['Seq.'] = df_exibicao.index + ajuste 
            
            # Inverte para mostrar os mais novos no topo
            df_exibicao = df_exibicao.iloc[::-1]
            
            st.dataframe(df_exibicao[['Seq.', 'Vencimento', 'Descrição', 'Valor', 'Categoria', 'Banco', 'Status']], 
                         use_container_width=True, 
                         hide_index=True)
        else:
            st.warning("Base de dados vazia.")
elif "Pendências" in aba:
    #st.title("📋 Lançamentos Pendentes")
    
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

   
    # 2. FILTRAGEM (INCLUINDO NOVOS FILTROS)
    # ========================================================
    # ... (seu código de data e banco continua igual aqui em cima) ...

    # --- BLOCO DE FILTROS SEGURO E COM CHAVES ÚNICAS ---
    st.subheader("Filtros")
    col_rel3, col_rel4, col_rel5 = st.columns(3)
    
    # Descrição
    busca_desc = col_rel3.text_input("📝 Descrição:", value=st.session_state.get('busca_desc', ""), key="input_desc")
    st.session_state.busca_desc = busca_desc
    
    # Beneficiário
    busca_beneficiario = col_rel4.text_input("👤 Beneficiário:", value=st.session_state.get('busca_beneficiario', ""), key="input_benef")
    st.session_state.busca_beneficiario = busca_beneficiario
    
    # Status
    opcoes_status = ["Todos", "Pago", "Pendente"]
    idx_status = opcoes_status.index(st.session_state.get('busca_status', "Todos"))
    busca_status = col_rel5.selectbox("📌 Status:", opcoes_status, index=idx_status, key="sel_status")
    st.session_state.busca_status = busca_status
    
    # -------------------------------------------------------------------------
    # LINHA DE FILTRO: TIPO (ÚNICA E CORRETA)
    # -------------------------------------------------------------------------
    col_rel6, col_rel7 = st.columns([1, 2])
    
    opcoes_tipo = ["Todos", "Receita", "Despesa", "Rendimento"]
    # Se o valor não estiver no estado, ele usa "Todos" como padrão
    valor_atual = st.session_state.get('busca_tipo', "Todos")
    
    # Garantia para o index não quebrar se o valor mudar
    idx_tipo = opcoes_tipo.index(valor_atual) if valor_atual in opcoes_tipo else 0
    
    busca_tipo = col_rel6.selectbox("🏷️ Filtrar por Tipo:", opcoes_tipo, index=idx_tipo, key="sel_tipo")
    st.session_state.busca_tipo = busca_tipo    
    # -------------------------------------------------------------------------
    # FILTRO: BENEFICIÁRIO (NA LATERAL)
    # -------------------------------------------------------------------------
     
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
            if st.session_state.get('busca_tipo') != "Todos":
                df_report = df_report[df_report['Tipo'].str.upper().str.strip() == st.session_state.busca_tipo.upper()]

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
            # 5. MONTAGEM DO CABEÇALHO DO PDF (ATUALIZADO)
            # ========================================================
            pdf.set_font("Arial", 'B', 12)
            pdf.cell(200, 10, txt="RELATORIO DE LANCAMENTOS - FINANCASPRO", ln=1, align="C")
            pdf.ln(2)
            
            pdf.set_font("Arial", '', 10)
            p_inicio = b_ini.strftime('%d/%m/%Y')
            p_fim = b_fim.strftime('%d/%m/%Y')
            
            # --- LOGICA DE FILTROS DO CABEÇALHO ---
            pdf.set_font("Arial", 'B', 10)
            if busca_beneficiario:
                pdf.cell(200, 6, txt=f"BENEFICIARIO FILTRADO: {str(busca_beneficiario).upper()}", ln=1, align="L")
            else:
                pdf.cell(200, 6, txt=f"BANCO SELECIONADO: {str(banco_nome).upper()}", ln=1, align="L")
                if busca_tipo:
                    pdf.cell(200, 6, txt=f"TIPO FILTRADO: {str(busca_tipo).upper()}", ln=1, align="L")
            
            pdf.cell(200, 6, txt=f"PERIODO DO RELATORIO: {p_inicio} ate {p_fim}", ln=1, align="L")
            pdf.ln(5)

      
            # ========================================================
            # FILTRO CORRIGIDO (USANDO NOMES DAS COLUNAS)
            # ========================================================
            df_report = df_base.copy()
            
            # 1. Filtro de Data (Coluna 'DT')
            df_report['DT'] = pd.to_datetime(df_report['DT'], format='%d/%m/%Y', errors='coerce')
            df_report = df_report[(df_report['DT'] >= pd.to_datetime(b_ini)) & (df_report['DT'] <= pd.to_datetime(b_fim))]
            
            # 2. Filtro de Banco (Coluna 'Banco' é a número 5)
            if banco_nome and str(banco_nome).lower() != "todos os bancos":
                # Filtra pela coluna 'Banco' usando .contains
                df_report = df_report[df_report['Banco'].astype(str).str.contains(str(banco_nome).strip(), case=False, na=False)]
            
            # 3. Filtro de Beneficiário (Coluna 'Beneficiário' é a número 9)
            if busca_beneficiario and str(busca_beneficiario).strip() != "":
                df_report = df_report[df_report['Beneficiário'].astype(str).str.contains(str(busca_beneficiario).strip(), case=False, na=False)]
            
            # 4. Ajustes de valores e ordenação
            df_report['V_Num'] = pd.to_numeric(df_report['V_Num'], errors='coerce').fillna(0)
            df_report = df_report.sort_values(by='DT')
            
            # 5. Saldo Acumulado (usando o valor inicial + cumsum)
            valor_inicial = float(saldo_anterior) 
            df_report['Valor_Com_Sinal'] = df_report.apply(
                lambda x: x['V_Num'] if str(x['Tipo']).strip() in ['Receita', 'Rendimento'] else -x['V_Num'], axis=1
            )
            df_report['Saldo_Acum'] = valor_inicial + df_report['Valor_Com_Sinal'].cumsum()
                
           
            # ========================================================
            # 6. LOOP DE IMPRESSÃO DAS LINHAS NO PDF (ATUALIZADO)
            # ========================================================
            
            # Cabeçalho da Tabela - Adicionamos a coluna "BANCO"
            pdf.set_font("Arial", 'B', 8) # Fonte ligeiramente menor para caber tudo
            pdf.cell(20, 7, "DATA", 1)
            pdf.cell(25, 7, "BANCO", 1)  # <--- NOVA COLUNA AQUI
            pdf.cell(18, 7, "TIPO", 1)
            pdf.cell(30, 7, "CATEGORIA", 1)
            pdf.cell(35, 7, "DESCRIÇÃO", 1)
            pdf.cell(22, 7, "VALOR", 1)
            pdf.cell(25, 7, "SALDO", 1)
            pdf.cell(15, 7, "STATUS", 1)
            pdf.ln()

            
            # --- LOOP DE IMPRESSÃO DAS LINHAS ---
            pdf.set_font("Arial", '', 8) # Reduzi um pouco a fonte para caber a nova coluna
            for index, row in df_report.iterrows():
                # Formatações
                # Tenta pegar a data de DT_FILTRO, se não existir, tenta pegar de DT
                if 'DT_FILTRO' in row and not pd.isna(row['DT_FILTRO']):
                    data_str = row['DT_FILTRO'].strftime('%d/%m/%Y')
                elif 'DT' in row and not pd.isna(row['DT']):
                    data_str = pd.to_datetime(row['DT']).strftime('%d/%m/%Y')
                else:
                    data_str = '---'
                # AQUI ESTÁ O BANCO: buscamos no dicionário da linha 'row'
                banco_str = str(row.get('Banco', '-'))[:12] 
                tipo_str = str(row.get('Tipo', '---')).strip()
                cat_val = str(row.get('Categoria', 'Geral'))[:15]
                desc_val = str(row.get('Descrição', row.get('Descricao', 'Sem nome')))[:20]
                valor_val = pd.to_numeric(row.get('V_Num', row.get('Valor', 0)), errors='coerce')
                if pd.isna(valor_val): valor_val = 0.0
                saldo_val = row.get('Saldo_Acum', 0.0)
                status_val = str(row.get('Status', '-'))

                # Lógica de cores
                if "DESPESA" in tipo_str.upper() or "GASTO" in tipo_str.upper():
                    texto_valor = f"- R$ {valor_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (255, 0, 0)
                else:
                    texto_valor = f"R$ {valor_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                    cor_valor = (0, 0, 0)

                texto_saldo = f"R$ {saldo_val:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')
                cor_saldo = (255, 0, 0) if saldo_val < 0 else (0, 0, 0)

                # Impressão das colunas (ADICIONAMOS A CÉLULA DO BANCO AQUI)
                pdf.cell(20, 6, data_str, 1)
                pdf.cell(25, 6, banco_str, 1) # <--- NOVA COLUNA BANCO
                pdf.cell(18, 6, tipo_str, 1)
                pdf.cell(30, 6, cat_val, 1)
                pdf.cell(35, 6, desc_val, 1)
                
                pdf.set_text_color(*cor_valor)
                pdf.cell(22, 6, texto_valor, 1)
                
                pdf.set_text_color(*cor_saldo)
                pdf.cell(28, 6, texto_saldo, 1)
                
                pdf.set_text_color(0, 0, 0)
                pdf.cell(15, 6, status_val, 1)
                pdf.ln()

            # Finalização e Download
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

    # (Este código abaixo fica FORA de qualquer bloco de erro, alinhado à esquerda)
    # =========================================================================
    # 7. EXIBIÇÃO DA TABELA NA TELA
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

    # ... (seu código atual de filtros de Data, Banco, Descrição e Status continua aqui) ...

    # --- INSERIR ESTES FILTROS AQUI (APÓS O FILTRO DE STATUS) ---
    
    # Filtra Beneficiário (Coluna J = índice 9)
    if st.session_state.get('busca_beneficiario'):
        # Verifica se tem pelo menos 10 colunas para não dar erro de índice
        if df_tela.shape[1] > 9:
            df_tela = df_tela[df_tela.iloc[:, 9].astype(str).str.contains(st.session_state.busca_beneficiario, case=False, na=False)]

    # Filtra Tipo
    if st.session_state.get('busca_tipo') != "Todos":
        df_tela = df_tela[df_tela['Tipo'].str.upper().str.strip() == st.session_state.busca_tipo.upper()]

    # --- (A PARTIR DAQUI SEGUE A FAXINA DAS COLUNAS) ---
    # Faxina das colunas internas para manter o visual limpo
    colunas_para_esconder = ['ID', 'V_Num', 'DT', 'DT_FILTRO', 'mesA', 'MESA', 'id', 'vnum', 'dt', 'mesa']
    colunas_visiveis = [c for c in df_tela.columns if c not in colunas_para_esconder]
    df_tela_limpo = df_tela[colunas_visiveis]

        # Exibe os dados
       # 1. Caixa de busca (o usuário digita aqui)
    busca_beneficiario = st.text_input("🔍 Pesquisar por Beneficiário:")
    
    # 2. Se algo foi digitado, filtramos o df_tela_limpo antes de exibir
    if busca_beneficiario:
        # Lembre-se: o 9 é a coluna J (Beneficiário)
        df_tela_limpo = df_tela_limpo[df_tela_limpo.iloc[:, 9].astype(str).str.contains(busca_beneficiario, case=False, na=False)]
    
    # 3. AGORA SIM, o código que você já tinha:
    if not df_tela_limpo.empty:
        st.dataframe(df_tela_limpo, use_container_width=True)
    else:
        st.info("Nenhum lançamento encontrado para os filtros aplicados.")

# --- O RESTO DO SEU CÓDIGO (ABA DE ANÁLISES) CONTINUA IGUAL ---# =========================================================================
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
    # Primeiro, criamos uma lista de meses únicos presentes na base (ordenados)
    meses_unicos = sorted(df_base[df_base['Status'] == 'Pago']['Mes_Ano'].unique())
    
    # Pegamos os dois últimos meses da lista
    if len(meses_unicos) >= 2:
        mes_ant = meses_unicos[-2]
        mes_atual = meses_unicos[-1]
    elif len(meses_unicos) == 1:
        mes_ant = None
        mes_atual = meses_unicos[0]
    else:
        mes_ant, mes_atual = None, None

    with st.expander(f"📊 Comparativo de Sobra Mensal ({mes_ant or 'N/A'} vs. {mes_atual or 'Atual'})", expanded=True):
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
