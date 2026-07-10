elif "Pendências" in aba:
    st.title("📋 Lançamentos Pendentes")
    
    # 1. Filtros Unificados
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        filtro_banco = st.multiselect("Filtrar Banco:", df_base['Banco'].unique())
    with col_b:
        busca_geral = st.text_input("🔍 Pesquisar (Desc/Beneficiário)")
    with col_c:
        periodo = st.date_input("Período:", (datetime.now().replace(day=1), datetime.now() + timedelta(days=30)))

    # 2. Processamento (Um único fluxo)
    df_filtrado = df_base[df_base['Status'].astype(str).str.strip().str.lower() == 'pendente'].copy()
    
    # Aplica Banco
    if filtro_banco:
        df_filtrado = df_filtrado[df_filtrado['Banco'].isin(filtro_banco)]
    
    # Aplica Busca (Descrição OU Beneficiário) - Agora garantido pelo nome da coluna
    if busca_geral:
        mask = (df_filtrado['Descrição'].astype(str).str.contains(busca_geral, case=False, na=False)) | \
               (df_filtrado['Beneficiário'].astype(str).str.contains(busca_geral, case=False, na=False))
        df_filtrado = df_filtrado[mask]
        
    # Aplica Data
    df_filtrado['Data_Obj'] = pd.to_datetime(df_filtrado['Vencimento'], dayfirst=True, errors='coerce')
    if isinstance(periodo, tuple) and len(periodo) == 2:
        df_filtrado = df_filtrado[(df_filtrado['Data_Obj'].dt.date >= periodo[0]) & 
                                  (df_filtrado['Data_Obj'].dt.date <= periodo[1])]

    # 3. Exibição
    st.write(f"### Lançamentos Encontrados: {len(df_filtrado)}")
    colunas_exibir = ['Vencimento', 'Banco', 'Descrição', 'Beneficiário', 'Valor', 'Categoria']
    st.dataframe(df_filtrado[colunas_exibir].iloc[::-1], use_container_width=True, hide_index=True)

    # 4. Botão de Baixa
    if not df_filtrado.empty:
        if st.button("✅ BAIXAR SELECIONADOS"):
            # Lógica de atualização (mantive sua estrutura original)
            headers = ws_base.row_values(1)
            idx_status = headers.index('Status') + 1
            for idx_df, row in df_filtrado.iterrows():
                ws_base.update_cell(int(idx_df) + 2, idx_status, "Pago")
            st.toast("✅ Itens baixados!", icon="💰")
            st.rerun()
