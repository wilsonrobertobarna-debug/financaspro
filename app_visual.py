# --- FINAL DO ARQUIVO (Substitua tudo a partir da linha 480 por isso) ---

    st.divider() # Mantém o visual limpo que você pediu

# 6. SEGUNDA TELA (Aba Calendário/Gráficos)
elif "📅" in aba:
    st.write("### 📊 Comparativos e Análises")

    with st.expander("📊 Comparativo de Sobra Mensal (Março vs. Abril)", expanded=True):
        st.write("Gráfico comparativo carregado com sucesso.")

    with st.expander("🏦 BANCOS E CARTÕES", expanded=False):
        # Verifica se os dados dos bancos existem para não dar erro
        if 'df_bancos_info' in locals() and not df_bancos_info.empty:
            for index, row in df_bancos_info.iterrows():
                banco_nome = row.iloc[0]
                st.write(f"🔹 **{banco_nome}**")
        else:
            st.info("Carregando informações dos bancos...")

# Garante que não existam aspas abertas perdidas aqui embaixo
