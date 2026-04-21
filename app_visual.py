import streamlit as st
import pandas as pd
import os
import smtplib
import urllib.parse
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fpdf import FPDF

# --- CONFIGURAÇÃO DE ACESSO ---
SENHA_ACESSO = "1234"

if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

def tela_login():
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.subheader("🔐 Acesso FinançasPro")
        senha = st.text_input("Senha:", type="password", key="login_pass")
        if st.button("Entrar", key="btn_login"):
            if senha == SENHA_ACESSO:
                st.session_state.autenticado = True
                st.rerun()
            else: st.error("Incorreta!")
    st.stop()

if not st.session_state.autenticado: tela_login()

# --- 1. BANCO DE DADOS ---
ARQ_D, ARQ_B, ARQ_C, ARQ_M = "financas_bruta.csv", "bancos_matilha.csv", "cartoes_matilha.csv", "metas_categorias.csv"
ENC = 'utf-8-sig'

def ler_dados(arq, colunas):
    if os.path.exists(arq):
        try:
            df = pd.read_csv(arq, sep=';', encoding=ENC)
            if df.empty: return pd.DataFrame(columns=colunas)
            for col in colunas:
                if col not in df.columns: df[col] = None
            if 'Data' in df.columns:
                df['DT'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
                df['DT'] = df['DT'].fillna(pd.Timestamp('2000-01-01'))
            if 'Valor' in df.columns:
                df['Valor'] = pd.to_numeric(df.Valor.astype(str).str.replace(',', '.'), errors='coerce').fillna(0.0)
            return df[colunas + (['DT'] if 'Data' in colunas else [])]
        except: return pd.DataFrame(columns=colunas)
    return pd.DataFrame(columns=colunas)

def salvar_dados(df, arq):
    df_s = df.copy()
    if 'DT' in df_s.columns: df_s = df_s.drop(columns=['DT'])
    df_s.to_csv(arq, index=False, sep=';', encoding=ENC)

def formatar_br(v):
    return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def enviar_email_wilson(destinatario, senha_app, resumo):
    if not destinatario or not senha_app:
        return False, "Preencha o Gmail e a Senha de App na lateral!"
    msg = MIMEMultipart()
    msg['From'] = destinatario
    msg['To'] = destinatario
    msg['Subject'] = f"RELATÓRIO WILSON - {date.today().strftime('%d/%m/%Y')}"
    corpo = f"""RELATÓRIO WILSON - DETALHADO
Período: {resumo['inicio']} a {resumo['fim']}
========================================
RESUMO DO PERÍODO:
REC: {formatar_br(resumo['rec'])}
DES: {formatar_br(resumo['des'])}
REND: {formatar_br(resumo['rend'])}
SOBRA: {formatar_br(resumo['sobra'])}
========================================
SALDO NAS CONTAS:
{resumo['detalhe_bancos']}
========================================
DÍVIDA EM CARTÕES:
{resumo['detalhe_cartoes']}
========================================
PATRIMÔNIO LÍQUIDO: {formatar_br(resumo['patrimonio'])}
"""
    msg.attach(MIMEText(corpo, 'plain'))
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(destinatario, senha_app.replace(" ", ""))
        server.sendmail(destinatario, destinatario, msg.as_string())
        server.quit()
        return True, "E-mail enviado com sucesso!"
    except Exception as e: return False, f"Erro: {str(e)}"

def gerar_pdf_custom(df_completo, df_filtrado, titulo_rel, periodo_txt, dt_inicial, df_bancos):
    pdf = FPDF()
    pdf.add_page(); pdf.set_font("Arial", "B", 16)
    pdf.cell(190, 10, f"RELATORIO: {titulo_rel.upper()}", 0, 1, "C")
    if "Banco:" in titulo_rel:
        bco_sel = titulo_rel.replace("Banco: ", "").strip()
        saldo_base = df_bancos[df_bancos['Banco'].str.strip() == bco_sel]['Limite'].sum()
    else: saldo_base = df_bancos['Limite'].sum()
    df_ant = df_completo[(df_completo['DT'].dt.date < dt_inicial) & (df_completo['Status'] == "✅ Pago")]
    if "Banco:" in titulo_rel: df_ant = df_ant[df_ant['Pagamento'].str.strip() == bco_sel]
    e_ant = df_ant[df_ant['Tipo'].str.contains("Receita|Rend")]['Valor'].sum()
    s_ant = df_ant[df_ant['Tipo'].str.contains("Despesa")]['Valor'].sum()
    
    saldo_roda = saldo_base + e_ant - s_ant
    pdf.set_font("Arial", "I", 10); pdf.cell(190, 8, f"Saldo Inicial em {dt_inicial.strftime('%d/%m/%Y')}: {formatar_br(saldo_roda)}", 0, 1, "L"); pdf.ln(5)
    
    pdf.set_fill_color(200, 220, 255); pdf.set_font("Arial", "B", 8)
    cols = [("Data",25), ("Categoria",35), ("Beneficiario",50), ("Valor",35), ("Saldo do Dia",45)]
    for c, w in cols: pdf.cell(w, 8, c, 1, 0, "C", 1)
    pdf.ln(); pdf.set_font("Arial", "", 8)

    df_pdf = df_filtrado.sort_values(by="DT").reset_index(drop=True)
    total_linhas = len(df_pdf)

    for i, row in df_pdf.iterrows():
        v = float(row['Valor'])
        if "Receita" in str(row['Tipo']) or "Rendimento" in str(row['Tipo']):
            saldo_roda += v; txt_v = f"+ {formatar_br(v)}"
        else:
            saldo_roda -= v; txt_v = f"- {formatar_br(v)}"
        
        pdf.cell(25, 7, str(row['Data']), 1)
        pdf.cell(35, 7, str(row['Categoria'])[:18], 1)
        pdf.cell(50, 7, str(row['Beneficiário'])[:25], 1)
        pdf.cell(35, 7, txt_v, 1, 0, "R")
        
        # LOGICA DO SALDO POR DIA:
        # Só imprime se for a última linha OU se a data da próxima linha for diferente
        if i == total_linhas - 1 or df_pdf.loc[i+1, 'Data'] != row['Data']:
            pdf.set_font("Arial", "B", 8)
            pdf.cell(45, 7, formatar_br(saldo_roda), 1, 1, "R")
            pdf.set_font("Arial", "", 8)
        else:
            pdf.cell(45, 7, "", 1, 1, "R") # Deixa vazio se não for o fim do dia
        
    pdf.ln(5); pdf.set_font("Arial", "B", 10); pdf.cell(145, 10, "SALDO FINAL NO PERÍODO:", 0, 0, "R"); pdf.cell(45, 10, formatar_br(saldo_roda), 0, 1, "R")
    return bytes(pdf.output(dest='S'))

# --- 2. SETUP DA PÁGINA ---
st.set_page_config(page_title="FinançasPro Wilson V601", layout="wide")
df_g = ler_dados(ARQ_D, ['Data', 'Tipo', 'Categoria', 'Valor', 'Pagamento', 'Beneficiário', 'Status', 'KM', 'Descrição'])
df_b = ler_dados(ARQ_B, ['Banco', 'Limite'])
df_c = ler_dados(ARQ_C, ['Cartão', 'Limite', 'Fechamento', 'Vencimento'])
df_m = ler_dados(ARQ_M, ['Categoria', 'Meta'])

hoje = date.today()
lista_contas = sorted(list(set(["Dinheiro", "Pix"] + df_b['Banco'].dropna().tolist() + df_c['Cartão'].dropna().tolist())))
lista_cats = sorted(list(set(["Mercado", "Ração", "Combustível", "Saúde", "Lazer", "Outros", "Transferência"] + df_m['Categoria'].dropna().tolist())))

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=80)
    st.title("🔐 Wilson Barna")
    mail_u = st.text_input("Gmail:", key="m_u"); mail_p = st.text_input("Senha App:", type="password", key="m_p")
    whats_u = st.text_input("WhatsApp (ex: 5511...):", key="w_u")
    if st.button("Sair"): st.session_state.autenticado = False; st.rerun()

st.markdown("<h1 style='text-align: center; color: #2E86C1;'>🐾 FinançasPro Wilson - V601</h1>", unsafe_allow_html=True)
tab_l, tab_b, tab_e, tab_gerenciar, tab_config = st.tabs(["💰 Lançar", "✅ Baixas / Transf", "📋 Extrato & E-mail", "🗑️ Gerenciar", "⚙️ Gestão Total"])

with tab_l:
    with st.container(border=True):
        c1, c2 = st.columns(2)
        dt_l = c1.date_input("Data:", hoje, key="l_dt")
        tipo = c2.radio("Tipo:", ["🔴 Despesa", "🟢 Receita", "💎 Rendimento"], key="l_tp", horizontal=True)
        c3, c4 = st.columns(2)
        conta = c3.selectbox("Conta:", lista_contas, key="l_cta")
        benef_l = c4.text_input("Beneficiário:", key="l_ben")
        c5, c6, c7 = st.columns([2, 2, 1])
        cat = c5.selectbox("Categoria:", lista_cats, key="l_cat")
        valor = c6.number_input("Valor:", 0.0, key="l_val")
        parc = c7.number_input("Parc:", 1, 48, 1, key="l_parc")
        c8, c9 = st.columns(2)
        status = c8.selectbox("Status:", ["⏳ Pendente", "✅ Pago"], key="l_st")
        km = c9.number_input("KM:", 0, key="l_km")
        desc = st.text_area("Descrição:", key="l_desc", height=70)
        
        if st.button("🚀 GRAVAR LANÇAMENTO", key="btn_gravar", use_container_width=True):
            novos = []
            for i in range(parc):
                dt_p = dt_l + timedelta(days=i*30)
                novos.append({"Data": dt_p.strftime('%d/%m/%Y'), "Tipo": tipo, "Categoria": cat, "Valor": valor/parc, "Pagamento": conta, "Beneficiário": f"{benef_l} ({i+1}/{parc})" if parc > 1 else benef_l, "Status": status if i == 0 else "⏳ Pendente", "KM": km, "Descrição": desc})
            df_g = pd.concat([df_g, pd.DataFrame(novos)], ignore_index=True)
            salvar_dados(df_g, ARQ_D)
            st.rerun()

with tab_b:
    st.subheader("✅ Baixas")
    busca_bco = st.selectbox("🔍 Procurar Banco ou Cartão:", ["Todos"] + lista_contas, key="busca_bco_bx")
    data_limite_mes = date(hoje.year, hoje.month, 1) + timedelta(days=32)
    data_limite_mes = date(data_limite_mes.year, data_limite_mes.month, 1) - timedelta(days=1)
    pend = df_g[(df_g['Status'].str.contains("⏳")) & (df_g['DT'].dt.date <= data_limite_mes)].copy()
    if busca_bco != "Todos": pend = pend[pend['Pagamento'] == busca_bco]
    if not pend.empty:
        c_bx1, c_bx2, c_bx3 = st.columns([2, 1, 1])
        sel_bx = c_bx1.selectbox("Item:", pend.index, format_func=lambda x: f"{df_g.loc[x,'Data']} | {df_g.loc[x,'Pagamento']} | {df_g.loc[x,'Beneficiário']} | {formatar_br(df_g.loc[x,'Valor'])}", key="bx_s")
        dt_bx_confirm = c_bx2.date_input("Data do Pagto:", hoje, key="bx_dt_cf")
        valor_bx_confirm = c_bx3.number_input("Valor Pago:", value=float(df_g.loc[sel_bx, 'Valor']), key="bx_val_cf")
        if st.button("CONFIRMAR PAGO", key="btn_bx_ok", use_container_width=True):
            df_g.at[sel_bx, 'Status'] = "✅ Pago"; df_g.at[sel_bx, 'Data'] = dt_bx_confirm.strftime('%d/%m/%Y'); df_g.at[sel_bx, 'Valor'] = valor_bx_confirm
            salvar_dados(df_g, ARQ_D); st.rerun()
    else: st.info(f"Nenhum lançamento pendente encontrado até o fim de {hoje.strftime('%m/%Y')}.")
    st.divider(); st.subheader("🔄 Transferência entre Contas")
    ct1, ct2 = st.columns(2)
    dt_t_val = ct1.date_input("Data Transf:", hoje, key="t_dt"); vt = ct2.number_input("Valor:", 0.0, key="t_v")
    ct3, ct4 = st.columns(2)
    o = ct3.selectbox("De:", lista_contas, key="t_o"); d = ct4.selectbox("Para:", lista_contas, key="t_d")
    dsc_t = st.text_input("Descrição:", "Transferência entre contas", key="t_desc")
    if st.button("EXECUTAR TRANSFERÊNCIA", key="btn_transf", use_container_width=True):
        s = {"Data": dt_t_val.strftime('%d/%m/%Y'), "Tipo": "🔴 Despesa", "Categoria": "Transferência", "Valor": vt, "Pagamento": o, "Beneficiário": f"Para {d}", "Status": "✅ Pago", "KM": 0, "Descrição": dsc_t}
        e = {"Data": dt_t_val.strftime('%d/%m/%Y'), "Tipo": "🟢 Receita", "Categoria": "Transferência", "Valor": vt, "Pagamento": d, "Beneficiário": f"De {o}", "Status": "✅ Pago", "KM": 0, "Descrição": dsc_t}
        df_g = pd.concat([df_g, pd.DataFrame([s, e])], ignore_index=True); salvar_dados(df_g, ARQ_D); st.rerun()

with tab_e:
    cf1, cf2, cf3 = st.columns([2, 1, 1])
    f_per = cf1.date_input("Período:", [date(hoje.year, hoje.month, 1), hoje], key="f_p")
    f_bco = cf2.selectbox("Filtrar Conta:", ["Todos"] + lista_contas, key="f_b"); f_benef = cf3.text_input("Buscar Beneficiário:", key="f_be")
    if not df_g.empty and len(f_per) == 2:
        df_v = df_g[(df_g['DT'].dt.date >= f_per[0]) & (df_g['DT'].dt.date <= f_per[1])].copy()
        if f_bco != "Todos": df_v = df_v[df_v['Pagamento'] == f_bco]
        if f_benef: df_v = df_v[df_v['Beneficiário'].str.contains(f_benef, case=False, na=False)]
        rend_metrics = df_v[(df_v['Tipo'].str.contains("Rendimento")) & (df_v['Status']=="✅ Pago")]['Valor'].sum()
        v_rec_pura = df_v[(df_v['Tipo'].str.contains("Receita")) & (df_v['Status']=="✅ Pago") & (df_v['Categoria']!="Transferência")]['Valor'].sum()
        rec_metrics = v_rec_pura + rend_metrics
        des_metrics = df_v[(df_v['Tipo'].str.contains("Despesa")) & (df_v['Status']=="✅ Pago") & (df_v['Categoria']!="Transferência")]['Valor'].sum()
        pend_metrics = df_v[df_v['Status'].str.contains("⏳")]['Valor'].sum()
        saldo_atual = rec_metrics - des_metrics
        st.markdown(f"<div style='background-color:#2E86C1;color:white;padding:10px;border-radius:5px;text-align:center'><b>SALDO DO PERÍODO: {formatar_br(saldo_atual)}</b></div>", unsafe_allow_html=True)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🟢 REC (Total)", formatar_br(rec_metrics)); m2.metric("🔴 DES", formatar_br(des_metrics)); m3.metric("💎 REND", formatar_br(rend_metrics)); m4.metric("⏳ PEND", formatar_br(pend_metrics))
        st.divider(); c_e1, c_e2, c_e3 = st.columns(3)
        pdf_b = gerar_pdf_custom(df_g, df_v, f"Banco: {f_bco}" if f_bco != "Todos" else "Geral", "", f_per[0], df_b)
        c_e1.download_button("📄 PDF", pdf_b, "Relatorio.pdf", "application/pdf", use_container_width=True)
        
        txt_bancos = ""; pat_bancos = 0
        for _, r in df_b.iterrows():
            n_b = str(r['Banco']); e_b = df_g[(df_g['Pagamento']==n_b) & (df_g['Tipo'].str.contains("Receita|Rend")) & (df_g['Status']=="✅ Pago")].Valor.sum()
            s_b = df_g[(df_g['Pagamento']==n_b) & (df_g['Tipo'].str.contains("Despesa")) & (df_g['Status']=="✅ Pago")].Valor.sum()
            saldo_f = r['Limite'] + e_b - s_b; pat_bancos += saldo_f; txt_bancos += f"{n_b}: {formatar_br(saldo_f)}\n"
        txt_cartoes = ""; pat_cartoes = 0
        for _, r in df_c.iterrows():
            n_c = str(r['Cartão']); divida = df_g[(df_g['Pagamento'].str.strip() == n_c.strip()) & (df_g['Status'].str.contains("⏳"))]['Valor'].sum()
            pat_cartoes += divida; txt_cartoes += f"{n_c}: {formatar_br(divida)}\n"
        res_mail = {'inicio': f_per[0].strftime('%d/%m/%Y'), 'fim': f_per[1].strftime('%d/%m/%Y'), 'rec': rec_metrics, 'des': des_metrics, 'rend': rend_metrics, 'sobra': saldo_atual, 'patrimonio': pat_bancos - pat_cartoes, 'detalhe_bancos': txt_bancos, 'detalhe_cartoes': txt_cartoes}

        if c_e2.button("📧 E-MAIL", use_container_width=True):
            ok, msg_m = enviar_email_wilson(mail_u, mail_p, res_mail); st.info(msg_m)

        if c_e3.button("💬 WHATSAPP", use_container_width=True):
            if not whats_u: st.error("Digite o número do WhatsApp na lateral!")
            else:
                texto_whats = f"""🐾 *RELATÓRIO WILSON - DETALHADO*
Período: {res_mail['inicio']} a {res_mail['fim']}
----------------------------------------
REC: {formatar_br(res_mail['rec'])}
DES: {formatar_br(res_mail['des'])}
REND: {formatar_br(res_mail['rend'])}
*SOBRA: {formatar_br(res_mail['sobra'])}*
----------------------------------------
*SALDO NAS CONTAS:*
{res_mail['detalhe_bancos']}
*DÍVIDA EM CARTÕES:*
{res_mail['detalhe_cartoes']}
----------------------------------------
*PATRIMÔNIO LÍQUIDO: {formatar_br(res_mail['patrimonio'])}*"""
                link_w = f"https://wa.me/{whats_u}?text={urllib.parse.quote(texto_whats)}"
                st.markdown(f'<a href="{link_w}" target="_blank" style="text-decoration:none;"><button style="width:100%; background-color:#25D366; color:white; border:none; padding:10px; border-radius:5px; cursor:pointer;">ABRIR CONVERSA NO WHATSAPP</button></a>', unsafe_allow_html=True)

        st.dataframe(df_v.sort_values(by='DT', ascending=False), use_container_width=True, hide_index=True)
        st.divider(); g1, g2 = st.columns(2)
        with g1:
            st.write("### 🌡️ Termômetro de Metas (Gasto x Meta)")
            if not df_m.empty:
                gastos_cat = df_v[df_v['Tipo'].str.contains("Despesa")].groupby('Categoria')['Valor'].sum().reset_index()
                df_term = pd.merge(df_m, gastos_cat, on='Categoria', how='left').fillna(0)
                fig_m = go.Figure(); fig_m.add_trace(go.Bar(name='Gasto Real', x=df_term['Categoria'], y=df_term['Valor'], marker_color='red')); fig_m.add_trace(go.Bar(name='Meta Wilson', x=df_term['Categoria'], y=df_term['Meta'], marker_color='blue')); st.plotly_chart(fig_m, use_container_width=True)
        with g2:
            st.write("### 📈 Evolução Mensal"); df_v['Mes'] = df_v['DT'].dt.strftime('%m/%Y'); df_evol = df_v.groupby(['Mes', 'Tipo'])['Valor'].sum().reset_index(); fig_e = px.bar(df_evol, x='Mes', y='Valor', color='Tipo', barmode='group'); st.plotly_chart(fig_e, use_container_width=True)

with tab_gerenciar:
    st.subheader("🗑️ Lixeira Inteligente")
    df_ord = df_g.sort_values(by="DT", ascending=False)
    sel_lix = st.selectbox("Item p/ excluir:", df_ord.index, format_func=lambda x: f"{df_g.loc[x,'Data']} | {df_g.loc[x,'Pagamento']} | {df_g.loc[x,'Beneficiário']} | {formatar_br(df_g.loc[x,'Valor'])}", key="lix_sel")
    item = df_g.loc[sel_lix]; benef_original = str(item['Beneficiário']); modo_exclusao = "Único"
    if "(" in benef_original and "/" in benef_original and ")" in benef_original:
        st.warning("Este item faz parte de um parcelamento!"); nome_base = benef_original.split(" (")[0]; parcela_atual = int(benef_original.split("(")[1].split("/")[0])
        modo_exclusao = st.radio("Como deseja excluir?", ["Apenas esta parcela", "Todo o parcelamento", "Desta parcela em diante"], horizontal=True)
    if st.button("🗑️ EXCLUIR AGORA", use_container_width=True):
        if modo_exclusao == "Apenas esta parcela" or modo_exclusao == "Único": df_g = df_g.drop(sel_lix)
        elif modo_exclusao == "Todo o parcelamento": df_g = df_g[~df_g['Beneficiário'].str.startswith(nome_base + " (")]
        elif modo_exclusao == "Desta parcela em diante":
            def deve_excluir(b):
                if not str(b).startswith(nome_base + " ("): return False
                try: p = int(str(b).split("(")[1].split("/")[0]); return p >= parcela_atual
                except: return False
            indices_excluir = [i for i, r in df_g.iterrows() if deve_excluir(r['Beneficiário'])]
            df_g = df_g.drop(indices_excluir)
        salvar_dados(df_g, ARQ_D); st.rerun()

with tab_config:
    st.subheader("⚙️ Gestão Total"); c1, c2, c3 = st.columns(3)
    with c1:
        st.write("### 🏦 Bancos"); nb = st.text_input("Banco:", key="cfg_bn"); lb = st.number_input("Saldo Inicial:", 0.0, key="cfg_bl")
        if st.button("Add Bco", use_container_width=True):
            df_b = pd.concat([df_b, pd.DataFrame([{"Banco":nb,"Limite":lb}])]); salvar_dados(df_b, ARQ_B); st.rerun()
        exb = st.selectbox("Excluir Banco:", ["-"] + df_b['Banco'].tolist(), key="ex_b_c")
        if st.button("Excluir Bco", use_container_width=True) and exb != "-":
            df_b = df_b[df_b['Banco']!=exb]; salvar_dados(df_b, ARQ_B); st.rerun()
    with c2:
        st.write("### 💳 Cartões"); nc = st.text_input("Cartão:", key="cfg_cn"); lc = st.number_input("Limite:", 0.0, key="cfg_cl")
        fch = st.number_input("Fechamento:", 1, 31, 10, key="cfg_cf"); vnc = st.number_input("Vencimento:", 1, 31, 15, key="cfg_cv")
        if st.button("Add Card", use_container_width=True):
            df_c = pd.concat([df_c, pd.DataFrame([{"Cartão":nc,"Limite":lc,"Fechamento":fch,"Vencimento":vnc}])]); salvar_dados(df_c, ARQ_C); st.rerun()
        exc = st.selectbox("Excluir Cartão:", ["-"] + df_c['Cartão'].tolist(), key="ex_c_c")
        if st.button("Excluir Card", use_container_width=True) and exc != "-":
            df_c = df_c[df_c['Cartão']!=exc]; salvar_dados(df_c, ARQ_C); st.rerun()
    with c3:
        st.write("### 🎯 Metas"); ncat = st.selectbox("Categoria:", lista_cats, key="cfg_mc"); vmet = st.number_input("Meta R$:", 0.0, key="cfg_mv")
        if st.button("Add Meta", use_container_width=True):
            df_m = pd.concat([df_m, pd.DataFrame([{"Categoria":ncat,"Meta":vmet}])]); salvar_dados(df_m, ARQ_M); st.rerun()
        exm = st.selectbox("Excluir Meta:", ["-"] + df_m['Categoria'].tolist(), key="ex_m_c")
        if st.button("Excluir Meta", use_container_width=True) and exm != "-":
            df_m = df_m[df_m['Categoria']!=exm]; salvar_dados(df_m, ARQ_M); st.rerun()

st.divider()
dtc_pat = sum([df_g[(df_g['Pagamento'].str.strip() == str(r['Cartão']).strip()) & (df_g['Status'].str.contains("⏳"))]['Valor'].sum() for _, r in df_c.iterrows()])
cb, cc = st.columns(2)
with cb:
    st.subheader("🏦 Resumo Bancos"); rb = []; pb_pat = 0
    for _, r in df_b.iterrows():
        n = str(r['Banco']); e = df_g[(df_g['Pagamento']==n) & (df_g['Tipo'].str.contains("Receita|Rend")) & (df_g['Status']=="✅ Pago")].Valor.sum()
        s = df_g[(df_g['Pagamento']==n) & (df_g['Tipo'].str.contains("Despesa")) & (df_g['Status']=="✅ Pago")].Valor.sum()
        sf = r['Limite'] + e - s; pb_pat += sf; rb.append({"Banco": n, "Saldo": formatar_br(sf)})
    st.table(pd.DataFrame(rb)); st.metric("💰 PATRIMÔNIO LÍQUIDO", formatar_br(pb_pat - dtc_pat))
with cc:
    st.subheader("💳 Situação Cartões"); rc = []
    for _, r in df_c.iterrows():
        n = str(r['Cartão']); li = float(r.get('Limite', 0.0)); dc = df_g[(df_g['Pagamento'].str.strip() == n.strip()) & (df_g['Status'].str.contains("⏳"))]['Valor'].sum()
        rc.append({"Cartão": n, "Limite": formatar_br(li), "Utilizado": formatar_br(dc), "Livre": formatar_br(li - dc), "F/V": f"{int(r.get('Fechamento',0))}/{int(r.get('Vencimento',0))}"})
    if rc: st.table(pd.DataFrame(rc))

st.markdown("<br><hr><center><p style='color: grey; font-size: 10px;'>Desenvolvido por Wilson Barna & Gemini AI 🤖</p></center>", unsafe_allow_html=True)