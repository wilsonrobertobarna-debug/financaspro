# --- ABA 5: RELATÓRIOS (Adicione este bloco para os cartões) ---
with tab_relat:
    st.header("💳 Gastos por Cartão de Crédito")
    
    if dados_g:
        df = pd.DataFrame(dados_g)
        df.columns = [c.strip() for c in df.columns]
        
        # 1. Tratamento de Dados
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        df['Valor'] = pd.to_numeric(df['Valor'], errors='coerce').fillna(0)
        
        # 2. Filtro: Apenas o mês atual e apenas pagamentos via "Crédito"
        mes_atual = datetime.now().month
        ano_atual = datetime.now().year
        
        # Ajuste 'Pagamento' ou 'Forma' conforme sua planilha
        col_pag = 'Pagamento' if 'Pagamento' in df.columns else 'Forma'
        col_banco = 'Banco' # Onde você seleciona o nome do cartão/banco
        
        df_cartoes = df[
            (df['Data'].dt.month == mes_atual) & 
            (df['Data'].dt.year == ano_atual) & 
            (df[col_pag] == 'Crédito')
        ]
        
        if not df_cartoes.empty:
            # 3. Agrupamento por Cartão (Coluna 'Banco')
            resumo_cartoes = df_cartoes.groupby(col_banco)['Valor'].sum().reset_index()
            
            c1, c2 = st.columns([2, 1])
            with c1:
                # Gráfico de Barras Comparativo
                fig_cartao = px.bar(
                    resumo_cartoes, 
                    x=col_banco, 
                    y='Valor', 
                    title=f"Total na Fatura - {datetime.now().strftime('%m/%Y')}",
                    labels={col_banco: "Cartão", "Valor": "Total (R$)"},
                    color=col_banco
                )
                st.plotly_chart(fig_cartao, use_container_width=True)
            
            with c2:
                # Tabela de Conferência
                st.write("📋 Resumo da Fatura")
                st.dataframe(resumo_cartoes, hide_index=True, use_container_width=True)
                
                total_mes = resumo_cartoes['Valor'].sum()
                st.metric("Total Geral em Cartões", f"R$ {total_mes:,.2f}")
        else:
            st.warning("Nenhum gasto no Crédito encontrado para o mês atual.")
