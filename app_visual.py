else:
        sel_f = st.sidebar.selectbox("ID Linha:", list(df_visual.index))
        if sel_f:
            row_f = df.loc[sel_f-2]
            with st.sidebar.form("e_fin"):
                st.write(f"Editando Registro #{sel_f}")
                e_dat = st.text_input("Data", value=str(row_f['Data']))
                e_val = st.text_input("Valor", value=str(row_f['Valor']))
                # Adicionei Banco e Categoria na edição:
                e_bnc = st.selectbox("Novo Banco", ["Nubank", "Itaú", "Dinheiro", "Outro"], 
                                   index=["Nubank", "Itaú", "Dinheiro", "Outro"].index(row_f[c_bnc]) if row_f[c_bnc] in ["Nubank", "Itaú", "Dinheiro", "Outro"] else 0)
                e_cat = st.text_input("Categoria", value=str(row_f[c_cat]))
                e_stat = st.selectbox("Status", ["Pago", "Pendente"], index=0 if "Pag" in str(row_f[c_stat]) else 1)
                
                c1, c2 = st.columns(2)
                if c1.form_submit_button("💾 ATUALIZAR TUDO"):
                    # Agora ele envia a linha completa com o banco novo
                    ws.update(f"A{sel_f}:F{sel_f}", [[e_dat, e_val, e_cat, row_f[c_tipo], e_bnc, e_stat]])
                    st.cache_data.clear()
                    st.rerun()
                if c2.form_submit_button("🗑️ EXCLUIR"):
                    ws.delete_rows(int(sel_f))
                    st.cache_data.clear()
                    st.rerun()
