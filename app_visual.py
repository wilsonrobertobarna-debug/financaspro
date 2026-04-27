import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from dateutil.relativedelta import relativedelta

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(page_title="FinançasPro Wilson", layout="wide", page_icon="🛡️")

st.markdown("""
    <style>
    .saldo-container { background-color: #007bff; color: white; padding: 20px; border-radius: 15px; text-align: center; margin-bottom: 25px; border: 1px solid #0056b3; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
    .saldo-container h2 { margin: 0; font-size: 2.8rem; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# 2. CONEXÃO COM GOOGLE SHEETS
@st.cache_resource
def conectar_google():
    try:
        creds_info = st.secrets["connections"]["gsheets"]
        private_key = creds_info["private_key"].replace("\\n", "\n").strip()
        final_creds = {
            "type": creds_info["type"], "project_id": creds_info["project_id"],
            "private_key_id": creds_info["private_key_id"], "private_key": private_key,
            "client_email": creds_info["client_email"], "token_uri": creds_info["token_uri"],
        }
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        return gspread.authorize(Credentials.from_service_account_info(final_creds, scopes=scopes))
    except Exception as e:
        st.error(f"Erro de Conexão: {e}"); st.stop()

client = conectar_google()
sh = client.open_by_key("147vDx908UMco7LByhOZjCGWCOoX8pEyAq-xG2BHaaU4")

# 3. CARREGAMENTO DE DADOS
@st.cache_data(ttl=5)
def carregar_dados():
    try:
        df_c = pd.DataFrame(sh.worksheet("Categoria").get_all_records())
        df_b = pd.DataFrame(sh.worksheet("Bancos").get_all_records())
        ws_base = sh.get_worksheet(0)
        dados = ws_base.get_all_values()
        if len(dados) > 1:
            df = pd.DataFrame(dados[1:], columns=dados[0])
            df.columns = [c.strip() for c in df.columns]
            return df_b, df_c, df
        return df_b, df_c, pd.DataFrame()
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

df_bancos_cad, df_cats_cad, df_base = carregar_dados()

def limpar_valor(v):
    v = str(v).replace('R$', '').replace(' ', '').replace('.', '').replace(',', '.')
    try: return float(v)
    except: return 0.0

if not df_base.empty:
    for col in ['Data', 'Valor', 'Descrição', 'Categoria', 'Tipo', 'Banco', 'Status']:
        if col not in df_base.columns: df_base[col] = ""
    df_base['V_Num'] = df_base['Valor'].apply(limpar_valor)
    df_base['DT'] = pd.to_datetime(df_base['Data'], dayfirst=True, errors='coerce')
    df_base['Mes_Ano'] = df_base['DT'].dt.strftime('%m/%y')
    mes_atual = datetime.now().strftime('%m/%y')

# 4. BARRA LATERAL
st.sidebar.title("🎮 Painel Wilson")
aba = st.sidebar.radio("Ir para:", ["💰 Finanças", "🐾 Milo & Bolt", "🚗 Meu Veículo"])

with st.sidebar.form("f_novo", clear_on_submit=True):
    st.write("### 🚀 Novo Lançamento")
    f_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
    f_val = st.number_input("Valor", min_value=0.0, step=0.01)
    f_des = st.text_input("Descrição")
    f_tip = st.selectbox("Tipo", ["Despesa", "Receita", "Rendimento"])
    f_cat = st.selectbox("Categoria", sorted(df_cats_cad['Nome'].tolist()) if not df_cats_cad.empty else ["Outros"])
    f_bnc = st.selectbox("Banco", sorted(df_bancos_cad['Nome do Banco'].tolist() + ["Dinheiro"]) if not df_bancos_cad.empty else ["Dinheiro"])
    f_sta = st.selectbox("Status", ["Pago", "Pendente"])
    f_parc = st.number_input("Parcelas", min_value=1, value=1)
    
    if st.form_submit_button("SALVAR NA PLANILHA"):
        ws = sh.get_worksheet(0)
        for i in range(int(f_parc)):
            dt_p = f_dat + relativedelta(months=i)
            desc_p = f"{f_des} ({i+1}/{int(f_parc)})" if f_parc > 1 else f_des
            ws.append_row([dt_p.strftime("%d/%m/%Y"), str(f_val).replace('.', ','), desc_p, f_cat, f_tip, f_bnc, f_sta])
        st.success("Salvo!")
        st.cache_data.clear(); st.rerun()

# 5. ABA FINANÇAS
if aba == "💰 Finanças":
    st.markdown("<h1 style='text-align: center;'>🛡️ FinançasPro Wilson</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        st.write("### 🔍 Filtros de Pesquisa")
        c_p1, c_p2, c_p3 = st.columns(3)
        with c_p1:
            banco_sel = st.selectbox("Filtrar por Banco:", ["Todos"] + sorted(df_base['Banco'].unique().tolist()))
        with c_p2:
            tipo_sel = st.selectbox("Filtrar por Tipo:", ["Todos", "Despesa", "Receita", "Rendimento"])
        with c_p3:
            status_sel = st.selectbox("Filtrar por Status:", ["Todos", "Pago", "Pendente"])

        df_f = df_base.copy()
        if banco_sel != "Todos": df_f = df_f[df_f['Banco'] == banco_sel]
        if tipo_sel != "Todos": df_f = df_f[df_f['Tipo'] == tipo_sel]
        if status_sel != "Todos": df_f = df_f[df_f['Status'] == status_sel]

        # Saldo Real
        df_pago_calc = df_base[df_base['Status'].str.strip() == 'Pago']
        if banco_sel != "Todos": df_pago_calc = df_pago_calc[df_pago_calc['Banco'] == banco_sel]
        
        s_ini = df_bancos_cad['Saldo Inicial'].apply(limpar_valor).sum() if banco_sel == "Todos" else df_bancos_cad[df_bancos_cad['Nome do Banco'] == banco_sel]['Saldo Inicial'].apply(limpar_valor).sum()
        entradas = df_pago_calc[df_pago_calc['Tipo'].isin(['Receita', 'Rendimento'])]['V_Num'].sum()
        saidas = df_pago_calc[df_pago_calc['Tipo'] == 'Despesa']['V_Num'].sum()
        
        st.markdown(f'<div class="saldo-container"><small>Saldo Atual em Conta ({banco_sel})</small><h2>R$ {s_ini + entradas - saidas:,.2f}</h2></div>'.replace(',', 'X').replace('.', ',').replace('X', '.'), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("📈 Evolução Mensal")
            df_evol = df_f.groupby(['Mes_Ano', 'Tipo'])['V_Num'].sum().unstack().fillna(0).reset_index()
            fig = go.Figure()
            for t, cor in zip(['Receita', 'Despesa', 'Rendimento'], ['#28a745', '#dc3545', '#007bff']):
                if t in df_evol.columns: fig.add_trace(go.Bar(x=df_evol['Mes_Ano'], y=df_evol[t], name=t, marker_color=cor))
            fig.update_layout(barmode='group', height=350, margin=dict(l=0,r=0,t=20,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📊 Resumo de Economia")
            df_mes_atual = df_f[df_f['Mes_Ano'] == mes_atual]
            gastos_por_cat = df_mes_atual[df_mes_atual['Tipo'] == 'Despesa'].groupby('Categoria')['V_Num'].sum()
            total_gasto_mes = gastos_por_cat.sum()
            
            if total_gasto_mes > 0:
                labels = [f"{cat}: R$ {val:,.2f} ({(val/total_gasto_mes)*100:.1f}%)" for cat, val in gastos_por_cat.items()]
                fig_resumo = go.Figure(data=[go.Pie(labels=labels, values=gastos_por_cat.values, hole=.4, textinfo='percent')])
                fig_resumo.update_layout(height=350, showlegend=True, legend=dict(orientation="h", y=-0.5))
                st.plotly_chart(fig_resumo, use_container_width=True)
            else:
                st.info("Sem despesas este mês.")

        st.write("---")
        st.subheader("📋 Tabela de Lançamentos")
        st.dataframe(df_f.drop(columns=['DT', 'Mes_Ano', 'V_Num', 'Linha'], errors='ignore').iloc[::-1], use_container_width=True)

# 6. ABA MILO & BOLT (CORRIGIDA)
elif aba == "🐾 Milo & Bolt":
    st.markdown("<h1 style='text-align: center;'>🐾 Milo & Bolt</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        # Busca por termos chave na Descrição OU na Categoria
        palavras_chave = 'Milo|Bolt|Pet|Ração|Veterinário|Banho|Tosa|Cachorro'
        df_pets = df_base[
            df_base['Descrição'].str.contains(palavras_chave, case=False, na=False) | 
            df_base['Categoria'].str.contains(palavras_chave, case=False, na=False)
        ].copy()
        
        st.metric("Total Investido nos Pets", f"R$ {df_pets['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_pets.drop(columns=['DT', 'Mes_Ano', 'V_Num', 'Linha'], errors='ignore').iloc[::-1], use_container_width=True)

elif aba == "🚗 Meu Veículo":
    st.markdown("<h1 style='text-align: center;'>🚗 Meu Veículo</h1>", unsafe_allow_html=True)
    if not df_base.empty:
        palavras_veic = 'Veículo|Carro|Combustível|IPVA|Manutenção|Oficina|Gasolina|Etanol'
        df_veic = df_base[
            df_base['Descrição'].str.contains(palavras_veic, case=False, na=False) | 
            df_base['Categoria'].str.contains('Veículo|Transporte', case=False, na=False)
        ].copy()
        st.metric("Total Gasto com Veículo", f"R$ {df_veic['V_Num'].sum():,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.'))
        st.dataframe(df_veic.drop(columns=['DT', 'Mes_Ano', 'V_Num', 'Linha'], errors='ignore').iloc[::-1], use_container_width=True)

# 7. GERENCIADOR
st.sidebar.write("---")
st.sidebar.write("### ⚙️ Gerenciar Linhas")
if not df_base.empty:
    df_base['Linha'] = df_base.index + 2
    opcoes_manag = {f"L{r['Linha']} | {r['Data']} | {r['Descrição']}": r['Linha'] for _, r in df_base.iloc[::-1].head(15).iterrows()}
    sel = st.sidebar.selectbox("Ação rápida:", [""] + list(opcoes_manag.keys()))
    if sel:
        l_alvo = opcoes_manag[sel]
        c1, c2 = st.sidebar.columns(2)
        if c1.button("🗑️ APAGAR"):
            sh.get_worksheet(0).delete_rows(int(l_alvo))
            st.cache_data.clear(); st.rerun()
        if c2.button("✅ PAGO"):
            sh.get_worksheet(0).update_cell(int(l_alvo), 7, "Pago")
            st.cache_data.clear(); st.rerun()
