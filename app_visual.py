# --- CÁLCULO DE VALORES ---
    df_per = df_base[(df_base['DT'].dt.date >= d_ini) & (df_base['DT'].dt.date <= d_fim)].copy()
    
    if not df_per.empty:
        df_per['T_UP'] = df_per['Tipo'].astype(str).str.upper().str.strip()
        
        # 1. A CONTA (Receita - Despesa)
        # Aqui pegamos tudo que é Receita (inclusive o que for rendimento)
        r_v = df_per[(df_per['T_UP'] == 'RECEITA') & (df_per['Status'] == 'Pago')]['V_Num'].sum()
        d_v = df_per[(df_per['T_UP'] == 'DESPESA') & (df_per['Status'] == 'Pago')]['V_Num'].sum()
        
        # 2. A INFORMAÇÃO (Apenas para mostrar no relatório)
        # Vamos buscar pela CATEGORIA 'Rendimento' ou pelo TIPO 'Rendimento'
        # Isso não entra na conta da sobra, apenas aparece no texto
        rend_v = df_per[(df_per['Tipo'].str.contains('Rendimento', case=False, na=False)) | 
                        (df_per['Categoria'].str.contains('Rendimento', case=False, na=False))]['V_Num'].sum()
        
        # 3. SALDO FINAL
        sobra = r_v - d_v
    else:
        r_v = d_v = rend_v = sobra = 0.0

    # --- RELATÓRIO ---
    relat = f"RELATÓRIO WILSON\nPeríodo: {d_ini.strftime('%d/%m/%Y')} a {d_fim.strftime('%d/%m/%Y')}\n"
    relat += f"========================================\n"
    relat += f"REC: {m_fmt(r_v)} | REND: {m_fmt(rend_v)} (Info)\n"
    relat += f"DES: {m_fmt(d_v)} | SOBRA: {m_fmt(sobra)}\n"
    relat += f"========================================\n"
