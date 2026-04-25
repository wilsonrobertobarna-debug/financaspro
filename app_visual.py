# ==========================================
# ABA 3: MEU VEÍCULO (CORRIGIDA)
# ==========================================
else:
    ws = sh.worksheet("Controle_Veiculo")
    st.title("🚗 Controle do Veículo")
    
    c1, c2 = st.columns([1, 2])
    with c1:
        st.subheader("⛽ Calculadora Flex")
        alc = st.number_input("Preço Álcool", min_value=0.0, format="%.2f")
        gas = st.number_input("Preço Gasolina", min_value=0.0, format="%.2f")
        if alc > 0 and gas > 0:
            res = alc/gas
            st.write(f"Proporção: {res:.2f}")
            if res <= 0.7:
                st.success("VÁ DE ÁLCOOL! ✅")
            else:
                st.warning("VÁ DE GASOLINA! ⛽")

    with c2:
        st.subheader("📝 Novo Registro")
        with st.sidebar.form("f_vei", clear_on_submit=True):
            v_dat = st.date_input("Data", datetime.now(), format="DD/MM/YYYY")
            v_tip = st.selectbox("Serviço", ["Abastecimento", "Troca de Óleo", "Manutenção", "Lavagem", "Outros"])
            v_km = st.number_input("KM Atual", min_value=0)
            v_val = st.number_input("Valor Total (R$)", min_value=0.0)
            
            if st.form_submit_button("🚗 SALVAR NO VEÍCULO"):
                dt_s = v_dat.strftime("%d/%m/%Y")
                # ORDEM CORRETA: Data, Serviço (Tipo), KM, Valor
                ws.append_row([dt_s, v_tip, str(v_km), str(v_val)])
                
                # LANÇA TAMBÉM NO FINANCEIRO GERAL
                sh.get_worksheet(0).append_row([dt_s, str(v_val), "Combustível" if v_tip == "Abastecimento" else "Veículo", "Despesa", "Nubank", "Pago"])
                
                st.cache_data.clear()
                st.rerun()
            
    exibir_tabela_segura(ws, "Histórico do Veículo")
