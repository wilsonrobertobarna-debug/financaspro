import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 10px; border: 1px solid #0056b3; }
    .saldo-container h2 { margin: 0; font-size: 2.5rem; font-weight: bold; }
    .tag-container { display: flex; justify-content: space-around; margin-bottom: 25px; gap: 10px; }
    .tag-card { flex: 1; padding: 12px; border-radius: 10px; text-align: center; color: white; font-weight: bold; font-size: 0.9rem; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    .tag-receita { background-color: #28a745; }
    .tag-despesa { background-color: #dc3545; }
    .tag-rendimento { background-color: #17a2b8; }
    .tag-pendente { background-color: #ffc107; color: #333; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO SIMPLIFICADA (EVITA O ERRO KEYERROR)
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=2)
def carregar_dados():
    try:
        # Carrega as abas principais
        df_base = conn.read(worksheet="LANCAMENTOS", ttl=0)
        df_bancos = conn.read(worksheet="Bancos", ttl=0)
        df_cats = conn.read(worksheet="Categoria", ttl=0)
        return df_bancos, df_cats, df_base
    except Exception as e:
        st.error(f"Erro ao ler planilhas: {e}")
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    if pd.isna(v) or v == "": return 0.0
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

if not df_base.empty:
    df_base.columns = [c.strip() for c in df_base.columns]
    for col in ['Data', 'Valor', 'Descrição', 'Categoria', 'Tipo', 'Banco', 'Status']:
        if col not in df_base.columns: df_base[col] = ""
    
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 3. BARRA LATERAL E NAVEGAÇÃO
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

# 4. ABA FINANÇAS (FILTROS E RESUMO)
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    
    if not df_base.empty:
        # FILTROS
        c1, c2, c3 = st.columns(3)
        with c1:
            lista_bancos = ["Todos"] + sorted(df_bancos_cad['Nome do Banco'].unique().tolist()) if not df_bancos_cad.empty else ["Todos"]
            banco_sel = st.selectbox("🔍 Banco:", lista_bancos)
        with c2:
            tipo_sel = st.selectbox("📂 Tipo:", ["Todos", "Despesa", "Receita", "Rendimento"])
        with c3:
            status_sel = st.multiselect("📌 Status:", ["Pago", "Pendente"], default=["Pago", "Pendente"])

        # Aplicar Filtros na Tabela
        df_f = df_base if banco_sel == "Todos" else df_base[df_base['Banco'] == banco_sel]
        if tipo_sel != "Todos": df_f = df_f[df_f['Tipo'] == tipo_sel]
        df_f = df_f[df_f['Status'].isin(status_sel)]

        # Cálculos para as Tags (Baseado no Banco selecionado)
        df_calc = df_base if banco_sel == "Todos" else df_base[df_base['Banco'] == banco_sel]
        receitas = df_calc[(df_calc['Tipo'] == 'Receita') & (df_calc['Status'] == 'Pago')]['V_Num'].sum()
        despesas = df_calc[(df_calc['Tipo'] == 'Despesa') & (df_calc['Status'] == 'Pago')]['V_Num'].sum()
        rendimentos = df_calc[(df_calc['Tipo'] == 'Rendimento') & (df_calc['Status'] == 'Pago')]['V_Num'].sum()
        pendentes = df_calc[df_calc['Status'] == 'Pendente']['V_Num'].sum()
        
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_valor).sum()
        saldo_final = s_ini + receitas + rendimentos - despesas

        # EXIBIÇÃO DE SALDO E TAGS
        st.markdown(f'''
            <div class="saldo-container">
                <small>Saldo Disponível ({banco_sel})</small>
                <h2>R$ {saldo_final:,.2f}</h2>
            </div>
            <div class="tag-container">
                <div class="tag-card tag-receita">Receitas<br>R$ {receitas:,.2f}</div>
                <div class="tag-card tag-despesa">Despesas<br>R$ {despesas:,.2f}</div>
                <div class="tag-card tag-rendimento">Rendimentos<br>R$ {rendimentos:,.2f}</div>
                <div class="tag-card tag-pendente">Pendências<br>R$ {pendentes:,.2f}</div>
            </div>
        '''.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        st.subheader("📋 Lançamentos Filtrados")
        st.dataframe(df_f.drop(columns=['DT', 'Mes_Ano', 'V_Num'], errors='ignore').iloc[::-1], use_container_width=True)

# 5. ABA MILO & BOLT
elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        df_p = df_base[df_base['Descrição'].str.contains('Milo|Bolt|Pet|Ração|Vet', case=False, na=False) | 
                       df_base['Categoria'].str.contains('Ração|Pet', case=False, na=False)]
        st.metric("Total Gasto", f"R$ {df_p['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_p.iloc[::-1], use_container_width=True)

# 6. GERENCIADOR (EXCLUSÃO)
st.sidebar.write("---")
if not df_base.empty:
    st.sidebar.write("### 🗑️ Apagar Linha")
    df_base['Linha'] = df_base.index + 2
    opcoes = {f"L{r['Linha']} | {r['Data']} | {r['Descrição']}": r['Linha'] for _, r in df_base.iloc[::-1].head(10).iterrows()}
    sel_del = st.sidebar.selectbox("Selecionar para excluir:", [""] + list(opcoes.keys()))
    
    if sel_del:
        if st.sidebar.button("CONFIRMAR EXCLUSÃO"):
            # Aqui você precisaria usar gspread para deletar, mas para evitar o erro de chave, 
            # foque primeiro em carregar os dados. Se carregar, resolvemos a exclusão depois.
            st.sidebar.warning("Funcionalidade de exclusão em manutenção para segurança das chaves.")
